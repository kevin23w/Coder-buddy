import Head from "next/head";
import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { LogOut, Zap, History, Key, CreditCard } from "lucide-react";
import { supabase, API_URL } from "@/lib/supabase";
import UsageBar from "@/components/UsageBar";

interface Profile {
  email:    string;
  full_name: string;
  plan:     string;
  plan_display: string;
  subscription_status: string;
  usage: {
    used:    number;
    limit:   number | "unlimited";
    plan:    string;
    history: { date: string; success: boolean; tokens: number }[];
  };
}

export default function Dashboard() {
  const router               = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError  ] = useState("");

  useEffect(() => {
    const load = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) { router.replace("/"); return; }

      const token = session.access_token;
      try {
        const res  = await fetch(`${API_URL}/me`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok) throw new Error(await res.text());
        setProfile(await res.json());
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/");
  };

  const handleUpgrade = async (plan: string) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;
    const res  = await fetch(`${API_URL}/billing/subscribe?plan_name=${plan}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session.access_token}` },
    });
    const data = await res.json();
    if (data.short_url) window.open(data.short_url, "_blank");
    else alert(data.detail || "Error creating subscription. Check Razorpay config.");
  };

  const handleCancel = async () => {
    if (!confirm("Cancel your subscription? You'll keep access until the billing period ends.")) return;
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return;
    const res  = await fetch(`${API_URL}/billing/cancel`, {
      method: "POST",
      headers: { Authorization: `Bearer ${session.access_token}` },
    });
    const data = await res.json();
    alert(data.message || "Cancellation requested.");
  };

  if (loading) return (
    <div className="min-h-screen bg-bg0 flex items-center justify-center">
      <div className="text-muted animate-pulse text-lg">Loading your dashboard…</div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-bg0 flex items-center justify-center px-6">
      <div className="text-center">
        <p className="text-red mb-4">{error}</p>
        <button onClick={() => router.push("/")} className="btn-primary">Go Home</button>
      </div>
    </div>
  );

  if (!profile) return null;

  const planColor = profile.plan === "team" ? "text-yellow" : profile.plan === "pro" ? "text-purple" : "text-muted";

  return (
    <>
      <Head>
        <title>Dashboard — Coder Buddy</title>
      </Head>

      <div className="min-h-screen bg-bg0">
        {/* Navbar */}
        <nav className="border-b border-border bg-bg1/80 backdrop-blur-md sticky top-0 z-40">
          <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link href="/" className="font-bold text-white">🤖 Coder Buddy</Link>
            <div className="flex items-center gap-4">
              <span className={`text-xs font-bold uppercase px-2.5 py-1 rounded-full border ${
                profile.plan === "team"  ? "bg-yellow/10 border-yellow/30 text-yellow" :
                profile.plan === "pro"   ? "bg-purple/10 border-purple/30 text-purple" :
                                           "bg-border text-muted border-border"
              }`}>{profile.plan_display}</span>
              <button onClick={handleLogout} className="text-muted hover:text-white transition-colors flex items-center gap-1.5 text-sm">
                <LogOut size={15} /> Sign out
              </button>
            </div>
          </div>
        </nav>

        <div className="max-w-5xl mx-auto px-6 py-10">
          {/* Welcome */}
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-white">
              Welcome back{profile.full_name ? `, ${profile.full_name.split(" ")[0]}` : ""}! 👋
            </h1>
            <p className="text-muted mt-1 text-sm">{profile.email}</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Left column */}
            <div className="lg:col-span-2 space-y-6">

              {/* Usage */}
              <UsageBar
                used={profile.usage.used}
                limit={profile.usage.limit}
                plan={profile.plan}
              />

              {/* Upgrade banner (free only) */}
              {profile.plan === "free" && (
                <div className="bg-gradient-to-r from-blue/10 to-purple/10 border border-blue/20 rounded-xl p-6">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div>
                      <h3 className="font-semibold text-white mb-1 flex items-center gap-2">
                        <Zap size={16} className="text-yellow" /> Upgrade to Pro
                      </h3>
                      <p className="text-muted text-sm">50 runs/month, email reports, commit generation & GitHub PRs.</p>
                    </div>
                    <button onClick={() => handleUpgrade("pro")} className="btn-primary text-sm px-5 py-2.5 shrink-0">
                      ₹499/month →
                    </button>
                  </div>
                </div>
              )}

              {/* Run history */}
              <div className="bg-bg2 border border-border rounded-xl overflow-hidden">
                <div className="flex items-center gap-2 px-5 py-4 border-b border-border">
                  <History size={16} className="text-muted" />
                  <h2 className="font-semibold text-white text-sm">Run History (this month)</h2>
                </div>
                {profile.usage.history.length === 0 ? (
                  <div className="px-5 py-10 text-center text-muted text-sm">
                    No runs yet this month. <Link href="/" className="text-blue hover:underline">Start analyzing →</Link>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left px-5 py-3 text-muted font-medium text-xs uppercase">Date</th>
                          <th className="text-left px-5 py-3 text-muted font-medium text-xs uppercase">Result</th>
                          <th className="text-left px-5 py-3 text-muted font-medium text-xs uppercase">Tokens</th>
                        </tr>
                      </thead>
                      <tbody>
                        {profile.usage.history.map((run, i) => (
                          <tr key={i} className="border-b border-border/50 last:border-0 hover:bg-bg1/50 transition-colors">
                            <td className="px-5 py-3 text-muted text-xs font-mono">
                              {new Date(run.date).toLocaleDateString("en-IN", { day:"numeric", month:"short", hour:"2-digit", minute:"2-digit" })}
                            </td>
                            <td className="px-5 py-3">
                              <span className={`text-xs font-bold ${run.success ? "text-green" : "text-red"}`}>
                                {run.success ? "✅ Passed" : "❌ Failed"}
                              </span>
                            </td>
                            <td className="px-5 py-3 text-muted text-xs">{run.tokens.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>

            {/* Right column */}
            <div className="space-y-4">

              {/* Account card */}
              <div className="bg-bg2 border border-border rounded-xl p-5">
                <h3 className="font-semibold text-white text-sm mb-4 flex items-center gap-2">
                  <CreditCard size={15} className="text-muted" /> Subscription
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted">Plan</span>
                    <span className={`font-semibold ${planColor}`}>{profile.plan_display}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Status</span>
                    <span className="text-white capitalize">{profile.subscription_status}</span>
                  </div>
                </div>

                {profile.plan === "free" ? (
                  <div className="mt-4 space-y-2">
                    <button onClick={() => handleUpgrade("pro")}  className="w-full btn-primary text-sm py-2">Upgrade to Pro ₹499/mo</button>
                    <button onClick={() => handleUpgrade("team")} className="w-full border border-border text-white text-sm py-2 rounded-lg hover:border-yellow/50 transition-colors">Team Plan ₹1499/mo</button>
                  </div>
                ) : profile.subscription_status !== "cancelling" ? (
                  <button onClick={handleCancel} className="mt-4 w-full text-xs text-muted hover:text-red transition-colors">
                    Cancel subscription
                  </button>
                ) : (
                  <p className="mt-4 text-xs text-yellow text-center">Cancels at end of billing period</p>
                )}
              </div>

              {/* API Key card (Team only) */}
              {profile.plan === "team" && (
                <div className="bg-bg2 border border-border rounded-xl p-5">
                  <h3 className="font-semibold text-white text-sm mb-3 flex items-center gap-2">
                    <Key size={15} className="text-muted" /> API Access
                  </h3>
                  <p className="text-muted text-xs mb-4">Use your API key to call Coder Buddy from CI/CD pipelines.</p>
                  <button
                    onClick={async () => {
                      const { data: { session } } = await supabase.auth.getSession();
                      if (!session) return;
                      const res  = await fetch(`${API_URL}/api-keys?label=Dashboard`, {
                        method: "POST",
                        headers: { Authorization: `Bearer ${session.access_token}` },
                      });
                      const data = await res.json();
                      if (data.api_key) {
                        prompt("Your new API key (save it — shown once):", data.api_key);
                      }
                    }}
                    className="w-full border border-border text-white text-sm py-2 rounded-lg hover:border-blue/50 transition-colors"
                  >
                    Generate API Key
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
