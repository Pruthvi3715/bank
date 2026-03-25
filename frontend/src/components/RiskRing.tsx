"use client";

import { useMemo } from "react";

interface RiskRingProps {
  score: number;
  label?: string;
  size?: number;
  className?: string;
  showValue?: boolean;
  strokeWidth?: number;
}

export default function RiskRing({
  score,
  label,
  size = 120,
  showValue = true,
  strokeWidth = 4,
}: RiskRingProps) {
  const clampedScore = Math.max(0, Math.min(100, Math.round(score)));
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clampedScore / 100) * circumference;

  const riskColor = useMemo(() => {
    if (clampedScore >= 80)
      return { stroke: "#ef4444", glow: "drop-shadow(0 0 8px rgba(239,68,68,0.5))" };
    if (clampedScore >= 60)
      return { stroke: "#f97316", glow: "drop-shadow(0 0 6px rgba(249,115,22,0.4))" };
    if (clampedScore >= 40)
      return { stroke: "#eab308", glow: "drop-shadow(0 0 6px rgba(234,179,8,0.3))" };
    return { stroke: "#10b981", glow: "drop-shadow(0 0 6px rgba(16,185,129,0.3))" };
  }, [clampedScore]);

  const riskLabel = useMemo(() => {
    if (clampedScore >= 80) return "CRITICAL";
    if (clampedScore >= 60) return "HIGH";
    if (clampedScore >= 40) return "ELEVATED";
    return "LOW";
  }, [clampedScore]);

  const center = size / 2;

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
          style={{ filter: clampedScore > 0 ? riskColor.glow : undefined }}
        >
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-border"
          />
          {clampedScore > 0 && (
            <circle
              cx={center}
              cy={center}
              r={radius}
              fill="none"
              stroke={riskColor.stroke}
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              strokeLinecap="butt"
              className="transition-all duration-700 ease-out"
            />
          )}
        </svg>
        {showValue && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span
              className="font-mono font-bold tabular-nums text-foreground"
              style={{ fontSize: size * 0.22 }}
            >
              {clampedScore}
            </span>
            <span
              className="font-mono uppercase tracking-widest text-muted-foreground"
              style={{ fontSize: Math.max(7, size * 0.07) }}
            >
              {riskLabel}
            </span>
          </div>
        )}
      </div>
      {label && (
        <span className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground">
          {label}
        </span>
      )}
    </div>
  );
}
