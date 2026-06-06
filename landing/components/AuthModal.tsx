import { useState } from "react";
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
      <div className="relative w-full max-w-md bg-bg1 border border-border rounded-2xl p-8 shadow-2xl">
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-muted hover:text-white transition-colors"
        >
          <X size={20} />
        </button>

        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white mb-1">
            🤖 Coder Buddy
          </h2>
          <p className="text-muted text-sm">
            Sign in for free — 3 runs/month, no credit card needed.
          </p>
        </div>

        {!isSupabaseConfigured ? (
          <div
            style={{
              background: "rgba(248,81,73,0.08)",
              border: "1px solid rgba(248,81,73,0.3)",
              borderRadius: "10px",
              padding: "16px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
              <AlertTriangle size={16} color="#f85149" />
              <span style={{ color: "#f85149", fontWeight: 600, fontSize: "14px" }}>
                Supabase Not Configured
              </span>
            </div>
            <p style={{ color: "#c9d1d9", fontSize: "13px", lineHeight: 1.6, margin: 0 }}>
              To enable sign-in, add your Supabase keys in{" "}
              <a
                href="https://vercel.com"
                target="_blank"
                style={{ color: "#58a6ff", textDecoration: "underline" }}
              >
                Vercel → Project Settings → Environment Variables
              </a>
              :
            </p>
            <pre
              style={{
                background: "#0d1117",
                border: "1px solid #30363d",
                borderRadius: "6px",
                padding: "12px",
                marginTop: "10px",
                fontSize: "11px",
                color: "#58a6ff",
                overflowX: "auto",
                whiteSpace: "pre-wrap",
              }}
            >
{`NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbG...`}
            </pre>
            <p style={{ color: "#7d8590", fontSize: "12px", marginTop: "8px", marginBottom: 0 }}>
              Then redeploy on Vercel for changes to take effect.
            </p>
          </div>
        ) : (
          <Auth
            supabaseClient={supabase}
            appearance={{
              theme: ThemeSupa,
              variables: {
                default: {
                  colors: {
                    brand:        "#1f6feb",
                    brandAccent:  "#388bfd",
                    inputBackground: "#0d1117",
                    inputBorder:     "#30363d",
                    inputText:       "#e6edf3",
                    inputPlaceholder:"#7d8590",
                  },
                  borderWidths: { buttonBorderWidth: "0px", inputBorderWidth: "1px" },
                  radii:        { borderRadiusButton: "8px", inputBorderRadius: "8px" },
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

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

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
      <div className="relative w-full max-w-md bg-bg1 border border-border rounded-2xl p-8 shadow-2xl">
        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-muted hover:text-white transition-colors"
        >
          <X size={20} />
        </button>

        <div className="mb-6">
          <h2 className="text-2xl font-bold text-white mb-1">
            🤖 Coder Buddy
          </h2>
          <p className="text-muted text-sm">
            Sign in for free — 3 runs/month, no credit card needed.
          </p>
        </div>

        <Auth
          supabaseClient={supabase}
          appearance={{
            theme: ThemeSupa,
            variables: {
              default: {
                colors: {
                  brand:        "#1f6feb",
                  brandAccent:  "#388bfd",
                  inputBackground: "#0d1117",
                  inputBorder:     "#30363d",
                  inputText:       "#e6edf3",
                  inputPlaceholder:"#7d8590",
                },
                borderWidths: { buttonBorderWidth: "0px", inputBorderWidth: "1px" },
                radii:        { borderRadiusButton: "8px", inputBorderRadius: "8px" },
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
      </div>
    </div>
  );
}
