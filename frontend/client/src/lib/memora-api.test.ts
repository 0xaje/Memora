import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoraApiError, memoraApi } from "./memora-api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("memoraApi REST client", () => {
  it("returns the typed health response from the authoritative backend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "healthy", sibyl_memory_connected: true, version: "0.1.0" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );
    await expect(memoraApi.health()).resolves.toMatchObject({ status: "healthy", sibyl_memory_connected: true });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/health"), expect.anything());
  });

  it("returns typed memory status response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            status: "connected",
            backend: "sqlite",
            storage_state: "available",
            tenant_id: "00000000-0000-0000-0000-000000000001",
            counts: { incidents: 5 },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        )
      )
    );
    const res = await memoraApi.memoryStatus();
    expect(res.status).toBe("connected");
    expect(res.backend).toBe("sqlite");
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/memory/status"), expect.anything());
  });

  it("sends analyzeIncident request and deserializes full analysis", async () => {
    const mockAnalysis = {
      incident: { incident_id: "INC-001", summary: "Suspicious vehicle observed" },
      baseline: { risk: "MEDIUM", recommendation: "MONITOR_AND_VERIFY" },
      decision: { risk: "HIGH", recommendation: "ESCALATE_TO_SUPERVISOR", changed: true },
      decision_changed: true,
      why_decision_changed: "Prior unresolved incident observed.",
      memory: { found: true, count: 1, records: [{ id: "REC-01", summary: "Previous vehicle" }] },
      provenance: { facts: "vehicle", retrieval: "1 record", inference: "recurrent", decision_shift: "escalated" },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(mockAnalysis), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const result = await memoraApi.analyzeIncident({
      raw_text: "Suspicious vehicle observed again near Gate 3.",
      location: "Gate 3",
    });

    expect(result.incident?.incident_id).toBe("INC-001");
    expect(result.decision_changed).toBe(true);
    expect(result.decision?.risk).toBe("HIGH");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/incidents/analyze"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          raw_text: "Suspicious vehicle observed again near Gate 3.",
          location: "Gate 3",
        }),
      })
    );
  });

  it("executes memory search query and deserializes results", async () => {
    const mockSearch = {
      query: "Gate 3",
      count: 1,
      results: [{ id: "INC-001", summary: "Suspicious vehicle at Gate 3" }],
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(mockSearch), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const result = await memoraApi.searchMemory("Gate 3");
    expect(result.count).toBe(1);
    expect(result.results[0].id).toBe("INC-001");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/memory/search?q=Gate%203"),
      expect.anything()
    );
  });

  it("submits outcome and deserializes learning confirmation", async () => {
    const mockOutcome = {
      status: "recorded",
      outcome_id: "OUT-001",
      incident_id: "INC-001",
      is_resolved: true,
      action_taken: "Dispatched patrol",
      observed_result: "Vehicle removed",
      lesson_id: "LES-001",
      message: "Operational outcome and organizational lesson successfully recorded in Sibyl Memory.",
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(mockOutcome), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const result = await memoraApi.recordOutcome({
      incident_id: "INC-001",
      action_taken: "Dispatched patrol",
      observed_result: "Vehicle removed",
      is_resolved: true,
    });

    expect(result.outcome_id).toBe("OUT-001");
    expect(result.status).toBe("recorded");
    expect(result.lesson_id).toBe("LES-001");
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/outcomes"),
      expect.objectContaining({ method: "POST" })
    );
  });

  it("handles HTTP error status and extracts backend detail envelope", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: { code: "SIBYL_UNAVAILABLE", message: "Sibyl storage database is locked" },
          }),
          { status: 503, headers: { "Content-Type": "application/json" } }
        )
      )
    );

    await expect(memoraApi.memoryStatus()).rejects.toMatchObject<Partial<MemoraApiError>>({
      code: "SIBYL_UNAVAILABLE",
      message: "Sibyl storage database is locked",
      status: 503,
    });
  });

  it("handles network failure honest exception", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("Connection refused"))
    );

    await expect(memoraApi.health()).rejects.toMatchObject<Partial<MemoraApiError>>({
      code: "NETWORK_ERROR",
      message: "Memora backend is unreachable.",
    });
  });

  it("rejects malformed non-object JSON responses without inventing fields", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(["array", "not", "object"]), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    await expect(memoraApi.searchMemory("test")).rejects.toMatchObject<Partial<MemoraApiError>>({
      code: "MALFORMED_RESPONSE",
    });
  });
});
