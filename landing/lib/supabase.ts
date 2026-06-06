import { createClient } from "@supabase/supabase-js";

const supabaseUrl  = process.env.NEXT_PUBLIC_SUPABASE_URL  || "";
const supabaseAnon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

// createClient requires non-empty strings — use dummy values at build time
export const supabase = supabaseUrl
  ? createClient(supabaseUrl, supabaseAnon)
  : createClient("https://placeholder.supabase.co", "placeholder");

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

