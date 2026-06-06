interface UsageBarProps {
  used:  number;
  limit: number | "unlimited";
  plan:  string;
}

export default function UsageBar({ used, limit, plan }: UsageBarProps) {
  const isUnlimited = limit === "unlimited";
  const pct         = isUnlimited ? 0 : Math.min((used / (limit as number)) * 100, 100);
  const color       = pct >= 90 ? "#f85149" : pct >= 70 ? "#e3b341" : "#3fb950";

  return (
    <div className="bg-bg2 border border-border rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold text-white">Monthly Usage</span>
        <span className="text-xs font-bold px-2.5 py-1 rounded-full"
          style={{
            background: plan === "free" ? "#30363d" : plan === "pro" ? "#d2a8ff22" : "#e3b34122",
            color:      plan === "free" ? "#7d8590"  : plan === "pro" ? "#d2a8ff"  : "#e3b341",
            border:     `1px solid ${plan === "free" ? "#30363d" : plan === "pro" ? "#d2a8ff44" : "#e3b34144"}`,
          }}>
          {plan.toUpperCase()}
        </span>
      </div>

      <div className="flex items-end justify-between mb-2">
        <span className="text-3xl font-extrabold text-white">{used}</span>
        <span className="text-muted text-sm">
          / {isUnlimited ? "∞" : limit} runs
        </span>
      </div>

      {!isUnlimited && (
        <div className="w-full bg-bg1 rounded-full h-2.5 mt-2">
          <div
            className="h-2.5 rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, background: color }}
          />
        </div>
      )}

      {!isUnlimited && pct >= 90 && (
        <p className="text-xs mt-2" style={{ color }}>
          {pct === 100 ? "Limit reached — upgrade to continue." : "Almost at your limit!"}
        </p>
      )}
    </div>
  );
}
