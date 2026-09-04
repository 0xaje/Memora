import { describe, expect, it } from "vitest";
import { workspaceContractState } from "./Home";

describe("Memora workspace frontend contract states", () => {
  it("keeps unsupported product procedures explicitly unavailable", () => {
    expect(workspaceContractState).toEqual({
      incidentAnalysis: "unavailable",
      memorySearch: "unavailable",
      memoryStatus: "unavailable",
      outcomeRecording: "unavailable",
      evidenceSummary: "unavailable",
    });
  });

  it("does not expose a fabricated activity or metric state", () => {
    expect(Object.values(workspaceContractState)).not.toContain("active");
    expect(Object.values(workspaceContractState)).not.toContain("42");
  });
});
