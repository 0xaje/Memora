import React, { useEffect, useMemo, useRef, useState } from "react";
import { trpc } from "@/lib/trpc";
import {
  memoraApi,
  MemoraApiError,
  type IncidentAnalysis,
  type MemorySearchResponse,
  type MemoryStatusResponse,
  type OutcomeResponse,
} from "@/lib/memora-api";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  BrainCircuit,
  Check,
  ChevronDown,
  ClipboardCheck,
  Clock3,
  Database,
  FileSearch,
  Grid2X2,
  HelpCircle,
  History,
  Info,
  LockKeyhole,
  Menu,
  Network,
  PanelRight,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useAuth } from "@/_core/hooks/useAuth";
import { startLogin } from "@/const";

export const workspaceContractState = {
  incidentAnalysis: "unavailable",
  memorySearch: "unavailable",
  memoryStatus: "unavailable",
  outcomeRecording: "unavailable",
  evidenceSummary: "unavailable",
} as const;

const sections = [
  { id: "workspace", label: "Incident workspace", icon: Grid2X2 },
  { id: "memory", label: "Memory explorer", icon: History },
  { id: "provenance", label: "Provenance", icon: Network },
];

type Notice = { type: "info" | "error"; message: string } | null;
type BackendState = { status: "idle" | "loading" | "success" | "empty" | "unavailable" | "error"; message?: string };
type LiveWorkspace = {
  analysis: IncidentAnalysis | null;
  analysisState: BackendState;
  memoryStatus: MemoryStatusResponse | null;
  memoryState: BackendState;
  search: MemorySearchResponse | null;
  searchState: BackendState;
  outcome: OutcomeResponse | null;
  outcomeState: BackendState;
};

const initialLiveWorkspace: LiveWorkspace = {
  analysis: null,
  analysisState: { status: "idle" },
  memoryStatus: null,
  memoryState: { status: "loading" },
  search: null,
  searchState: { status: "idle" },
  outcome: null,
  outcomeState: { status: "idle" },
};

function apiMessage(error: unknown) {
  return error instanceof MemoraApiError ? error.message : "Memora backend request failed.";
}

export function getSibylStatusCopy(state: BackendState) {
  if (state.status === "loading") return { label: "Sibyl checking", tone: "warn" as const };
  if (state.status === "success") return { label: "Sibyl connected", tone: "ok" as const };
  if (state.status === "unavailable") return { label: "Sibyl unavailable", tone: "warn" as const };
  return { label: "Sibyl error", tone: "warn" as const };
}

export function getAnalysisStateCopy(state: BackendState) {
  if (state.status === "loading") return "Waiting for Memora backend";
  if (state.status === "unavailable") return state.message || "Unable to analyze incident";
  if (state.status === "error") return state.message || "The backend did not return an analysis.";
  if (state.status === "success") return "Backend analysis received";
  return "No incident analyzed yet";
}

export function getMemorySearchStateLabel(state: BackendState, count?: number) {
  if (state.status === "loading") return "SEARCHING";
  if (state.status === "success") return `${count ?? 0} RESULTS`;
  if (state.status === "empty") return "NO MATCHES";
  if (state.status === "unavailable") return "SIBYL UNAVAILABLE";
  if (state.status === "error") return "SEARCH ERROR";
  return "GET /api/memory/search";
}

function SectionKicker({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <div className="section-kicker">
      <span className="section-kicker__label">{label}</span>
      <span className="section-kicker__line" />
      {children}
    </div>
  );
}

function EmptyPanel({
  icon: Icon,
  eyebrow,
  title,
  description,
  action,
}: {
  icon: typeof Database;
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty-panel">
      <div className="empty-panel__icon"><Icon size={20} strokeWidth={1.5} /></div>
      <div>
        <p className="micro-label">{eyebrow}</p>
        <h3>{title}</h3>
        <p className="empty-panel__copy">{description}</p>
        {action}
      </div>
    </div>
  );
}

function StatusChip({ label, tone = "neutral" }: { label: string; tone?: "neutral" | "ok" | "warn" }) {
  return <span className={cn("status-chip", `status-chip--${tone}`)}><span className="status-chip__dot" />{label}</span>;
}

function Header({ active, onNavigate, onNewIncident, memoryState }: { active: string; onNavigate: (id: string) => void; onNewIncident: () => void; memoryState: BackendState }) {
  const { user, loading, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const { label: sibylLabel, tone: sibylTone } = getSibylStatusCopy(memoryState);
  return (
    <header className="topbar">
      <div className="topbar__brand" onClick={() => onNavigate("workspace")} role="button" tabIndex={0} onKeyDown={(event) => event.key === "Enter" && onNavigate("workspace")}>
        <div className="brand-mark"><span /><span /><span /></div>
        <div><div className="brand-name">MEMORA</div><div className="brand-subtitle">Operational memory system</div></div>
      </div>
      <nav className="topbar__nav" aria-label="Primary navigation">
        {sections.map((section) => {
          const Icon = section.icon;
          return <button key={section.id} className={cn("nav-link", active === section.id && "nav-link--active")} onClick={() => onNavigate(section.id)}><Icon size={15} />{section.label}</button>;
        })}
      </nav>
      <div className="topbar__actions">
        <StatusChip label={sibylLabel} tone={sibylTone} />
        <button className="header-icon-button" aria-label="Show system status"><Activity size={16} /></button>
        <button className="user-button" onClick={() => setMenuOpen((value) => !value)} aria-expanded={menuOpen}>
          <span className="avatar">{user?.name?.slice(0, 1).toUpperCase() || "O"}</span>
          <span className="user-button__name">{loading ? "Loading operator" : user?.name || "Operator"}</span>
          <ChevronDown size={14} />
        </button>
        {menuOpen && <div className="user-menu"><div className="user-menu__meta">{user?.email || "Unauthenticated session"}</div>{user ? <button onClick={logout}>Sign out</button> : <button onClick={() => startLogin()}>Sign in</button>}</div>}
      </div>
      <button className="mobile-menu" aria-label="Open navigation"><Menu size={20} /></button>
    </header>
  );
}

function BlueprintRail({ active, onNavigate }: { active: string; onNavigate: (id: string) => void }) {
  return <aside className="blueprint-rail" aria-label="Workspace outline">
    <div className="rail-header"><span className="rail-index">01</span><span className="rail-title">SYSTEM MAP</span></div>
    <div className="rail-track">
      {[
        ["workspace", "Analysis workspace", "01"],
        ["memory", "Historical memory", "02"],
        ["provenance", "Audit provenance", "03"],
      ].map(([id, label, number]) => <button key={id} className={cn("rail-node", active === id && "rail-node--active")} onClick={() => onNavigate(id)}><span className="rail-node__number">{number}</span><span>{label}</span></button>)}
    </div>
    <div className="rail-footnote"><span className="rail-footnote__line" /><span>REAL DATA ONLY</span></div>
  </aside>;
}

function Intake({ onNotice, onAnalysis }: { onNotice: (notice: Notice) => void; onAnalysis: (state: BackendState, analysis?: IncidentAnalysis | null) => void }) {
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [incidentType, setIncidentType] = useState("");
  const [focused, setFocused] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const requestVersion = useRef(0);
  const canSubmit = description.trim().length >= 5;
  const submit = async () => {
    if (!canSubmit) {
      onNotice({ type: "error", message: "Describe the incident in at least five characters before requesting analysis." });
      return;
    }
    const requestId = ++requestVersion.current;
    setSubmitting(true);
    onAnalysis({ status: "loading" });
    try {
      const analysis = await memoraApi.analyzeIncident({ raw_text: description.trim(), location: location.trim() || undefined, incident_type: incidentType.trim() || undefined });
      if (requestId !== requestVersion.current) return;
      onAnalysis({ status: "success" }, analysis);
      onNotice({ type: "info", message: analysis.decision_changed ? "Memory changed the decision. Review the retrieved evidence and provenance below." : "Incident analyzed by the Memora backend." });
    } catch (error) {
      if (requestId !== requestVersion.current) return;
      const message = apiMessage(error);
      onAnalysis({ status: message.includes("unreachable") ? "unavailable" : "error", message });
      onNotice({ type: "error", message });
    } finally {
      setSubmitting(false);
    }
  };
  return <section className="panel intake-panel" id="intake">
    <div className="panel-corner panel-corner--tl" /><div className="panel-corner panel-corner--br" />
    <SectionKicker label="01 / CURRENT INPUT"><span className="section-kicker__state"><span className="live-dot" />READY FOR INPUT</span></SectionKicker>
    <div className="intake-grid">
      <div className="intake-copy"><h1>What happened?</h1><p>Describe the operational event in plain language. Memora will compare the current signal with historical memory before a decision is returned.</p><div className="intake-rule" /><div className="intake-meta"><span><LockKeyhole size={13} /> Evidence-bound workflow</span><span><ShieldCheck size={13} /> No local simulation</span></div></div>
      <div className={cn("intake-form", focused && "intake-form--focused")}>
        <div className="field field--primary"><Label htmlFor="incident-description">Incident description <span>*</span></Label><Textarea id="incident-description" placeholder="Describe the incident you need to analyze…" value={description} onChange={(event) => setDescription(event.target.value)} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)} /><div className="field-hint">Natural language accepted · no schema knowledge required</div></div>
        <div className="intake-form__row"><div className="field"><Label htmlFor="incident-location">Location <span className="optional">OPTIONAL</span></Label><Input id="incident-location" placeholder="e.g. Gate 3" value={location} onChange={(event) => setLocation(event.target.value)} /></div><div className="field"><Label htmlFor="incident-type">Incident type <span className="optional">OPTIONAL</span></Label><Input id="incident-type" placeholder="e.g. suspicious_vehicle" value={incidentType} onChange={(event) => setIncidentType(event.target.value)} /></div></div>
        <div className="form-actions"><span className="form-contract"><span className="contract-dot" />POST /api/incidents/analyze <span className="contract-muted">· backend authoritative</span></span><Button onClick={submit} className="analyze-button" disabled={submitting}>{submitting ? <Clock3 size={15} className="animate-spin" /> : <Sparkles size={15} />}{submitting ? "Analyzing…" : "Analyze incident"}<ArrowRight size={15} /></Button></div>
      </div>
    </div>
  </section>;
}

export function AnalysisOutput({ analysis, state }: { analysis: IncidentAnalysis | null; state: BackendState }) {
  if (state.status === "loading") return <EmptyPanel icon={Clock3} eyebrow="ANALYSIS IN PROGRESS" title={getAnalysisStateCopy(state)} description="The current incident is being analyzed by the authoritative decision engine and Sibyl Memory." />;
  if (state.status === "unavailable" || state.status === "error") return <EmptyPanel icon={AlertCircle} eyebrow={state.status === "unavailable" ? "MEMORA BACKEND UNAVAILABLE" : "ANALYSIS ERROR"} title="Unable to analyze incident" description={getAnalysisStateCopy(state)} />;
  if (!analysis) return <EmptyPanel icon={ClipboardCheck} eyebrow="CURRENT INCIDENT" title="No incident analyzed yet" description="Submit an incident above to populate the operational record, timestamp, and incident identifier from the backend." />;
  return (
    <div className="analysis-result">
      <div className="result-meta">
        <span>{analysis.incident?.incident_id || "Incident ID not provided by backend"}</span>
        <span>{analysis.incident?.timestamp ? new Date(analysis.incident.timestamp).toLocaleString() : "Timestamp not provided by backend"}</span>
      </div>
      <h3>{analysis.incident?.summary || "Incident summary not provided by backend"}</h3>
      {(analysis.incident?.approximate_time || analysis.incident?.duration || analysis.incident?.reported_by) && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", margin: "6px 0 12px", color: "#8eaee1", fontSize: "11px", fontFamily: "IBM Plex Mono, monospace" }}>
          {analysis.incident?.approximate_time && <span>TIME: {analysis.incident.approximate_time}</span>}
          {analysis.incident?.duration && <span>DURATION: {analysis.incident.duration}</span>}
          {analysis.incident?.reported_by && <span>REPORTER: {analysis.incident.reported_by}</span>}
        </div>
      )}
      {((analysis.unknowns && analysis.unknowns.length > 0) || (analysis.incident?.unknowns && analysis.incident.unknowns.length > 0)) && (
        <div style={{ margin: "10px 0 14px" }}>
          <span className="micro-label" style={{ display: "block", marginBottom: "6px" }}>OPERATIONAL UNKNOWNS IDENTIFIED</span>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
            {(analysis.unknowns || analysis.incident?.unknowns || []).map((u, i) => (
              <span key={i} className="unknown-chip">
                <HelpCircle size={11} />
                {u}
              </span>
            ))}
          </div>
        </div>
      )}
      <div className="result-grid">
        <div>
          <span className="micro-label">BASELINE</span>
          <strong>{analysis.baseline?.risk || "Not provided"}</strong>
          <span>{analysis.baseline?.recommendation || "Not provided"}</span>
        </div>
        <div>
          <span className="micro-label">MEMORA DECISION</span>
          <strong>{analysis.decision?.risk || "Not provided"}</strong>
          <span>{analysis.decision?.recommendation || "Not provided"}</span>
        </div>
      </div>
      {analysis.decision_changed && (
        <div className="decision-change-banner">
          <strong>MEMORY CHANGED THIS DECISION</strong>
          <span>{analysis.why_decision_changed || analysis.decision?.escalation_reason || "Reason not provided by backend"}</span>
        </div>
      )}
      <div className="evidence-stack">
        {(analysis.memory?.records || []).map((record) => (
          <div className="evidence-row" key={record.id || `${record.category}-${record.timestamp}`}>
            <span className="evidence-tag evidence-tag--memory">{record.category || "MEMORY"}</span>
            <span>{record.summary || "Memory summary not provided by backend"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DecisionSection({ analysis, state }: { analysis: IncidentAnalysis | null; state: BackendState }) {
  const [showWhy, setShowWhy] = useState(true);

  if (state.status === "loading") {
    return (
      <EmptyPanel
        icon={Clock3}
        eyebrow="EVALUATING"
        title="Comparing against Sibyl Memory"
        description="Querying historical operational incidents and evaluating decision shift..."
      />
    );
  }

  if (!analysis) {
    return (
      <div className="decision-empty">
        <div className="decision-empty__glyph"><TriangleAlert size={24} strokeWidth={1.25} /></div>
        <p className="micro-label">MEMORA DECISION</p>
        <h3>Awaiting analysis</h3>
        <p>Baseline, memory-informed risk, and recommendation will appear here only after a successful backend response.</p>
        <button className="text-action" onClick={() => setShowWhy((value) => !value)}>
          Why did Memora change this decision? <ChevronDown size={14} className={cn(showWhy && "rotate-180")} />
        </button>
        {showWhy && (
          <div className="why-panel">
            <div><span>BASELINE</span><strong>Unavailable</strong></div>
            <div><span>HISTORICAL EVIDENCE</span><strong>Unavailable</strong></div>
            <div><span>MEMORA</span><strong>Unavailable</strong></div>
            <div><span>REASON</span><strong>Will use backend response only</strong></div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{ padding: "20px" }}>
      {analysis.decision_changed ? (
        <div className="hero-transformation">
          <div className="hero-banner">
            <span className="hero-banner__title">MEMORY CHANGED THIS DECISION</span>
            <span className="hero-banner__subtitle">
              Prior unresolved incident history retrieved from Sibyl Memory escalated this recommendation.
            </span>
          </div>
          <div className="transformation-flow">
            <div className="flow-card flow-card--baseline">
              <span className="micro-label">01 BASELINE (STATELESS)</span>
              <div className="flow-card__risk">{analysis.baseline?.risk || "UNKNOWN"}</div>
              <div className="flow-card__rec">{analysis.baseline?.recommendation || "NONE"}</div>
            </div>
            <div className="flow-arrow">
              <ArrowRight size={18} />
              <span>SIBYL MEMORY ({analysis.memory?.count ?? 0} retrieved)</span>
            </div>
            <div className="flow-card flow-card--transformed">
              <span className="micro-label">02 MEMORA (MEMORY-INFORMED)</span>
              <div className="flow-card__risk">{analysis.decision?.risk || "UNKNOWN"}</div>
              <div className="flow-card__rec">{analysis.decision?.recommendation || "NONE"}</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="result-grid">
          <div>
            <span className="micro-label">BASELINE RISK</span>
            <strong>{analysis.baseline?.risk || "UNKNOWN"}</strong>
            <span>{analysis.baseline?.recommendation}</span>
          </div>
          <div>
            <span className="micro-label">FINAL DECISION</span>
            <strong style={{ color: "#79edbe" }}>{analysis.decision?.risk || "UNKNOWN"}</strong>
            <span>{analysis.decision?.recommendation}</span>
          </div>
        </div>
      )}

      <button className="text-action" onClick={() => setShowWhy((value) => !value)}>
        Why did Memora decide this? <ChevronDown size={14} className={cn(showWhy && "rotate-180")} />
      </button>

      {showWhy && (
        <div className="why-panel" style={{ marginTop: "12px" }}>
          <div>
            <span>CURRENT INCIDENT</span>
            <strong>{analysis.incident?.summary || "Direct input"}</strong>
          </div>
          <div>
            <span>SIBYL RETRIEVAL</span>
            <strong>{analysis.memory?.found ? `${analysis.memory.count} matching historical records` : "No prior memory"}</strong>
          </div>
          <div>
            <span>PATTERN INFERRED</span>
            <strong>{analysis.inference?.summary || "Deterministic baseline evaluation"}</strong>
          </div>
          <div>
            <span>REASON / SHIFT</span>
            <strong>{analysis.why_decision_changed || analysis.decision?.escalation_reason || "Aligned with baseline"}</strong>
          </div>
        </div>
      )}

      {analysis.failed_mitigations && analysis.failed_mitigations.length > 0 && (
        <div style={{ marginTop: "16px" }}>
          <span className="micro-label" style={{ color: "#ffb86c", display: "block", marginBottom: "8px" }}>
            FAILED MITIGATION DIAGNOSIS ({analysis.failed_mitigations.length})
          </span>
          {analysis.failed_mitigations.map((fm, idx) => (
            <div key={idx} className="intelligence-card">
              <div className="intelligence-card__header">
                <strong>Prior Action Attempted: {fm.prior_action}</strong>
                <span className="evidence-tag evidence-tag--warn">FAILED MITIGATION</span>
              </div>
              <div className="intelligence-card__diag">
                <div><strong>Observed Result:</strong> {fm.observed_result}</div>
                <div><strong>Diagnosis:</strong> {fm.failure_diagnosis}</div>
              </div>
              <div className="intelligence-card__impl">
                <span>OPERATIONAL IMPLICATION</span>
                {fm.current_implication}
              </div>
            </div>
          ))}
        </div>
      )}

      {analysis.actionable_lessons && analysis.actionable_lessons.length > 0 && (
        <div style={{ marginTop: "16px" }}>
          <span className="micro-label" style={{ color: "#79edbe", display: "block", marginBottom: "8px" }}>
            ACTIONABLE OPERATIONAL LESSONS ({analysis.actionable_lessons.length})
          </span>
          {analysis.actionable_lessons.map((lesson, idx) => (
            <div key={idx} className="intelligence-card intelligence-card--lesson">
              <div className="intelligence-card__header">
                <strong>Directive: {lesson.historical_rule}</strong>
                <span className="evidence-tag evidence-tag--ok">{lesson.lesson_id}</span>
              </div>
              <div className="intelligence-card__diag" style={{ color: "#b5ccf2" }}>
                <strong>Operational Context:</strong> {lesson.current_implication}
              </div>
              <div className="intelligence-card__impl" style={{ borderLeftColor: "#79edbe", background: "rgba(121, 237, 190, 0.1)" }}>
                <span style={{ color: "#79edbe" }}>ADJUSTMENT REQUIRED</span>
                {lesson.recommended_adjustment}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function OutcomeSection({
  live,
  onNotice,
  onOutcome,
}: {
  live: LiveWorkspace;
  onNotice: (notice: Notice) => void;
  onOutcome: (state: BackendState, outcome?: OutcomeResponse | null) => void;
}) {
  const [actionTaken, setActionTaken] = useState("");
  const [observedResult, setObservedResult] = useState("");
  const [isResolved, setIsResolved] = useState(false);
  const [unresolvedReason, setUnresolvedReason] = useState("");
  const [operationalLesson, setOperationalLesson] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const incidentId = live.analysis?.incident?.incident_id;

  const submitOutcome = async () => {
    if (!incidentId) {
      onNotice({ type: "error", message: "Cannot record outcome without an analyzed incident." });
      return;
    }
    if (actionTaken.trim().length < 3 || observedResult.trim().length < 3) {
      onNotice({ type: "error", message: "Action taken and observed result must each be at least 3 characters." });
      return;
    }

    setSubmitting(true);
    onOutcome({ status: "loading" });
    try {
      const response = await memoraApi.recordOutcome({
        incident_id: incidentId,
        action_taken: actionTaken.trim(),
        observed_result: observedResult.trim(),
        is_resolved: isResolved,
        unresolved_reason: !isResolved && unresolvedReason.trim() ? unresolvedReason.trim() : undefined,
        operational_lesson: operationalLesson.trim() || undefined,
      });
      onOutcome({ status: "success" }, response);
      onNotice({
        type: "info",
        message: `Outcome recorded for ${incidentId}. Operational learning stored in Sibyl Memory.`,
      });
    } catch (error) {
      const message = apiMessage(error);
      onOutcome({ status: "error", message });
      onNotice({ type: "error", message });
    } finally {
      setSubmitting(false);
    }
  };

  if (!live.analysis) {
    return (
      <div className="outcome-layout">
        <div>
          <h3>Record what happened next</h3>
          <p>
            Outcome recording becomes available after an incident and decision exist. The returned outcome will update future operational context.
          </p>
        </div>
        <div className="outcome-fields">
          <div className="outcome-field"><span>Action taken</span><span className="field-unavailable">Unavailable</span></div>
          <div className="outcome-field"><span>Observed result</span><span className="field-unavailable">Unavailable</span></div>
          <div className="outcome-field"><span>Resolution state</span><span className="field-unavailable">Unavailable</span></div>
        </div>
      </div>
    );
  }

  if (live.outcome) {
    return (
      <div className="outcome-success">
        <div className="outcome-success__header">
          <div>
            <span className="micro-label">SIBYL OPERATIONAL LEARNING</span>
            <h3 style={{ color: "#79edbe", margin: "4px 0 0" }}>Outcome recorded & memory updated</h3>
          </div>
          <StatusChip label={live.outcome.is_resolved ? "RESOLVED" : "UNRESOLVED"} tone={live.outcome.is_resolved ? "ok" : "warn"} />
        </div>
        <p style={{ color: "#b5ccf2", fontSize: "12px", margin: 0 }}>{live.outcome.message}</p>
        <div className="outcome-success__grid">
          <div className="outcome-success__box">
            <span>OUTCOME ID</span>
            <strong>{live.outcome.outcome_id}</strong>
          </div>
          <div className="outcome-success__box">
            <span>INCIDENT REF</span>
            <strong>{live.outcome.incident_id}</strong>
          </div>
          <div className="outcome-success__box">
            <span>RECURRENCE COUNT</span>
            <strong>{live.outcome.recurrence_count ?? "0"}</strong>
          </div>
          <div className="outcome-success__box">
            <span>ACTION TAKEN</span>
            <strong>{live.outcome.action_taken}</strong>
          </div>
          <div className="outcome-success__box">
            <span>OBSERVED RESULT</span>
            <strong>{live.outcome.observed_result}</strong>
          </div>
          <div className="outcome-success__box">
            <span>ORGANIZATIONAL LESSON</span>
            <strong>{live.outcome.lesson_rule || live.outcome.lesson_id || "None recorded"}</strong>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="outcome-form">
      <div style={{ color: "#8eaee1", fontSize: "11px", fontFamily: "IBM Plex Mono, monospace" }}>
        ACTIVE INCIDENT: <strong style={{ color: "#ffffff" }}>{incidentId}</strong>
      </div>
      <div className="outcome-form__grid">
        <div className="field">
          <Label htmlFor="outcome-action">Action taken <span>*</span></Label>
          <Input
            id="outcome-action"
            placeholder="e.g. Monitored delivery vehicle at Gate 3"
            value={actionTaken}
            onChange={(e) => setActionTaken(e.target.value)}
          />
        </div>
        <div className="field">
          <Label htmlFor="outcome-result">Observed result <span>*</span></Label>
          <Input
            id="outcome-result"
            placeholder="e.g. Vehicle departed before verification"
            value={observedResult}
            onChange={(e) => setObservedResult(e.target.value)}
          />
        </div>
      </div>
      <div className="outcome-form__grid">
        <div className="field">
          <Label>Resolution state <span>*</span></Label>
          <div className="resolution-toggle">
            <button
              type="button"
              className={cn("toggle-btn", isResolved && "toggle-btn--active-ok")}
              onClick={() => setIsResolved(true)}
            >
              Resolved
            </button>
            <button
              type="button"
              className={cn("toggle-btn", !isResolved && "toggle-btn--active-warn")}
              onClick={() => setIsResolved(false)}
            >
              Unresolved
            </button>
          </div>
        </div>
        <div className="field">
          <Label htmlFor="outcome-lesson">Operational lesson <span className="optional">OPTIONAL</span></Label>
          <Input
            id="outcome-lesson"
            placeholder="e.g. Fast recurrence requires supervisor escalation"
            value={operationalLesson}
            onChange={(e) => setOperationalLesson(e.target.value)}
          />
        </div>
      </div>
      {!isResolved && (
        <div className="field">
          <Label htmlFor="outcome-unresolved-reason">Reason unresolved <span className="optional">OPTIONAL</span></Label>
          <Input
            id="outcome-unresolved-reason"
            placeholder="e.g. Subject fled before identity verified"
            value={unresolvedReason}
            onChange={(e) => setUnresolvedReason(e.target.value)}
          />
        </div>
      )}
      <div className="form-actions">
        <span className="form-contract">
          <span className="contract-dot" />POST /api/outcomes <span className="contract-muted">· updates Sibyl Memory</span>
        </span>
        <Button onClick={submitOutcome} className="analyze-button" disabled={submitting}>
          {submitting ? <Clock3 size={15} className="animate-spin" /> : <Check size={15} />}
          {submitting ? "Recording…" : "Record outcome & update learning"}
        </Button>
      </div>
    </div>
  );
}

function Workspace({
  onNotice,
  onNavigate,
  live,
  onAnalysis,
  onOutcome,
}: {
  onNotice: (notice: Notice) => void;
  onNavigate: (id: string) => void;
  live: LiveWorkspace;
  onAnalysis: (state: BackendState, analysis?: IncidentAnalysis | null) => void;
  onOutcome: (state: BackendState, outcome?: OutcomeResponse | null) => void;
}) {
  return (
    <>
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">OPERATIONAL INTELLIGENCE / LIVE WORKSPACE</p>
          <h2>Incident analysis</h2>
          <p className="heading-copy">A decision workspace for connecting current events to what operations has already learned.</p>
        </div>
        <button className="outline-action" onClick={() => document.getElementById("intake")?.scrollIntoView({ behavior: "smooth" })}>
          <Plus size={15} />New incident
        </button>
      </div>
      <Intake onNotice={onNotice} onAnalysis={onAnalysis} />
      <div className="section-row-label">
        <span>ANALYSIS OUTPUT</span>
        <span className="section-row-label__line" />
        <span className="section-row-label__note">
          {live.analysisState.status === "success" ? "LIVE BACKEND RESPONSE" : "AWAITING BACKEND RESPONSE"}
        </span>
      </div>
      <div className="analysis-grid">
        <section className="panel current-panel">
          <SectionKicker label="02 / INCIDENT">
            <span className="record-status">
              {live.analysisState.status === "success" ? "BACKEND RESPONSE" : live.analysisState.status === "loading" ? "ANALYZING" : "NO ACTIVE RECORD"}
            </span>
          </SectionKicker>
          <AnalysisOutput analysis={live.analysis} state={live.analysisState} />
        </section>
        <section className="panel decision-panel">
          <SectionKicker label="03 / DECISION">
            <span className="record-status">
              {live.analysis?.decision_changed ? "MEMORY CHANGED DECISION" : live.analysis ? "DECISION APPLIED" : "NO DECISION"}
            </span>
          </SectionKicker>
          <DecisionSection analysis={live.analysis} state={live.analysisState} />
        </section>
      </div>
      <div className="analysis-grid analysis-grid--lower">
        <section className="panel memory-panel">
          <SectionKicker label="04 / MEMORY">
            <span className="record-status">
              {live.memoryState.status === "success" ? "SIBYL CONNECTED" : live.memoryState.status === "loading" ? "SIBYL CHECKING" : live.memoryState.status === "unavailable" ? "SIBYL UNAVAILABLE" : "SIBYL ERROR"}
            </span>
          </SectionKicker>
          {live.analysis?.memory?.found ? (
            <div className="evidence-stack">
              <div style={{ marginBottom: "8px", color: "#8eaee1", fontSize: "11px", fontFamily: "IBM Plex Mono, monospace" }}>
                RETRIEVED {live.analysis.memory.count} HISTORICAL RECORD(S) FROM SIBYL
              </div>
              {live.analysis.memory.records?.map((record) => (
                <div className="evidence-row" key={record.id || `${record.category}-${record.timestamp}`}>
                  <span className="evidence-tag evidence-tag--memory">{record.category || "MEMORY"}</span>
                  <div>
                    <span style={{ display: "block", color: "#ffffff" }}>{record.summary}</span>
                    <small style={{ color: "#8eaee1" }}>
                      ID: {record.id || "N/A"} · Status: {record.status || "unresolved"} · Location: {record.location || "N/A"}
                    </small>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyPanel
              icon={History}
              eyebrow="OPERATIONAL MEMORY"
              title={live.memoryState.status === "success" ? "Search historical memory" : live.memoryState.status === "unavailable" ? "Historical memory unavailable" : "Historical memory not ready"}
              description={live.memoryState.status === "success" ? "Sibyl Memory is connected. Open the explorer to query real records." : live.memoryState.message || "No relevant operational history can be shown until the memory status endpoint responds."}
              action={<button className="text-action" onClick={() => onNavigate("memory")}>Open memory explorer <ArrowRight size={14} /></button>}
            />
          )}
        </section>
        <section className="panel inference-panel">
          <SectionKicker label="05 / INFERENCE">
            <span className="record-status">{live.analysis ? "INFERENCE COMPLETE" : "NO INFERENCE"}</span>
          </SectionKicker>
          {live.analysis ? (
            <div className="evidence-stack">
              {live.analysis.patterns_detected && live.analysis.patterns_detected.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "10px" }}>
                  {live.analysis.patterns_detected.map((p, idx) => (
                    <div key={idx} className="pattern-badge" title={p.description}>
                      <Activity size={12} />
                      <span>{p.title || p.pattern_type}</span>
                    </div>
                  ))}
                </div>
              )}
              {live.analysis.evidence_chain && live.analysis.evidence_chain.length > 0 ? (
                live.analysis.evidence_chain.map((item, idx) => {
                  let tagClass = "evidence-tag--inference";
                  let label: string = item.type;
                  if (item.type === "CURRENT_FACT") {
                    tagClass = "evidence-tag--fact";
                    label = "CURRENT FACT";
                  } else if (item.type === "HISTORICAL_FACT") {
                    tagClass = "evidence-tag--historical";
                    label = "HISTORICAL FACT";
                  } else if (item.type === "INFERENCE") {
                    tagClass = "evidence-tag--inference";
                    label = "INFERENCE";
                  } else if (item.type === "UNKNOWN") {
                    tagClass = "evidence-tag--unknown";
                    label = "UNKNOWN";
                  } else if (item.type === "RECOMMENDATION") {
                    tagClass = "evidence-tag--decision";
                    label = "RECOMMENDATION";
                  }
                  return (
                    <div className="evidence-row" key={idx}>
                      <span className={cn("evidence-tag", tagClass)}>{label}</span>
                      <div>
                        <span style={{ display: "block", color: "#ffffff" }}>{item.text}</span>
                        <small style={{ color: "#8eaee1", fontSize: "10px", fontFamily: "IBM Plex Mono, monospace" }}>
                          Source: {item.source} · Confidence: {Math.round(item.confidence * 100)}%
                          {item.supporting_record_id ? ` · Ref: ${item.supporting_record_id}` : ""}
                        </small>
                      </div>
                    </div>
                  );
                })
              ) : (
                <>
                  <div className="evidence-row">
                    <span className="evidence-tag evidence-tag--fact">FACT</span>
                    <span>{live.analysis.provenance?.facts || live.analysis.incident?.summary || "Extracted from operator input."}</span>
                  </div>
                  <div className="evidence-row">
                    <span className="evidence-tag evidence-tag--memory">MEMORY</span>
                    <span>{live.analysis.provenance?.retrieval || (live.analysis.memory?.found ? `${live.analysis.memory.count} matching record(s) retrieved from Sibyl.` : "No relevant operational history found.")}</span>
                  </div>
                  <div className="evidence-row">
                    <span className="evidence-tag evidence-tag--inference">INFERENCE</span>
                    <span>{live.analysis.inference?.summary || live.analysis.provenance?.inference || "Deterministic pattern evaluation complete."}</span>
                  </div>
                  {live.analysis.inference?.unresolved_history && (
                    <div className="evidence-row">
                      <span className="evidence-tag evidence-tag--warn">UNRESOLVED</span>
                      <span>Prior related incident history contains unresolved events ({live.analysis.inference.unresolved_incident_ids?.join(", ") || "prior incident"}).</span>
                    </div>
                  )}
                  {Boolean(live.analysis.inference?.recurrence_count) && (
                    <div className="evidence-row">
                      <span className="evidence-tag evidence-tag--warn">RECURRENCE</span>
                      <span>Recurrence count: {live.analysis.inference?.recurrence_count} prior similar occurrence(s).</span>
                    </div>
                  )}
                </>
              )}
            </div>
          ) : (
            <div className="evidence-stack">
              <div className="evidence-row"><span className="evidence-tag evidence-tag--fact">FACT</span><span>Waiting for explicit operator input.</span></div>
              <div className="evidence-row"><span className="evidence-tag evidence-tag--memory">MEMORY</span><span>Waiting for retrieved operational history.</span></div>
              <div className="evidence-row"><span className="evidence-tag evidence-tag--inference">INFERENCE</span><span>Will render backend inference; nothing is inferred locally.</span></div>
            </div>
          )}
        </section>
      </div>
      <section className="panel outcome-panel">
        <SectionKicker label="06 / OUTCOME + LEARNING">
          <span className="record-status">
            {live.outcome ? "LEARNING RECORDED" : live.analysis ? "READY FOR OUTCOME" : "LOCKED UNTIL DECISION"}
          </span>
        </SectionKicker>
        <OutcomeSection live={live} onNotice={onNotice} onOutcome={onOutcome} />
      </section>
      <section className="ai-strip">
        <div className="ai-strip__icon"><BrainCircuit size={18} /></div>
        <div className="ai-strip__content">
          <div className="ai-strip__title"><span>OPTIONAL / EVIDENCE SUMMARY</span><Badge variant="outline">NOT CONNECTED</Badge></div>
          <p>When enabled, this view will summarize only incident evidence returned by the backend. It will never create activity, memory, metrics, or recommendations.</p>
        </div>
        <button className="outline-action outline-action--muted" onClick={() => onNotice({ type: "info", message: "Evidence-only AI summaries will appear here once a typed summary procedure is available." })}>
          <Info size={14} />View guardrails
        </button>
      </section>
    </>
  );
}

function MemoryExplorer({ onNotice }: { onNotice: (notice: Notice) => void }) {
  const [query, setQuery] = useState("");
  const [state, setState] = useState<BackendState>({ status: "idle" });
  const [results, setResults] = useState<MemorySearchResponse | null>(null);
  const requestVersion = useRef(0);
  const search = async () => {
    if (!query.trim()) { onNotice({ type: "error", message: "Enter a search term before querying operational memory." }); return; }
    const requestId = ++requestVersion.current;
    setState({ status: "loading" }); setResults(null);
    try {
      const response = await memoraApi.searchMemory(query.trim());
      if (requestId !== requestVersion.current) return;
      setResults(response);
      setState({ status: response.results.length ? "success" : "empty" });
    } catch (error) {
      if (requestId !== requestVersion.current) return;
      const message = apiMessage(error);
      setState({ status: message.includes("unreachable") ? "unavailable" : "error", message });
      onNotice({ type: "error", message });
    }
  };
  const statusLabel = getMemorySearchStateLabel(state, results?.count ?? results?.results.length);
  return (
    <div className="page-section">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">OPERATIONAL MEMORY / SIBYL</p>
          <h2>Memory explorer</h2>
          <p className="heading-copy">Inspect historical operational records as chronology, not as a generic search feed.</p>
        </div>
        <StatusChip label={state.status === "unavailable" ? "Connection unavailable" : "REST search ready"} tone={state.status === "unavailable" ? "warn" : "ok"} />
      </div>
      <section className="panel explorer-panel">
        <SectionKicker label="01 / SEARCH"><span className="record-status">{statusLabel}</span></SectionKicker>
        <div className="explorer-search">
          <div className="search-field">
            <Search size={16} />
            <Input aria-label="Search operational memory" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search incidents, outcomes, lessons…" />
          </div>
          <Button onClick={search} className="analyze-button" disabled={state.status === "loading"}>
            <Search size={15} />{state.status === "loading" ? "Searching…" : "Search memory"}
          </Button>
        </div>
        {state.status === "success" && results ? (
          <div className="evidence-stack">
            {results.results.map((record) => (
              <div className="evidence-row" key={record.id || `${record.category}-${record.timestamp}`}>
                <span className="evidence-tag evidence-tag--memory">{record.category || record.tier || "MEMORY"}</span>
                <div>
                  <span style={{ display: "block", color: "#ffffff" }}>{record.summary || "Summary not provided by backend"}</span>
                  <small style={{ color: "#8eaee1" }}>{record.id || "ID not provided"} · {record.timestamp ? new Date(record.timestamp).toLocaleString() : "Timestamp not provided"}</small>
                </div>
              </div>
            ))}
          </div>
        ) : state.status === "empty" ? (
          <EmptyPanel icon={FileSearch} eyebrow="EMPTY MEMORY RESULT" title="No relevant historical memory found" description="The backend returned no matching records for this query." />
        ) : state.status === "unavailable" || state.status === "error" ? (
          <EmptyPanel icon={AlertCircle} eyebrow={state.status === "unavailable" ? "SIBYL MEMORY UNAVAILABLE" : "MEMORY SEARCH ERROR"} title="Unable to search operational memory" description={state.message || "The backend did not return a valid search response."} />
        ) : (
          <EmptyPanel icon={FileSearch} eyebrow="READY FOR QUERY" title="Search real operational memory" description="Results, timestamps, IDs, status, and relevance will appear only from Sibyl Memory." />
        )}
      </section>
    </div>
  );
}

function Provenance({ analysis, onNotice }: { analysis: IncidentAnalysis | null; onNotice: (notice: Notice) => void }) {
  const steps = useMemo(() => {
    if (!analysis) {
      return [
        ["01", "What happened", "Operator input", "Unavailable until the backend returns this stage."],
        ["02", "What Memora retrieved", "Sibyl memory", "Unavailable until the backend returns this stage."],
        ["03", "What Memora inferred", "Backend inference", "Unavailable until the backend returns this stage."],
        ["04", "What Memora recommended", "Decision response", "Unavailable until the backend returns this stage."],
      ];
    }
    return [
      [
        "01",
        "What happened",
        "Operator input",
        analysis.provenance?.facts || analysis.incident?.summary || "Operator input received.",
      ],
      [
        "02",
        "What Memora retrieved",
        "Sibyl memory",
        analysis.provenance?.retrieval || (analysis.memory?.found ? `${analysis.memory.count} matching historical record(s) retrieved from Sibyl Memory.` : "No historical records retrieved."),
      ],
      [
        "03",
        "What Memora inferred",
        "Backend inference",
        analysis.provenance?.inference || analysis.inference?.summary || "Deterministic baseline evaluation.",
      ],
      [
        "04",
        "What Memora recommended",
        "Decision response",
        analysis.provenance?.decision_shift || `${analysis.decision?.risk} (${analysis.decision?.recommendation})`,
      ],
    ];
  }, [analysis]);

  return (
    <div className="page-section">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">TRACEABILITY / AUDIT VIEW</p>
          <h2>Provenance</h2>
          <p className="heading-copy">Follow the evidence chain without exposing internal storage or implementation details.</p>
        </div>
        <button
          className="outline-action"
          onClick={() => onNotice({ type: "info", message: analysis ? `Viewing provenance for ${analysis.incident?.incident_id}` : "Provenance details will populate after a real incident-analysis response." })}
        >
          <PanelRight size={15} />{analysis ? "Active trace" : "Inspect response"}
        </button>
      </div>
      <section className="panel provenance-panel">
        <SectionKicker label="01 / EVIDENCE CHAIN">
          <span className="record-status">{analysis ? "TRACE ACTIVE" : "NO ACTIVE TRACE"}</span>
        </SectionKicker>
        <div className="provenance-chain">
          {steps.map(([number, title, detail, description], index) => (
            <div className="provenance-step" key={number}>
              <div className="provenance-step__top">
                <span className="provenance-step__number">{number}</span>
                {index < steps.length - 1 && <span className="provenance-step__connector" />}
              </div>
              <div className="provenance-step__body">
                <p className="micro-label">{detail}</p>
                <h3>{title}</h3>
                <p>{description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
      {analysis && (
        <div className="provenance-note" style={{ marginTop: "16px" }}>
          <AlertCircle size={17} />
          <div>
            <strong>Backend Identifiers & Audit Metadata</strong>
            <span>
              Incident ID: {analysis.incident?.incident_id || "Not provided"} · Timestamp: {analysis.incident?.timestamp || "Not provided"} · Session: {analysis.session?.id || "Direct"} · Fresh: {analysis.session?.is_fresh ? "True" : "False"}
            </span>
          </div>
        </div>
      )}
      {!analysis && (
        <div className="provenance-note">
          <AlertCircle size={17} />
          <div>
            <strong>Technical metadata stays progressive.</strong>
            <span>Only backend-provided provenance, decision change, inference, and response identifiers will be exposed here.</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Home() {
  const [active, setActive] = useState("workspace");
  const [notice, setNotice] = useState<Notice>(null);
  const [live, setLive] = useState<LiveWorkspace>(initialLiveWorkspace);
  const { data: authUser } = trpc.auth.me.useQuery();

  useEffect(() => {
    let cancelled = false;
    memoraApi.memoryStatus().then((status) => {
      if (!cancelled) setLive((current) => ({ ...current, memoryStatus: status, memoryState: { status: status.status === "connected" ? "success" : "error", message: status.status } }));
    }).catch((error) => {
      if (!cancelled) setLive((current) => ({ ...current, memoryState: { status: error instanceof MemoraApiError && error.code === "NETWORK_ERROR" ? "unavailable" : "error", message: apiMessage(error) } }));
    });
    return () => { cancelled = true; };
  }, []);

  const onAnalysis = (state: BackendState, analysis: IncidentAnalysis | null = null) =>
    setLive((current) => ({
      ...current,
      analysisState: state,
      analysis: analysis ?? (state.status === "loading" ? null : current.analysis),
      outcome: state.status === "loading" ? null : current.outcome,
      outcomeState: state.status === "loading" ? { status: "idle" } : current.outcomeState,
    }));

  const onOutcome = (state: BackendState, outcome: OutcomeResponse | null = null) =>
    setLive((current) => ({
      ...current,
      outcomeState: state,
      outcome: outcome ?? current.outcome,
    }));

  const navigate = (id: string) => { setActive(id); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const dismiss = () => setNotice(null);

  return (
    <div className="memora-shell">
      <Header
        active={active}
        onNavigate={navigate}
        memoryState={live.memoryState}
        onNewIncident={() => {
          navigate("workspace");
          setTimeout(() => document.getElementById("intake")?.scrollIntoView({ behavior: "smooth" }), 50);
        }}
      />
      <div className="shell-body">
        <BlueprintRail active={active} onNavigate={navigate} />
        <main className="main-canvas">
          <div className="canvas-grid" />
          <div className="canvas-content">
            <div className="context-bar">
              <span><span className="context-pip" />OPERATIONS / {authUser ? "AUTHENTICATED SESSION" : "READINESS VIEW"}</span>
              <span className="context-bar__right"><Clock3 size={13} />UTC display · real backend responses only</span>
            </div>
            {active === "workspace" && (
              <Workspace
                onNotice={setNotice}
                onNavigate={navigate}
                live={live}
                onAnalysis={onAnalysis}
                onOutcome={onOutcome}
              />
            )}
            {active === "memory" && <MemoryExplorer onNotice={setNotice} />}
            {active === "provenance" && <Provenance analysis={live.analysis} onNotice={setNotice} />}
            <footer className="canvas-footer">
              <span>MEMORA / PHASE 2.5</span>
              <span>DECISION TRACEABILITY OVER DECISION THEATRE</span>
              <span>v0.2 / SIBYL LOAD-BEARING PROOF</span>
            </footer>
          </div>
        </main>
      </div>
      {notice && (
        <div className={cn("notice", notice.type === "error" && "notice--error")} role="status">
          <div className="notice__icon">{notice.type === "error" ? <X size={16} /> : <Info size={16} />}</div>
          <span>{notice.message}</span>
          <button onClick={dismiss} aria-label="Dismiss notice"><X size={14} /></button>
        </div>
      )}
    </div>
  );
}

export { StatusChip };
