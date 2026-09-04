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

export type IncidentAnalysis = {
  incident?: {
    incident_id?: string;
    location?: string;
    incident_type?: string;
    summary?: string;
    indicators?: string[];
    entities_involved?: string[];
    timestamp?: string;
  };
  session?: { id?: string; is_fresh?: boolean };
  baseline?: { risk?: string; recommendation?: string; confidence?: number; factors?: string[] };
  decision?: { risk?: string; recommendation?: string; changed?: boolean; confidence?: number; escalation_reason?: string };
  decision_changed?: boolean;
  decision_change?: { from_risk?: string; to_risk?: string; from_recommendation?: string; to_recommendation?: string };
  memory?: { found?: boolean; count?: number; records?: MemoryRecord[] };
  inference?: { is_recurrent?: boolean; recurrence_count?: number; unresolved_history?: boolean; summary?: string; applicable_lessons?: string[] };
  why_decision_changed?: string;
  provenance?: { facts?: string; retrieval?: string; inference?: string; decision_shift?: string };
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
  memoryStatus: () => request<MemoryStatusResponse>("/api/memory/status"),
  analyzeIncident: (body: IncidentRequest) => request<IncidentAnalysis>("/api/incidents/analyze", { method: "POST", body: JSON.stringify(body) }),
  searchMemory: (query: string) => request<MemorySearchResponse>(`/api/memory/search?q=${encodeURIComponent(query)}`),
  recordOutcome: (body: OutcomeRequest) => request<OutcomeResponse>("/api/outcomes", { method: "POST", body: JSON.stringify(body) }),
};

export const memoraApiConfig = { baseUrl: API_BASE_URL };
