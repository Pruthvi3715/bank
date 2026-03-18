"use client";

import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download, FileText, AlertCircle, CheckCircle, HelpCircle } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import RiskRing from "@/components/RiskRing";
import { Alert } from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function SARReport({ alert }: { alert: Alert | null }) {
  const printRef = useRef<HTMLDivElement>(null);
  const [feedbackConfidence, setFeedbackConfidence] = useState(3);
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);

  const submitFeedback = async (
    decision: "confirmed_fraud" | "false_positive" | "unclear"
  ) => {
    if (!alert) return;
    setFeedbackSent(null);
    try {
      const res = await fetch(`${API_BASE}/api/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          alert_id: alert.alert_id,
          decision,
          confidence: feedbackConfidence,
          pattern_type: alert.pattern_type,
          notes: feedbackNotes,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      setFeedbackSent(decision);
    } catch {
      setFeedbackSent("error");
    }
  };

  const downloadPDF = async () => {
    if (!alert) return;
    if (typeof window !== "undefined") {
      const html2pdf = (await import("html2pdf.js")).default;
      const element = printRef.current;
      if (element) {
        const opt = {
          margin: 0.5,
          filename: `SAR_FIU_IND_${alert.alert_id.split("-")[0]}.pdf`,
          image: { type: "jpeg" as const, quality: 0.98 },
          html2canvas: { scale: 2 },
          jsPDF: {
            unit: "in",
            format: "letter",
            orientation: "portrait" as const,
          },
        };
        html2pdf().set(opt).from(element).save();
      }
    }
  };

  if (!alert) {
    return (
      <Card className="h-full">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-muted-foreground" />
            <CardTitle className="text-sm font-medium">SAR Report</CardTitle>
          </div>
          <CardDescription>
            Select an alert to view its Suspicious Activity Report
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[300px]">
          <div className="text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-xl border-2 border-dashed border-muted-foreground/30 flex items-center justify-center">
              <FileText className="w-6 h-6 text-muted-foreground/40" />
            </div>
            <p className="text-sm text-muted-foreground">
              No alert selected
            </p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Click on an alert in the queue to view details
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3 flex-shrink-0">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              <CardTitle className="text-sm font-medium">SAR Report</CardTitle>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono">
              {alert.alert_id.slice(0, 8)}...
            </Badge>
          </div>
          <div className="flex items-center gap-3">
            <RiskRing score={alert.risk_score} size={36} strokeWidth={2.5} />
            <Button
              size="sm"
              variant="outline"
              onClick={downloadPDF}
              className="gap-1.5 text-xs h-7"
            >
              <Download className="w-3 h-3" />
              Export PDF
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 p-0 min-h-0">
        <ScrollArea className="h-full">
          <div className="px-4 pb-4 space-y-5" ref={printRef}>
            {/* Detection Summary */}
            <motion.section
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
            >
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <div className="w-1 h-3 rounded-full bg-primary" />
                Detection Summary
              </h3>
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-muted/50 border border-border">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">
                    Pattern
                  </span>
                  <span className="text-sm font-medium">{alert.pattern_type}</span>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 border border-border">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">
                    Discount
                  </span>
                  <span className="text-sm font-medium">{alert.innocence_discount}%</span>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 border border-border">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider block mb-1">
                    Score
                  </span>
                  <span className="text-sm font-medium">{alert.risk_score.toFixed(1)}/100</span>
                </div>
              </div>
            </motion.section>

            {/* Narrative */}
            <motion.section
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <div className="w-1 h-3 rounded-full bg-primary" />
                Investigative Narrative
              </h3>
              <div className="p-4 rounded-lg border border-border bg-muted/30 text-sm leading-relaxed whitespace-pre-wrap">
                {alert.llm_explanation}
              </div>
            </motion.section>

            {/* Feedback */}
            <motion.section
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <div className="w-1 h-3 rounded-full bg-primary" />
                Investigator Feedback
              </h3>
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-muted-foreground">Confidence:</span>
                  <select
                    value={feedbackConfidence}
                    onChange={(e) => setFeedbackConfidence(Number(e.target.value))}
                    className="h-7 rounded-md border border-input bg-background px-2 text-xs focus:outline-none focus:ring-2 focus:ring-ring/50"
                  >
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => submitFeedback("false_positive")}
                    className="gap-1.5 text-xs h-8 border-emerald-500/30 text-emerald-500 hover:bg-emerald-500/10"
                  >
                    <CheckCircle className="w-3 h-3" />
                    False Positive
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => submitFeedback("confirmed_fraud")}
                    className="gap-1.5 text-xs h-8 border-red-500/30 text-red-500 hover:bg-red-500/10"
                  >
                    <AlertCircle className="w-3 h-3" />
                    Confirmed Fraud
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => submitFeedback("unclear")}
                    className="gap-1.5 text-xs h-8"
                  >
                    <HelpCircle className="w-3 h-3" />
                    Unclear
                  </Button>
                </div>
                <textarea
                  placeholder="Additional notes (optional)"
                  value={feedbackNotes}
                  onChange={(e) => setFeedbackNotes(e.target.value)}
                  className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm min-h-[60px] focus:outline-none focus:ring-2 focus:ring-ring/50 resize-none"
                />
                {feedbackSent === "error" && (
                  <p className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Feedback submission failed
                  </p>
                )}
                {feedbackSent && feedbackSent !== "error" && (
                  <p className="text-xs text-emerald-500 flex items-center gap-1">
                    <CheckCircle className="w-3 h-3" />
                    Feedback recorded: {feedbackSent.replace("_", " ")}
                  </p>
                )}
              </div>
            </motion.section>

            {/* Edge Flow */}
            <motion.section
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3 flex items-center gap-2">
                <div className="w-1 h-3 rounded-full bg-primary" />
                Edge Flow ({alert.subgraph_edges.length})
              </h3>
              <div className="rounded-lg border border-border max-h-[150px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-[10px] text-muted-foreground uppercase tracking-wider">
                        Transaction Flow
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {alert.subgraph_edges.map((edge: string, i: number) => (
                      <TableRow key={i}>
                        <TableCell className="text-xs font-mono text-muted-foreground">
                          {edge}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </motion.section>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
