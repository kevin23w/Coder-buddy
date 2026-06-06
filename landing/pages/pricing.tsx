import Head from "next/head";
import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, HelpCircle } from "lucide-react";
import PricingCard from "@/components/PricingCard";
import AuthModal from "@/components/AuthModal";

const FAQ = [
  { q: "What counts as one 'run'?",           a: "One run = one call to POST /analyze. Analyzing a single repo with one set of instructions = 1 run, regardless of how many files or retries happen internally." },
  { q: "Can I get a refund?",                  a: "Yes — if you're unsatisfied within 7 days of your first payment, email us for a full refund. No questions asked." },
  { q: "Is my code stored anywhere?",          a: "No. We only store metadata (run count, token count, success/fail). Your actual source code never leaves your machine." },
  { q: "What if I need more than 50 runs?",   a: "The Team plan offers unlimited runs. Or contact us for a custom enterprise plan." },
  { q: "Does it work with non-Python repos?",  a: "Currently Python only. JavaScript/TypeScript support is on the roadmap." },
];

export default function Pricing() {
  const [isAnnual, setIsAnnual] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [openFaq,  setOpenFaq]  = useState<number | null>(null);

  const handlePro  = () => setAuthOpen(true);
  const handleTeam = () => setAuthOpen(true);
  const handleFree = () => setAuthOpen(true);

  return (
    <>
      <Head>
        <title>Pricing — Coder Buddy</title>
        <meta name="description" content="Simple, transparent pricing. Free plan available. Pro at ₹499/month. Team at ₹1,499/month." />
      </Head>

      <div className="min-h-screen bg-bg0">
        {/* Navbar */}
        <nav className="border-b border-border bg-bg1/80 backdrop-blur-md sticky top-0 z-40">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 text-muted hover:text-white transition-colors text-sm">
              <ArrowLeft size={16} /> Back
            </Link>
            <span className="font-bold text-lg text-white">🤖 Coder Buddy</span>
            <button onClick={() => setAuthOpen(true)} className="btn-primary text-sm px-4 py-2">
              Start Free
            </button>
          </div>
        </nav>

        <div className="max-w-6xl mx-auto px-6 py-20">
          {/* Header */}
          <div className="text-center mb-14">
            <h1 className="text-4xl font-extrabold text-white mb-3">Simple, transparent pricing</h1>
            <p className="text-muted text-lg mb-8">Start free. Upgrade when you need more runs.</p>

            {/* Annual toggle */}
            <div className="inline-flex items-center gap-3 bg-bg2 border border-border rounded-full px-2 py-1.5">
              <button
                onClick={() => setIsAnnual(false)}
                className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-all ${!isAnnual ? "bg-blue/20 text-blue" : "text-muted hover:text-white"}`}
              >Monthly</button>
              <button
                onClick={() => setIsAnnual(true)}
                className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-all ${isAnnual ? "bg-blue/20 text-blue" : "text-muted hover:text-white"}`}
              >
                Annual
                <span className="ml-2 text-xs text-green font-bold">−20%</span>
              </button>
            </div>
          </div>

          {/* Pricing cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center mb-24">
            <PricingCard
              name="Free" price={0} annualPrice={0} isAnnual={isAnnual}
              color="gray" cta="Start Free" ctaStyle="outline" onCta={handleFree}
              features={[
                { label: "3 runs per month",          included: true  },
                { label: "Bug detection",              included: true  },
                { label: "pytest integration",         included: true  },
                { label: "Email reports",              included: false },
                { label: "Commit + PR generation",     included: false },
                { label: "GitHub PR creation",         included: false },
                { label: "Batch repo analysis",        included: false },
              ]}
            />
            <PricingCard
              name="Pro" price={499} annualPrice={399 * 12} isAnnual={isAnnual}
              color="purple" badge="⚡ Most Popular" cta="Upgrade to Pro" onCta={handlePro}
              features={[
                { label: "50 runs per month",          included: true  },
                { label: "Bug detection",              included: true  },
                { label: "pytest integration",         included: true  },
                { label: "Email reports",              included: true  },
                { label: "Commit + PR generation",     included: true  },
                { label: "GitHub PR creation",         included: true  },
                { label: "Batch repo analysis",        included: true  },
              ]}
            />
            <PricingCard
              name="Team" price={1499} annualPrice={1199 * 12} isAnnual={isAnnual}
              color="yellow" badge="🏢 For Teams" cta="Start Team Plan" onCta={handleTeam}
              features={[
                { label: "Unlimited runs",             included: true  },
                { label: "5 team members",             included: true  },
                { label: "API access + API keys",      included: true  },
                { label: "Slack / Discord webhooks",   included: true  },
                { label: "Email reports",              included: true  },
                { label: "Commit + PR generation",     included: true  },
                { label: "GitHub PR creation",         included: true  },
              ]}
            />
          </div>

          {/* FAQ */}
          <div className="max-w-2xl mx-auto">
            <h2 className="text-2xl font-bold text-white text-center mb-8">Frequently asked questions</h2>
            <div className="space-y-3">
              {FAQ.map((item, i) => (
                <div key={i} className="bg-bg2 border border-border rounded-xl overflow-hidden">
                  <button
                    onClick={() => setOpenFaq(openFaq === i ? null : i)}
                    className="w-full flex items-center justify-between px-5 py-4 text-left"
                  >
                    <span className="font-semibold text-white text-sm">{item.q}</span>
                    <HelpCircle size={16} className={`text-muted transition-transform ${openFaq === i ? "rotate-180 text-blue" : ""}`} />
                  </button>
                  {openFaq === i && (
                    <div className="px-5 pb-4 text-muted text-sm leading-relaxed border-t border-border pt-3">
                      {item.a}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <AuthModal isOpen={authOpen} onClose={() => setAuthOpen(false)} />
    </>
  );
}
