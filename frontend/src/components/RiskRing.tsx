"use client";

import { cn } from "@/lib/utils";

interface RiskRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
  showValue?: boolean;
}

export default function RiskRing({
  score,
  size = 48,
  strokeWidth = 4,
  className,
  showValue = true,
}: RiskRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (s: number) => {
    if (s >= 80) return "stroke-red-500";
    if (s >= 60) return "stroke-orange-500";
    if (s >= 40) return "stroke-yellow-500";
    return "stroke-emerald-500";
  };

  const getBgColor = (s: number) => {
    if (s >= 80) return "text-red-500/20";
    if (s >= 60) return "text-orange-500/20";
    if (s >= 40) return "text-yellow-500/20";
    return "text-emerald-500/20";
  };

  return (
    <div
      className={cn("relative inline-flex items-center justify-center", className)}
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          className={cn("transition-all duration-500", getBgColor(score))}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={cn(
            "transition-all duration-700 ease-out",
            getColor(score)
          )}
        />
      </svg>
      {showValue && (
        <span className="absolute text-xs font-bold font-mono">
          {score.toFixed(0)}
        </span>
      )}
    </div>
  );
}
