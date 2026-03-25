"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: "amber" | "emerald" | "red" | "cyan" | "orange";
  delay?: number;
}

const colorMap: Record<string, { border: string; text: string; bg: string }> = {
  amber: { border: "border-amber-500/30", text: "text-amber-500", bg: "bg-amber-500/8" },
  emerald: { border: "border-emerald-500/30", text: "text-emerald-500", bg: "bg-emerald-500/8" },
  red: { border: "border-red-500/30", text: "text-red-500", bg: "bg-red-500/8" },
  cyan: { border: "border-cyan-500/30", text: "text-cyan-500", bg: "bg-cyan-500/8" },
  orange: { border: "border-orange-500/30", text: "text-orange-500", bg: "bg-orange-500/8" },
};

export default function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = "amber",
  delay = 0,
}: StatsCardProps) {
  const c = colorMap[color] || colorMap.amber;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay }}
      className={`border ${c.border} bg-card p-3 group hover:bg-secondary/50 transition-colors cursor-default`}
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
          {title}
        </span>
        <div className={`p-1 ${c.bg}`}>
          <Icon className={`w-3.5 h-3.5 ${c.text}`} />
        </div>
      </div>
      <div className={`text-2xl font-semibold tabular-nums ${c.text}`}>
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
      {subtitle && (
        <p className="text-[10px] text-muted-foreground mt-1 truncate font-mono">
          {subtitle}
        </p>
      )}
    </motion.div>
  );
}
