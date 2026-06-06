import { Check, X, Zap } from "lucide-react";
import clsx from "clsx";

interface PricingCardProps {
  name:        string;
  price:       number;
  annualPrice: number;
  isAnnual:    boolean;
  badge?:      string;
  color:       "gray" | "purple" | "yellow";
  features: {
    label:   string;
    included: boolean;
  }[];
  cta:       string;
  ctaStyle?: "primary" | "outline";
  onCta:     () => void;
}

const colorMap = {
  gray:   { border: "border-border",  badge: "bg-muted/20 text-muted",      glow: "" },
  purple: { border: "border-purple/50", badge: "bg-purple/20 text-purple", glow: "shadow-purple/10 shadow-2xl" },
  yellow: { border: "border-yellow/50", badge: "bg-yellow/20 text-yellow", glow: "shadow-yellow/10 shadow-2xl" },
};

export default function PricingCard({
  name, price, annualPrice, isAnnual, badge, color,
  features, cta, ctaStyle = "primary", onCta,
}: PricingCardProps) {
  const c         = colorMap[color];
  const displayed = isAnnual ? Math.round(annualPrice / 12) : price;

  return (
    <div className={clsx(
      "relative flex flex-col bg-bg2 border rounded-2xl p-8 transition-all duration-300",
      c.border, c.glow,
      color === "purple" && "scale-105 z-10",
    )}>
      {badge && (
        <div className={clsx("absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-bold tracking-wide", c.badge)}>
          {badge}
        </div>
      )}

      <div className="mb-6">
        <h3 className="text-lg font-bold text-white mb-4">{name}</h3>
        <div className="flex items-end gap-1">
          <span className="text-4xl font-extrabold text-white">
            {price === 0 ? "₹0" : `₹${displayed}`}
          </span>
          {price > 0 && (
            <span className="text-muted text-sm mb-1.5">/month</span>
          )}
        </div>
        {isAnnual && price > 0 && (
          <p className="text-green text-xs mt-1 font-semibold">
            ✓ Save 20% — ₹{annualPrice}/year
          </p>
        )}
      </div>

      <ul className="space-y-3 flex-1 mb-8">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-3 text-sm">
            {f.included
              ? <Check size={16} className="text-green shrink-0" />
              : <X     size={16} className="text-muted/50 shrink-0" />
            }
            <span className={f.included ? "text-gray-200" : "text-muted line-through"}>
              {f.label}
            </span>
          </li>
        ))}
      </ul>

      <button
        onClick={onCta}
        className={clsx(
          "w-full py-3 rounded-xl font-semibold text-sm transition-all duration-200 hover:-translate-y-0.5",
          ctaStyle === "primary"
            ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-900/30"
            : "border border-border text-white hover:border-blue/50",
        )}
      >
        {cta}
      </button>
    </div>
  );
}
