import Head from "next/head";
import Link from "next/link";
import { useState } from "react";
import { Bot, Zap, GitPullRequest, TestTube, ArrowRight, Star, Check } from "lucide-react";
import AuthModal from "@/components/AuthModal";

const STEPS = [
  { icon: "📁", title: "Paste your repo path",  desc: "Point Coder Buddy at any local Python project."         },
  { icon: "✏️", title: "Describe the problem",  desc: "Plain English — 'Fix all bugs in the auth module'."    },
  { icon: "🚀", title: "Agent does the work",   desc: "Plans, fixes, tests, and proposes a git commit for you."},
];

const FEATURES = [
  { icon: <Bot    size={22} className="text-blue"  />, title: "Smart Planner",   desc: "LLaMA 3.3 70B reads your codebase and creates a step-by-step fix plan." },
  { icon: <Zap    size={22} className="text-yellow"/>, title: "Instant Fixes",   desc: "Applies corrected code directly to disk — no copy-paste needed."        },
  { icon: <TestTube size={22} className="text-green"/>,title: "Auto Retry",      desc: "Runs pytest, learns from failures, and retries up to 3 times."          },
  { icon: <GitPullRequest size={22} className="text-purple"/>, title: "PR Ready",desc: "Generates a Conventional Commit message and full PR description."       },
];

export default function Home() {
  const [authOpen, setAuthOpen] = useState(false);

  return (
    <>
      <Head>
        <title>Coder Buddy — AI Software Engineer That Fixes Your Bugs</title>
        <meta name="description" content="Autonomous AI agent that reads your Python repo, fixes bugs, runs tests, and proposes a git commit. Free to start — no credit card needed." />
        <meta property="og:title"       content="Coder Buddy — AI Software Engineer" />
        <meta property="og:description" content="Fix bugs automatically with LangGraph + Groq. Free tier available." />
        <meta name="viewport"           content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-bg0">
        {/* ── Navbar ──────────────────────────────────────────────── */}
        <nav className="border-b border-border bg-bg1/80 backdrop-blur-md sticky top-0 z-40">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
            <span className="font-bold text-lg text-white flex items-center gap-2">
              🤖 <span className="bg-gradient-to-r from-blue to-purple bg-clip-text text-transparent">Coder Buddy</span>
            </span>
            <div className="flex items-center gap-4">
              <Link href="/pricing" className="text-muted hover:text-white text-sm transition-colors">Pricing</Link>
              <button
                onClick={() => setAuthOpen(true)}
                className="btn-primary text-sm px-4 py-2"
              >
                Start Free
              </button>
            </div>
          </div>
        </nav>

        {/* ── Hero ────────────────────────────────────────────────── */}
        <section className="relative overflow-hidden">
          {/* Background glow */}
          <div className="absolute inset-0 bg-hero-gradient pointer-events-none" />
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue/5 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute top-10 right-1/4 w-80 h-80 bg-purple/5 rounded-full blur-3xl pointer-events-none" />

          <div className="relative max-w-5xl mx-auto px-6 pt-28 pb-24 text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-blue/10 border border-blue/20 text-blue text-xs font-semibold px-4 py-1.5 rounded-full mb-6">
              <Zap size={12} /> Powered by LLaMA 3.3 70B × Groq × LangGraph
            </div>

            {/* Headline */}
            <h1 className="text-5xl md:text-6xl font-extrabold text-white mb-6 leading-tight">
              Your AI{" "}
              <span className="bg-gradient-to-r from-blue to-purple bg-clip-text text-transparent">
                Software Engineer
              </span>
            </h1>
            <p className="text-xl text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
              Fix bugs, run tests, and generate PRs automatically.
              Describe the problem in plain English — Coder Buddy handles the rest.
            </p>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => setAuthOpen(true)}
                className="btn-primary flex items-center justify-center gap-2 text-base px-8 py-4"
              >
                Start Free — No Credit Card <ArrowRight size={18} />
              </button>
              <Link
                href="/pricing"
                className="border border-border text-white px-8 py-4 rounded-lg font-semibold text-base hover:border-blue/50 transition-all"
              >
                View Pricing
              </Link>
            </div>

            {/* Social proof */}
            <div className="mt-10 flex items-center justify-center gap-6 text-muted text-sm flex-wrap">
              <span className="flex items-center gap-1.5"><Check size={14} className="text-green"/>Free plan — 3 runs/month</span>
              <span className="flex items-center gap-1.5"><Check size={14} className="text-green"/>No setup, no infra</span>
              <span className="flex items-center gap-1.5"><Check size={14} className="text-green"/>Pro from ₹499/month</span>
            </div>
          </div>
        </section>

        {/* ── How it works ─────────────────────────────────────────── */}
        <section className="max-w-5xl mx-auto px-6 py-24">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-white mb-3">How it works</h2>
            <p className="text-muted">Three steps. Under 60 seconds.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STEPS.map((s, i) => (
              <div key={i} className="card text-center relative">
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 bg-blue/20 border border-blue/30 rounded-full flex items-center justify-center text-blue font-bold text-sm">
                  {i + 1}
                </div>
                <div className="text-4xl mt-4 mb-4">{s.icon}</div>
                <h3 className="font-semibold text-white mb-2">{s.title}</h3>
                <p className="text-muted text-sm leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Demo terminal ────────────────────────────────────────── */}
        <section className="max-w-4xl mx-auto px-6 pb-20">
          <div className="bg-bg1 border border-border rounded-2xl overflow-hidden shadow-2xl">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-bg2">
              <div className="w-3 h-3 rounded-full bg-red/70" />
              <div className="w-3 h-3 rounded-full bg-yellow/70" />
              <div className="w-3 h-3 rounded-full bg-green/70" />
              <span className="text-muted text-xs ml-2 font-mono">coder-buddy — agent run</span>
            </div>
            <div className="p-6 font-mono text-sm space-y-2">
              <p><span className="text-muted">$</span> <span className="text-blue">coder-buddy analyze</span> <span className="text-white">--repo ./my-project --fix "Fix division bug"</span></p>
              <p className="text-muted">→ Planner: Generating 4-step action plan…</p>
              <p className="text-green">✓ Step 1: Read calculator.py (142 lines)</p>
              <p className="text-green">✓ Step 2: Identified bug — line 31 uses * instead of /</p>
              <p className="text-green">✓ Step 3: Applied fix + wrote corrected file</p>
              <p className="text-green">✓ Step 4: pytest — 12 passed in 0.8s ✅</p>
              <p className="text-purple mt-2">→ Commit: fix(calculator): resolve division operator bug</p>
              <p className="text-muted text-xs mt-3">⚡ Completed in 28 seconds via Groq</p>
            </div>
          </div>
        </section>

        {/* ── Features ─────────────────────────────────────────────── */}
        <section className="max-w-5xl mx-auto px-6 py-16">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-white mb-3">Everything you need</h2>
            <p className="text-muted">Built for Python developers who ship fast.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {FEATURES.map((f, i) => (
              <div key={i} className="card flex gap-4 hover:border-blue/30 transition-colors">
                <div className="mt-0.5 shrink-0">{f.icon}</div>
                <div>
                  <h3 className="font-semibold text-white mb-1">{f.title}</h3>
                  <p className="text-muted text-sm leading-relaxed">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Testimonials ─────────────────────────────────────────── */}
        <section className="max-w-4xl mx-auto px-6 py-16">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              { quote: "Coder Buddy fixed a bug in 30 seconds that I spent 2 hours on. Insane.", name: "Arjun M.", role: "Backend Developer, Chennai" },
              { quote: "The auto-retry feature is brilliant — it learns from pytest failures and fixes itself.", name: "Priya K.", role: "ML Engineer, Bangalore" },
            ].map((t, i) => (
              <div key={i} className="card">
                <div className="flex gap-1 mb-3">
                  {[...Array(5)].map((_, j) => <Star key={j} size={14} className="text-yellow fill-yellow" />)}
                </div>
                <p className="text-gray-300 text-sm leading-relaxed mb-4">"{t.quote}"</p>
                <div>
                  <p className="text-white font-semibold text-sm">{t.name}</p>
                  <p className="text-muted text-xs">{t.role}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── CTA Banner ───────────────────────────────────────────── */}
        <section className="max-w-5xl mx-auto px-6 py-16">
          <div className="bg-gradient-to-r from-blue/10 to-purple/10 border border-blue/20 rounded-2xl p-12 text-center">
            <h2 className="text-3xl font-bold text-white mb-3">Start fixing bugs with AI today</h2>
            <p className="text-muted mb-8">Free plan includes 3 runs/month. No credit card required.</p>
            <button onClick={() => setAuthOpen(true)} className="btn-primary text-base px-10 py-4 flex items-center gap-2 mx-auto">
              Get Started Free <ArrowRight size={18} />
            </button>
          </div>
        </section>

        {/* ── Footer ───────────────────────────────────────────────── */}
        <footer className="border-t border-border py-8">
          <div className="max-w-5xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-muted">
            <span>🤖 Coder Buddy — Autonomous AI Software Engineer</span>
            <div className="flex gap-6">
              <Link href="/pricing"   className="hover:text-white transition-colors">Pricing</Link>
              <Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
              <a href="https://github.com/kevin23w/Coder-buddy" target="_blank" className="hover:text-white transition-colors">GitHub</a>
            </div>
          </div>
        </footer>
      </div>

      <AuthModal isOpen={authOpen} onClose={() => setAuthOpen(false)} />
    </>
  );
}
