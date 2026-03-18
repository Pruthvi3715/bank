export type PatternType =
  | "Cycle"
  | "Smurfing"
  | "HubAndSpoke"
  | "PassThrough"
  | "DormantActivation"
  | "TemporalLayering";

export interface Alert {
  alert_id: string;
  timestamp: string;
  subgraph_nodes: string[];
  subgraph_edges: string[];
  risk_score: number;
  pattern_type: PatternType;
  structural_score: number;
  innocence_discount: number;
  disposition: string;
  channels: string[];
  scoring_signals: Record<string, number>;
  llm_explanation?: string;
}

export interface GraphNode {
  id: string;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  amount: number;
  channel: string;
}

export interface GraphPayload {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface PipelineStats {
  total_txns: number;
  total_nodes: number;
  total_edges: number;
  alerts_generated: number;
  pattern_counts: Record<string, number>;
}

export interface AgentActivityStep {
  agent: string;
  message: string;
}

export interface PipelineResponse {
  alerts: Alert[];
  graph: GraphPayload;
  stats: PipelineStats;
  agent_activity?: AgentActivityStep[];
}
