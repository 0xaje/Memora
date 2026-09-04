import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

describe("Memora workspace contract boundary", () => {
  it("returns the real authenticated operator through the typed auth procedure", async () => {
    const user = {
      id: 7,
      openId: "operator-open-id",
      email: "operator@example.com",
      name: "Operations Officer",
      loginMethod: "manus",
      role: "admin" as const,
      createdAt: new Date("2026-01-01T00:00:00.000Z"),
      updatedAt: new Date("2026-01-01T00:00:00.000Z"),
      lastSignedIn: new Date("2026-01-01T00:00:00.000Z"),
    };

    const ctx: TrpcContext = {
      user,
      req: { protocol: "https", headers: {} } as TrpcContext["req"],
      res: {} as TrpcContext["res"],
    };

    const result = await appRouter.createCaller(ctx).auth.me();

    expect(result).toEqual(user);
    expect(result?.name).toBe("Operations Officer");
  });
});
