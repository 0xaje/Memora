import { afterEach, describe, expect, it, vi } from "vitest";
import { MemoraApiError, memoraApi } from "./memora-api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("memoraApi", () => {
  it("returns the typed health response from the authoritative backend", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "healthy", sibyl_memory_connected: true, version: "0.1.0" }), { status: 200, headers: { "Content-Type": "application/json" } })));
    await expect(memoraApi.health()).resolves.toMatchObject({ status: "healthy", sibyl_memory_connected: true });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/health"), expect.objectContaining({ headers: expect.objectContaining({ "Content-Type": "application/json" }) }));
  });

  it("preserves the backend error code and message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: { code: "SIBYL_UNAVAILABLE", message: "storage unavailable" } }), { status: 503, headers: { "Content-Type": "application/json" } })));
    await expect(memoraApi.memoryStatus()).rejects.toMatchObject<Partial<MemoraApiError>>({ code: "SIBYL_UNAVAILABLE", message: "storage unavailable", status: 503 });
  });

  it("rejects malformed successful responses instead of inventing fields", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(["not", "an", "object"]), { status: 200, headers: { "Content-Type": "application/json" } })));
    await expect(memoraApi.searchMemory("Gate 3")).rejects.toMatchObject<Partial<MemoraApiError>>({ code: "MALFORMED_RESPONSE" });
  });
});
