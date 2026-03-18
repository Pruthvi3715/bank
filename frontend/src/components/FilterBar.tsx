"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
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
    <div className="border-b border-border">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full justify-between h-9 px-4 text-sm"
      >
        <span className="flex items-center gap-2">
          <SlidersHorizontal className="w-3.5 h-3.5" />
          Filters
          {activeFilters > 0 && (
            <span className="ml-1 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
              {activeFilters}
            </span>
          )}
        </span>
        <ChevronDown
          className={`w-4 h-4 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`}
        />
      </Button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-4 pt-0">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-muted-foreground">
                  Pattern
                </span>
                <select
                  value={patternFilter}
                  onChange={(e) =>
                    setPatternFilter(e.target.value as PatternType | "All")
                  }
                  className="h-8 rounded-md border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
                >
                  <option value="All">All Patterns</option>
                  <option value="Cycle">Cycle</option>
                  <option value="Smurfing">Smurfing</option>
                  <option value="HubAndSpoke">Hub & Spoke</option>
                  <option value="PassThrough">Pass Through</option>
                  <option value="DormantActivation">Dormant</option>
                  <option value="TemporalLayering">Temporal</option>
                </select>
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-muted-foreground">
                  Channel
                </span>
                <select
                  value={channelFilter}
                  onChange={(e) => setChannelFilter(e.target.value)}
                  className="h-8 rounded-md border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
                >
                  {allChannels.map((channel) => (
                    <option key={channel} value={channel}>
                      {channel}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-muted-foreground">
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

              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-muted-foreground">
                  From Date
                </span>
                <input
                  type="datetime-local"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  className="h-8 rounded-md border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
                />
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-medium text-muted-foreground">
                  To Date
                </span>
                <input
                  type="datetime-local"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  className="h-8 rounded-md border border-input bg-background px-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
                />
              </label>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
