import { useState } from "react";
import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { supabase } from "@/lib/supabase";
import { X } from "lucide-react";

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
