"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, SlidersHorizontal } from "lucide-react";
import type { PatternType } from "@/types/api";

interface FilterBarProps {
  patternFilter: PatternType | "All";
  setPatternFilter: (v: PatternType | "All") => void;
  channelFilter: string;
  setChannelFilter: (v: string) => void;
  minScore: number;
  setMinScore: (v: number) => void;
  fromDate: string;
  setFromDate: (v: string) => void;
  toDate: string;
  setToDate: (v: string) => void;
  allChannels: string[];
}

export default function FilterBar({
  patternFilter,
  setPatternFilter,
  channelFilter,
  setChannelFilter,
  minScore,
  setMinScore,
  fromDate,
  setFromDate,
  toDate,
  setToDate,
  allChannels,
}: FilterBarProps) {
  const [isOpen, setIsOpen] = useState(false);

  const activeFilters = [
    patternFilter !== "All",
    channelFilter !== "All",
    minScore > 0,
    fromDate !== "",
    toDate !== "",
  ].filter(Boolean).length;

  return (
    <div className="border-t border-border/50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between h-8 px-4 text-[10px] font-mono uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
      >
        <span className="flex items-center gap-2">
          <SlidersHorizontal className="w-3 h-3" />
          Filters
          {activeFilters > 0 && (
            <span className="flex h-4 min-w-4 items-center justify-center px-1 bg-primary text-primary-foreground text-[9px] font-bold">
              {activeFilters}
            </span>
          )}
        </span>
        <ChevronDown
          className={`w-3 h-3 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2 px-4 pb-3">
              <label className="flex flex-col gap-1">
                <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">
                  Pattern
                </span>
                <select
                  value={patternFilter}
                  onChange={(e) =>
                    setPatternFilter(e.target.value as PatternType | "All")
                  }
                  className="h-7 border border-border bg-secondary px-2 text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="All">All</option>
                  <option value="Cycle">Cycle</option>
                  <option value="Smurfing">Smurfing</option>
                  <option value="HubAndSpoke">Hub & Spoke</option>
                  <option value="PassThrough">Pass Through</option>
                  <option value="DormantActivation">Dormant</option>
                  <option value="TemporalLayering">Temporal</option>
                </select>
              </label>

              <label className="flex flex-col gap-1">
                <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">
                  Channel
                </span>
                <select
                  value={channelFilter}
                  onChange={(e) => setChannelFilter(e.target.value)}
                  className="h-7 border border-border bg-secondary px-2 text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  {allChannels.map((ch) => (
                    <option key={ch} value={ch}>
                      {ch}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col gap-1">
                <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">
                  Min Score: {minScore}
                </span>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={minScore}
                  onChange={(e) => setMinScore(Number(e.target.value))}
                  className="mt-1 accent-primary"
                />
              </label>

              <label className="flex flex-col gap-1">
                <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">
                  From
                </span>
                <input
                  type="datetime-local"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  className="h-7 border border-border bg-secondary px-2 text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </label>

              <label className="flex flex-col gap-1">
                <span className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">
                  To
                </span>
                <input
                  type="datetime-local"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  className="h-7 border border-border bg-secondary px-2 text-[11px] font-mono focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </label>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
