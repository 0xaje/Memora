export type MemoraErrorCode =
  | "VALIDATION_ERROR"
  | "SIBYL_UNAVAILABLE"
  | "SIBYL_SERVICE_ERROR"
  | "INTERNAL_SERVER_ERROR"
  | "NETWORK_ERROR"
  | "MALFORMED_RESPONSE";

export class MemoraApiError extends Error {
  constructor(
    message: string,
    public readonly code: MemoraErrorCode,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "MemoraApiError";
  }
}

export type HealthResponse = {
  status: string;
  sibyl_memory_connected: boolean;
  version?: string;
};

export type MemoryStatusResponse = {
  status: string;
  backend?: string;
  storage_state?: string;
  tenant_id?: string;
  counts?: Record<string, number>;
  logical_size_bytes?: number;
};

export type IncidentRequest = {
  raw_text: string;
  location?: string;
  incident_type?: string;
  reported_by?: string;
  session_id?: string;
  tenant_id?: string;
};

export type MemoryRecord = {
  category?: string;
  id?: string;
  tier?: string;
  location?: string;
  summary?: string;
  status?: string;
  timestamp?: string;
  score?: number;
  action_taken?: string;
  rule_or_insight?: string;
  recurrence_count?: number | null;
  successful_mitigation?: string | null;
};

export type EvidenceItem = {
  source: string;
  type: "CURRENT_FACT" | "HISTORICAL_FACT" | "INFERENCE" | "RECOMMENDATION" | "UNKNOWN";
  confidence: number;
  entity_or_location?: string;
  supporting_record_id?: string;
  text: string;
};

export type FailedMitigation = {
  prior_action: string;
  observed_result: string;
  failure_diagnosis: string;
  current_implication: string;
};

export type ActionableLesson = {
  lesson_id: string;
  historical_rule: string;
  current_implication: string;
  recommended_adjustment: string;
};

export type HistoricalPatternDetail = {
  pattern_type: string;
  title: string;
  description: string;
  supporting_record_ids?: string[];
};

export type IncidentAnalysis = {
  incident?: {
    incident_id?: string;
    location?: string;
    incident_type?: string;
    summary?: string;
    indicators?: string[];
    entities_involved?: string[];
    timestamp?: string;
    approximate_time?: string;
    duration?: string;
    reported_by?: string;
    unknowns?: string[];
  };
  session?: { id?: string; is_fresh?: boolean };
  baseline?: { risk?: string; recommendation?: string; confidence?: number; factors?: string[] };
  decision?: { risk?: string; recommendation?: string; changed?: boolean; confidence?: number; escalation_reason?: string };
  decision_changed?: boolean;
  decision_change?: { from_risk?: string; to_risk?: string; from_recommendation?: string; to_recommendation?: string };
  memory?: { found?: boolean; count?: number; records?: MemoryRecord[] };
  inference?: {
    is_recurrent?: boolean;
    recurrence_count?: number;
    unresolved_history?: boolean;
    unresolved_incident_ids?: string[];
    has_prior_failed_outcome?: boolean;
    failed_prior_actions?: string[];
    verified_mitigations?: string[];
    applicable_lessons?: string[];
    failed_mitigation_details?: FailedMitigation[];
    actionable_lessons_details?: ActionableLesson[];
    patterns_detected?: HistoricalPatternDetail[];
    is_resolved_precedent?: boolean;
    summary?: string;
  };
  why_decision_changed?: string;
  provenance?: { facts?: string; retrieval?: string; inference?: string; decision_shift?: string };
  evidence_chain?: EvidenceItem[];
  failed_mitigations?: FailedMitigation[];
  actionable_lessons?: ActionableLesson[];
  patterns_detected?: HistoricalPatternDetail[];
  unknowns?: string[];
};

export type MemorySearchResponse = {
  query: string;
  tenant_id?: string;
  count?: number;
  results: MemoryRecord[];
};

export type OutcomeRequest = {
  incident_id: string;
  action_taken: string;
  observed_result: string;
  is_resolved: boolean;
  unresolved_reason?: string;
  operational_lesson?: string;
  tenant_id?: string;
};

export type OutcomeResponse = {
  status?: string;
  outcome_id?: string;
  incident_id?: string;
  is_resolved?: boolean;
  action_taken?: string;
  observed_result?: string;
  lesson_id?: string | null;
  lesson_rule?: string | null;
  recurrence_count?: number | null;
  successful_mitigation?: string | null;
  message?: string;
};

export type ShiftHandoverReport = {
  shift_period_hours: number;
  generated_at: string;
  tenant_id: string;
  threat_level: string;
  total_incidents_recorded: number;
  active_unresolved_threats: Array<{ risk_id: string; location: string; severity: string; description: string }>;
  failed_mitigations_to_avoid: Array<{ outcome_id: string; incident_id: string; failed_action: string; observed_result: string; unresolved_reason?: string }>;
  operational_rules_active: Array<{ lesson_id: string; location?: string; operational_rule: string }>;
  supervisor_directives: string[];
};

export type EventProof = {
  event_id: string;
  timestamp: string;
  action: string;
  evaluated_entity: Record<string, unknown>;
  event_hash: string;
  chain_hash: string;
};

export type AuditExport = {
  export_id: string;
  tenant_id: string;
  generated_at: string;
  total_events: number;
  compliance_framework: string;
  cryptographic_root_digest: string;
  chain_verified: boolean;
  events: EventProof[];
};

export type TierStatusResponse = {
  current_tier: string;
  tenant_id: string;
  status: {
    tier?: string;
    db_size_bytes?: number;
    soft_cap_bytes?: number;
    pct_used?: number;
    uncapped?: boolean;
    upgrade_url?: string;
  };
  capabilities: {
    name: string;
    storage_limit: string;
    fts5_indexing: boolean;
    multi_tier_architecture: boolean;
    cold_audit_journal: boolean;
    distributed_clustering: boolean;
  };
};

const API_BASE_URL = (import.meta.env.VITE_MEMORA_API_URL || "http://localhost:8000").replace(/\/$/, "");

function assertObject(value: unknown, endpoint: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new MemoraApiError(`Malformed response from ${endpoint}.`, "MALFORMED_RESPONSE");
  }
  return value as Record<string, unknown>;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
  } catch {
    throw new MemoraApiError("Memora backend is unreachable.", "NETWORK_ERROR");
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const body = payload && typeof payload === "object" ? (payload as { detail?: { code?: string; message?: string } }).detail : undefined;
    const code = body?.code as MemoraErrorCode | undefined;
    throw new MemoraApiError(body?.message || `Memora request failed with HTTP ${response.status}.`, code || (response.status === 503 ? "SIBYL_UNAVAILABLE" : "INTERNAL_SERVER_ERROR"), response.status);
  }

  return assertObject(payload, path) as T;
}

export const memoraApi = {
  health: () => request<HealthResponse>("/health"),
  memoryStatus: (tenantId?: string) => request<MemoryStatusResponse>(`/api/memory/status${tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ""}`),
  analyzeIncident: (body: IncidentRequest) => request<IncidentAnalysis>("/api/incidents/analyze", { method: "POST", body: JSON.stringify(body) }),
  searchMemory: (query: string, tenantId?: string) => request<MemorySearchResponse>(`/api/memory/search?q=${encodeURIComponent(query)}${tenantId ? `&tenant_id=${encodeURIComponent(tenantId)}` : ""}`),
  recordOutcome: (body: OutcomeRequest) => request<OutcomeResponse>("/api/outcomes", { method: "POST", body: JSON.stringify(body) }),
  shiftHandover: (hours: number = 24, tenantId?: string) => request<ShiftHandoverReport>(`/api/reports/shift-handover?hours=${hours}${tenantId ? `&tenant_id=${encodeURIComponent(tenantId)}` : ""}`),
  exportAudit: (limit: number = 100, tenantId?: string) => request<AuditExport>(`/api/audit/export?limit=${limit}${tenantId ? `&tenant_id=${encodeURIComponent(tenantId)}` : ""}`),
  getTierStatus: (tenantId?: string) => request<TierStatusResponse>(`/api/memory/tier${tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ""}`),
  setTier: (tier: string, tenantId?: string) => request<{ status: string; active_tier: string }>(`/api/memory/tier${tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : ""}`, { method: "POST", body: JSON.stringify({ tier }) }),
};

export const memoraApiConfig = { baseUrl: API_BASE_URL };

export const BUILD_METADATA = {
  commitSha: typeof __GIT_COMMIT_SHA__ !== "undefined" ? __GIT_COMMIT_SHA__ : "dev-local",
  buildTimestamp: typeof __BUILD_TIMESTAMP__ !== "undefined" ? __BUILD_TIMESTAMP__ : new Date().toISOString(),
};
