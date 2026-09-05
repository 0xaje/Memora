import React, { useEffect, useMemo, useRef, useState } from "react";
import { trpc } from "@/lib/trpc";
import { memoraApi, MemoraApiError, type IncidentAnalysis, type MemorySearchResponse, type MemoryStatusResponse, type OutcomeResponse } from "@/lib/memora-api";
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
  History,
  Info,
  LockKeyhole,
  Menu,
  Network,
  PanelRight,
  Plus,
  Search,
  ShieldCheck,
  SlidersHorizontal,
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
        <div className="intake-form__row"><div className="field"><Label htmlFor="incident-location">Location <span className="optional">OPTIONAL</span></Label><Input id="incident-location" placeholder="e.g. North perimeter" value={location} onChange={(event) => setLocation(event.target.value)} /></div><div className="field"><Label htmlFor="incident-type">Incident type <span className="optional">OPTIONAL</span></Label><Input id="incident-type" placeholder="e.g. Access anomaly" value={incidentType} onChange={(event) => setIncidentType(event.target.value)} /></div></div>
        <div className="form-actions"><span className="form-contract"><span className="contract-dot" />POST /api/incidents/analyze <span className="contract-muted">· backend authoritative</span></span><Button onClick={submit} className="analyze-button" disabled={submitting}>{submitting ? <Clock3 size={15} className="animate-spin" /> : <Sparkles size={15} />}{submitting ? "Analyzing…" : "Analyze incident"}<ArrowRight size={15} /></Button></div>
      </div>
    </div>
  </section>;
}

export function AnalysisOutput({ analysis, state }: { analysis: IncidentAnalysis | null; state: BackendState }) {
  if (state.status === "loading") return <EmptyPanel icon={Clock3} eyebrow="ANALYSIS IN PROGRESS" title={getAnalysisStateCopy(state)} description="The current incident is being analyzed by the authoritative decision engine and Sibyl Memory." />;
  if (state.status === "unavailable" || state.status === "error") return <EmptyPanel icon={AlertCircle} eyebrow={state.status === "unavailable" ? "MEMORA BACKEND UNAVAILABLE" : "ANALYSIS ERROR"} title="Unable to analyze incident" description={getAnalysisStateCopy(state)} />;
  if (!analysis) return <EmptyPanel icon={ClipboardCheck} eyebrow="CURRENT INCIDENT" title="No incident analyzed yet" description="Submit an incident above to populate the operational record, timestamp, and incident identifier from the backend." />;
  return <div className="analysis-result"><div className="result-meta"><span>{analysis.incident?.incident_id || "Incident ID not provided by backend"}</span><span>{analysis.incident?.timestamp ? new Date(analysis.incident.timestamp).toLocaleString() : "Timestamp not provided by backend"}</span></div><h3>{analysis.incident?.summary || "Incident summary not provided by backend"}</h3><div className="result-grid"><div><span className="micro-label">BASELINE</span><strong>{analysis.baseline?.risk || "Not provided"}</strong><span>{analysis.baseline?.recommendation || "Not provided"}</span></div><div><span className="micro-label">MEMORA DECISION</span><strong>{analysis.decision?.risk || "Not provided"}</strong><span>{analysis.decision?.recommendation || "Not provided"}</span></div></div>{analysis.decision_changed && <div className="decision-change-banner"><strong>MEMORY CHANGED THIS DECISION</strong><span>{analysis.why_decision_changed || analysis.decision?.escalation_reason || "Reason not provided by backend"}</span></div>}<div className="evidence-stack">{(analysis.memory?.records || []).map((record) => <div className="evidence-row" key={record.id || `${record.category}-${record.timestamp}`}><span className="evidence-tag evidence-tag--memory">{record.category || "MEMORY"}</span><span>{record.summary || "Memory summary not provided by backend"}</span></div>)}</div></div>;
}

function Workspace({ onNotice, onNavigate, live, onAnalysis }: { onNotice: (notice: Notice) => void; onNavigate: (id: string) => void; live: LiveWorkspace; onAnalysis: (state: BackendState, analysis?: IncidentAnalysis | null) => void }) {
  const [showWhy, setShowWhy] = useState(false);
  return <>
    <div className="workspace-heading"><div><p className="eyebrow">OPERATIONAL INTELLIGENCE / LIVE WORKSPACE</p><h2>Incident analysis</h2><p className="heading-copy">A decision workspace for connecting current events to what operations has already learned.</p></div><button className="outline-action" onClick={() => document.getElementById("intake")?.scrollIntoView({ behavior: "smooth" })}><Plus size={15} />New incident</button></div>
    <Intake onNotice={onNotice} onAnalysis={onAnalysis} />
    <div className="section-row-label"><span>ANALYSIS OUTPUT</span><span className="section-row-label__line" /><span className="section-row-label__note">AWAITING BACKEND RESPONSE</span></div>
    <div className="analysis-grid">
      <section className="panel current-panel"><SectionKicker label="02 / INCIDENT"><span className="record-status">{live.analysisState.status === "success" ? "BACKEND RESPONSE" : live.analysisState.status === "loading" ? "ANALYZING" : "NO ACTIVE RECORD"}</span></SectionKicker><AnalysisOutput analysis={live.analysis} state={live.analysisState} /></section>
      <section className="panel decision-panel"><SectionKicker label="03 / DECISION"><span className="record-status">NO DECISION</span></SectionKicker><div className="decision-empty"><div className="decision-empty__glyph"><TriangleAlert size={24} strokeWidth={1.25} /></div><p className="micro-label">MEMORA DECISION</p><h3>Awaiting analysis</h3><p>Baseline, memory-informed risk, and recommendation will appear here only after a successful backend response.</p><button className="text-action" onClick={() => setShowWhy((value) => !value)}>Why did Memora change this decision? <ChevronDown size={14} className={cn(showWhy && "rotate-180")} /></button>{showWhy && <div className="why-panel"><div><span>BASELINE</span><strong>Unavailable</strong></div><div><span>HISTORICAL EVIDENCE</span><strong>Unavailable</strong></div><div><span>MEMORA</span><strong>Unavailable</strong></div><div><span>REASON</span><strong>Will use backend response only</strong></div></div>}</div></section>
    </div>
    <div className="analysis-grid analysis-grid--lower">
      <section className="panel memory-panel"><SectionKicker label="04 / MEMORY"><span className="record-status">{live.memoryState.status === "success" ? "SIBYL CONNECTED" : live.memoryState.status === "loading" ? "SIBYL CHECKING" : live.memoryState.status === "unavailable" ? "SIBYL UNAVAILABLE" : "SIBYL ERROR"}</span></SectionKicker><EmptyPanel icon={History} eyebrow="OPERATIONAL MEMORY" title={live.memoryState.status === "success" ? "Search historical memory" : live.memoryState.status === "unavailable" ? "Historical memory unavailable" : "Historical memory not ready"} description={live.memoryState.status === "success" ? "Sibyl Memory is connected. Open the explorer to query real records." : live.memoryState.message || "No relevant operational history can be shown until the memory status endpoint responds."} action={<button className="text-action" onClick={() => onNavigate("memory")}>Open memory explorer <ArrowRight size={14} /></button>} /></section>
      <section className="panel inference-panel"><SectionKicker label="05 / INFERENCE"><span className="record-status">NO INFERENCE</span></SectionKicker><div className="evidence-stack"><div className="evidence-row"><span className="evidence-tag evidence-tag--fact">FACT</span><span>Waiting for explicit operator input.</span></div><div className="evidence-row"><span className="evidence-tag evidence-tag--memory">MEMORY</span><span>Waiting for retrieved operational history.</span></div><div className="evidence-row"><span className="evidence-tag evidence-tag--inference">INFERENCE</span><span>Will render backend inference; nothing is inferred locally.</span></div></div></section>
    </div>
    <section className="panel outcome-panel"><SectionKicker label="06 / OUTCOME + LEARNING"><span className="record-status">LOCKED UNTIL DECISION</span></SectionKicker><div className="outcome-layout"><div><h3>Record what happened next</h3><p>Outcome recording becomes available after an incident and decision exist. The returned outcome will update future operational context.</p></div><div className="outcome-fields"><div className="outcome-field"><span>Action taken</span><span className="field-unavailable">Unavailable</span></div><div className="outcome-field"><span>Observed result</span><span className="field-unavailable">Unavailable</span></div><div className="outcome-field"><span>Resolution state</span><span className="field-unavailable">Unavailable</span></div></div></div></section>
    <section className="ai-strip"><div className="ai-strip__icon"><BrainCircuit size={18} /></div><div className="ai-strip__content"><div className="ai-strip__title"><span>OPTIONAL / EVIDENCE SUMMARY</span><Badge variant="outline">NOT CONNECTED</Badge></div><p>When enabled, this view will summarize only incident evidence returned by the backend. It will never create activity, memory, metrics, or recommendations.</p></div><button className="outline-action outline-action--muted" onClick={() => onNotice({ type: "info", message: "Evidence-only AI summaries will appear here once a typed summary procedure is available." })}><Info size={14} />View guardrails</button></section>
  </>;
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
    try { const response = await memoraApi.searchMemory(query.trim()); if (requestId !== requestVersion.current) return; setResults(response); setState({ status: response.results.length ? "success" : "empty" }); }
    catch (error) { if (requestId !== requestVersion.current) return; const message = apiMessage(error); setState({ status: message.includes("unreachable") ? "unavailable" : "error", message }); onNotice({ type: "error", message }); }
  };
  const statusLabel = getMemorySearchStateLabel(state, results?.count ?? results?.results.length);
  return <div className="page-section"><div className="workspace-heading"><div><p className="eyebrow">OPERATIONAL MEMORY / SIBYL</p><h2>Memory explorer</h2><p className="heading-copy">Inspect historical operational records as chronology, not as a generic search feed.</p></div><StatusChip label={state.status === "unavailable" ? "Connection unavailable" : "REST search ready"} tone={state.status === "unavailable" ? "warn" : "ok"} /></div><section className="panel explorer-panel"><SectionKicker label="01 / SEARCH"><span className="record-status">{statusLabel}</span></SectionKicker><div className="explorer-search"><div className="search-field"><Search size={16} /><Input aria-label="Search operational memory" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search incidents, outcomes, lessons…" /></div><Button onClick={search} className="analyze-button" disabled={state.status === "loading"}><Search size={15} />{state.status === "loading" ? "Searching…" : "Search memory"}</Button></div>{state.status === "success" && results ? <div className="evidence-stack">{results.results.map((record) => <div className="evidence-row" key={record.id || `${record.category}-${record.timestamp}`}><span className="evidence-tag evidence-tag--memory">{record.category || record.tier || "MEMORY"}</span><span>{record.summary || "Summary not provided by backend"}</span><small>{record.id || "ID not provided"} · {record.timestamp ? new Date(record.timestamp).toLocaleString() : "Timestamp not provided"}</small></div>)}</div> : state.status === "empty" ? <EmptyPanel icon={FileSearch} eyebrow="EMPTY MEMORY RESULT" title="No relevant historical memory found" description="The backend returned no matching records for this query." /> : state.status === "unavailable" || state.status === "error" ? <EmptyPanel icon={AlertCircle} eyebrow={state.status === "unavailable" ? "SIBYL MEMORY UNAVAILABLE" : "MEMORY SEARCH ERROR"} title="Unable to search operational memory" description={state.message || "The backend did not return a valid search response."} /> : <EmptyPanel icon={FileSearch} eyebrow="READY FOR QUERY" title="Search real operational memory" description="Results, timestamps, IDs, status, and relevance will appear only from Sibyl Memory." />}</section></div>;
}

function Provenance({ onNotice }: { onNotice: (notice: Notice) => void }) {
  const steps = useMemo(() => [["01", "What happened", "Operator input"], ["02", "What Memora retrieved", "Sibyl memory"], ["03", "What Memora inferred", "Backend inference"], ["04", "What Memora recommended", "Decision response"]], []);
  return <div className="page-section"><div className="workspace-heading"><div><p className="eyebrow">TRACEABILITY / AUDIT VIEW</p><h2>Provenance</h2><p className="heading-copy">Follow the evidence chain without exposing internal storage or implementation details.</p></div><button className="outline-action" onClick={() => onNotice({ type: "info", message: "Provenance details will populate after a real incident-analysis response." })}><PanelRight size={15} />Inspect response</button></div><section className="panel provenance-panel"><SectionKicker label="01 / EVIDENCE CHAIN"><span className="record-status">NO ACTIVE TRACE</span></SectionKicker><div className="provenance-chain">{steps.map(([number, title, detail], index) => <div className="provenance-step" key={number}><div className="provenance-step__top"><span className="provenance-step__number">{number}</span>{index < steps.length - 1 && <span className="provenance-step__connector" />}</div><div className="provenance-step__body"><p className="micro-label">{detail}</p><h3>{title}</h3><p>Unavailable until the backend returns this stage.</p></div></div>)}</div></section><div className="provenance-note"><AlertCircle size={17} /><div><strong>Technical metadata stays progressive.</strong><span>Only backend-provided provenance, decision change, inference, and response identifiers will be exposed here.</span></div></div></div>;
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

  const onAnalysis = (state: BackendState, analysis: IncidentAnalysis | null = null) => setLive((current) => ({ ...current, analysisState: state, analysis: analysis ?? (state.status === "loading" ? null : current.analysis) }));
  const navigate = (id: string) => { setActive(id); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const dismiss = () => setNotice(null);
  return <div className="memora-shell"><Header active={active} onNavigate={navigate} memoryState={live.memoryState} onNewIncident={() => { navigate("workspace"); setTimeout(() => document.getElementById("intake")?.scrollIntoView({ behavior: "smooth" }), 50); }} /><div className="shell-body"><BlueprintRail active={active} onNavigate={navigate} /><main className="main-canvas"><div className="canvas-grid" /><div className="canvas-content"><div className="context-bar"><span><span className="context-pip" />OPERATIONS / {authUser ? "AUTHENTICATED SESSION" : "READINESS VIEW"}</span><span className="context-bar__right"><Clock3 size={13} />UTC display · real backend responses only</span></div>{active === "workspace" && <Workspace onNotice={setNotice} onNavigate={navigate} live={live} onAnalysis={onAnalysis} />}{active === "memory" && <MemoryExplorer onNotice={setNotice} />}{active === "provenance" && <Provenance onNotice={setNotice} />}<footer className="canvas-footer"><span>MEMORA / PHASE 2</span><span>DECISION TRACEABILITY OVER DECISION THEATRE</span><span>v0.1 / CONTRACT-FIRST UI</span></footer></div></main></div>{notice && <div className={cn("notice", notice.type === "error" && "notice--error")} role="status"><div className="notice__icon">{notice.type === "error" ? <X size={16} /> : <Info size={16} />}</div><span>{notice.message}</span><button onClick={dismiss} aria-label="Dismiss notice"><X size={14} /></button></div>}</div>;
}

export { StatusChip };
