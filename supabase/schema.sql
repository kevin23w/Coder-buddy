-- =============================================================
-- Coder Buddy SaaS — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- =============================================================

-- ── profiles ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS profiles (
  id                       UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  email                    TEXT NOT NULL,
  full_name                TEXT,
  plan                     TEXT DEFAULT 'free' CHECK (plan IN ('free','pro','team')),
  razorpay_customer_id     TEXT,
  razorpay_subscription_id TEXT,
  subscription_status      TEXT DEFAULT 'inactive'
                              CHECK (subscription_status IN ('inactive','active','cancelling','past_due')),
  subscription_ends_at     TIMESTAMPTZ,
  created_at               TIMESTAMPTZ DEFAULT NOW(),
  updated_at               TIMESTAMPTZ DEFAULT NOW()
);

-- ── usage_logs ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usage_logs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  repo_path    TEXT,
  instructions TEXT,
  run_result   JSONB,
  tokens_used  INT DEFAULT 0,
  success      BOOLEAN DEFAULT FALSE,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast monthly queries
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_month
  ON usage_logs (user_id, created_at DESC);

-- ── api_keys ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS api_keys (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
  key_hash     TEXT NOT NULL UNIQUE,  -- SHA-256 hash of the raw key
  label        TEXT DEFAULT 'Default Key',
  is_active    BOOLEAN DEFAULT TRUE,
  last_used_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── Row Level Security ────────────────────────────────────────
ALTER TABLE profiles   ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys   ENABLE ROW LEVEL SECURITY;

-- profiles policies
CREATE POLICY "Users own their profile"
  ON profiles FOR ALL
  USING (auth.uid() = id);

-- usage_logs policies
CREATE POLICY "Users see own usage"
  ON usage_logs FOR ALL
  USING (auth.uid() = user_id);

-- api_keys policies
CREATE POLICY "Users manage own keys"
  ON api_keys FOR ALL
  USING (auth.uid() = user_id);

-- ── Auto-create profile on signup ─────────────────────────────
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email,'@',1))
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

-- Drop trigger if exists, then recreate
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- ── Auto-update updated_at ────────────────────────────────────
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_profiles_updated_at ON profiles;
CREATE TRIGGER set_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at();

-- ── Helpful views ─────────────────────────────────────────────

-- Monthly usage summary per user
CREATE OR REPLACE VIEW usage_this_month AS
SELECT
  user_id,
  COUNT(*) AS runs_used,
  SUM(tokens_used) AS total_tokens,
  COUNT(*) FILTER (WHERE success = TRUE) AS successful_runs
FROM usage_logs
WHERE created_at >= date_trunc('month', NOW())
GROUP BY user_id;
