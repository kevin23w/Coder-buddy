import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { supabase } from "@/lib/supabase";
import { X, AlertTriangle } from "lucide-react";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const isSupabaseConfigured =
  typeof process.env.NEXT_PUBLIC_SUPABASE_URL === "string" &&
  process.env.NEXT_PUBLIC_SUPABASE_URL.length > 10 &&
  !process.env.NEXT_PUBLIC_SUPABASE_URL.includes("placeholder");

export default function AuthModal({ isOpen, onClose }: AuthModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md rounded-2xl p-8 shadow-2xl"
        style={{ background: "#161b22", border: "1px solid #30363d" }}>
        {/* Close */}
        <button
          onClick={onClose}
          style={{ position: "absolute", top: 16, right: 16, color: "#7d8590", background: "none", border: "none", cursor: "pointer" }}
        >
          <X size={20} />
        </button>

        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: "#fff", marginBottom: 4 }}>
            🤖 Coder Buddy
          </h2>
          <p style={{ color: "#7d8590", fontSize: 13, margin: 0 }}>
            Sign in for free — 3 runs/month, no credit card needed.
          </p>
        </div>

        {!isSupabaseConfigured ? (
          <div style={{
            background: "rgba(248,81,73,0.08)",
            border: "1px solid rgba(248,81,73,0.3)",
            borderRadius: 10, padding: 16,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <AlertTriangle size={16} color="#f85149" />
              <span style={{ color: "#f85149", fontWeight: 600, fontSize: 14 }}>
                Supabase Not Configured
              </span>
            </div>
            <p style={{ color: "#c9d1d9", fontSize: 13, lineHeight: 1.6, margin: 0 }}>
              Add your Supabase keys in{" "}
              <a href="https://vercel.com" target="_blank"
                style={{ color: "#58a6ff", textDecoration: "underline" }}>
                Vercel → Settings → Environment Variables
              </a>{" "}then redeploy.
            </p>
            <pre style={{
              background: "#0d1117", border: "1px solid #30363d",
              borderRadius: 6, padding: 12, marginTop: 10,
              fontSize: 11, color: "#58a6ff", overflowX: "auto", whiteSpace: "pre-wrap",
            }}>
{`NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbG...`}
            </pre>
          </div>
        ) : (
          <Auth
            supabaseClient={supabase}
            appearance={{
              theme: ThemeSupa,
              variables: {
                default: {
                  colors: {
                    brand: "#1f6feb",
                    brandAccent: "#388bfd",
                    inputBackground: "#0d1117",
                    inputBorder: "#30363d",
                    inputText: "#e6edf3",
                    inputPlaceholder: "#7d8590",
                  },
                  borderWidths: { buttonBorderWidth: "0px", inputBorderWidth: "1px" },
                  radii: { borderRadiusButton: "8px", inputBorderRadius: "8px" },
                },
              },
            }}
            providers={["google", "github"]}
            redirectTo={
              typeof window !== "undefined"
                ? `${window.location.origin}/dashboard`
                : "/dashboard"
            }
            theme="dark"
          />
        )}
      </div>
    </div>
  );
}
