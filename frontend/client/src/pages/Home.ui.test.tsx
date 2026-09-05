import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/trpc", () => ({
  trpc: { auth: { me: { useQuery: () => ({ data: undefined }) } } },
}));

vi.mock("@/_core/hooks/useAuth", () => ({
  useAuth: () => ({ user: null, loading: false, logout: vi.fn() }),
}));

vi.mock("@/const", () => ({ startLogin: vi.fn() }));

import Home from "./Home";

describe("Memora Home workspace UI states", () => {
  it("renders honest empty and unavailable states without activity records", () => {
    const html = renderToStaticMarkup(<Home />);

    expect(html).toContain("No incident analyzed yet");
    expect(html).toContain("Historical memory not ready");
    expect(html).toContain("Awaiting analysis");
    expect(html).toContain("NOT CONNECTED");
    expect(html).toContain("Historical memory not ready");
    expect(html).not.toContain("42");
  });

  it("renders evidence-only AI guardrail copy", () => {
    const html = renderToStaticMarkup(<Home />);

    expect(html).toContain("summarize only incident evidence returned by the backend");
    expect(html).toContain("never create activity, memory, metrics, or recommendations");
  });
});
