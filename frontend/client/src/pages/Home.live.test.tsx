import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { AnalysisOutput, getAnalysisStateCopy, getMemorySearchStateLabel, getSibylStatusCopy } from "./Home";

describe("Memora live UI state copy", () => {
  it("surfaces each real Sibyl status without assuming connectivity", () => {
    expect(getSibylStatusCopy({ status: "loading" })).toMatchObject({ label: "Sibyl checking" });
    expect(getSibylStatusCopy({ status: "success" })).toMatchObject({ label: "Sibyl connected", tone: "ok" });
    expect(getSibylStatusCopy({ status: "unavailable" })).toMatchObject({ label: "Sibyl unavailable" });
    expect(getSibylStatusCopy({ status: "error" })).toMatchObject({ label: "Sibyl error" });
  });

  it("renders incident analysis loading, unavailable, error, and success states from backend-shaped state", () => {
    expect(renderToStaticMarkup(<AnalysisOutput analysis={null} state={{ status: "loading" }} />)).toContain("Waiting for Memora backend");
    expect(renderToStaticMarkup(<AnalysisOutput analysis={null} state={{ status: "unavailable", message: "Memora backend is unreachable." }} />)).toContain("Memora backend is unreachable.");
    expect(renderToStaticMarkup(<AnalysisOutput analysis={null} state={{ status: "error", message: "Validation failed." }} />)).toContain("Validation failed.");
    expect(getAnalysisStateCopy({ status: "success" })).toBe("Backend analysis received");
    
    // With decision changed:
    const htmlWithChange = renderToStaticMarkup(
      <AnalysisOutput
        analysis={{
          incident: { incident_id: "INC-TEST", summary: "Backend incident response" },
          baseline: { risk: "MEDIUM", recommendation: "MONITOR_AND_VERIFY" },
          decision: { risk: "HIGH", recommendation: "ESCALATE_TO_SUPERVISOR" },
          decision_changed: true,
          why_decision_changed: "Backend-provided rationale",
          memory: { found: true, count: 1, records: [{ id: "REC-01", category: "incident", summary: "Previous vehicle incident" }] },
        }}
        state={{ status: "success" }}
      />
    );
    expect(htmlWithChange).toContain("MEMORY CHANGED THIS DECISION");
    expect(htmlWithChange).toContain("Previous vehicle incident");
    expect(htmlWithChange).toContain("Backend-provided rationale");

    // Without decision change:
    const htmlUnchanged = renderToStaticMarkup(
      <AnalysisOutput
        analysis={{
          incident: { incident_id: "INC-TEST-2", summary: "Clean baseline incident" },
          baseline: { risk: "MEDIUM", recommendation: "MONITOR_AND_VERIFY" },
          decision: { risk: "MEDIUM", recommendation: "MONITOR_AND_VERIFY" },
          decision_changed: false,
        }}
        state={{ status: "success" }}
      />
    );
    expect(htmlUnchanged).not.toContain("MEMORY CHANGED THIS DECISION");
    expect(htmlUnchanged).toContain("Clean baseline incident");
  });

  it("distinguishes real memory search states", () => {
    expect(getMemorySearchStateLabel({ status: "loading" })).toBe("SEARCHING");
    expect(getMemorySearchStateLabel({ status: "success" }, 3)).toBe("3 RESULTS");
    expect(getMemorySearchStateLabel({ status: "empty" })).toBe("NO MATCHES");
    expect(getMemorySearchStateLabel({ status: "unavailable" })).toBe("SIBYL UNAVAILABLE");
    expect(getMemorySearchStateLabel({ status: "error" })).toBe("SEARCH ERROR");
  });
});
