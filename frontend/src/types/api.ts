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
  if_score?: number;
  xgb_score?: number;
}

export interface GraphNode {
  id: string;
  pagerank?: number;
  betweenness?: number;
  total_sent?: number;
  total_received?: number;
  channels?: string[];
  if_score?: number;
  xgb_score?: number;
}

export interface GraphLink {
  source: string | GraphNode;
  target: string | GraphNode;
  amount: number;
  channel: string;
  color?: string;
  timestamp?: string;
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
  advanced_detection?: AdvancedDetection;
  ml_info?: MLInfo;
}

export interface SARChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface QuickQuestion {
  label: string;
  prompt: string;
}

export interface AdvancedDetection {
  tarjan_sccs: number;
  fraud_rings: number;
  centrality_top: {
    pagerank: [string, number][];
    betweenness: [string, number][];
  };
  dormant_motifs: number;
  profile_mismatches: number;
}

export interface MLInfo {
  feature_importance: Record<string, number>;
  model_status: {
    isolation_forest: string;
    gradient_boosting: string;
  };
}
