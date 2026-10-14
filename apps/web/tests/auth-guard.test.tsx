import { describe, expect, it } from "vitest";
import { config, middleware } from "@/middleware";
import { NextRequest } from "next/server";

describe("auth guard middleware", () => {
  it("matches chat and home routes", () => {
    expect(config.matcher).toContain("/");
    expect(config.matcher).toContain("/chat/:path*");
  });

  it("redirects unauthenticated users away from chat", () => {
    const req = new NextRequest("http://localhost/chat/abc");
    const res = middleware(req);
    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toContain("/login");
  });

  it("allows authenticated users into chat", () => {
    const req = new NextRequest("http://localhost/chat/abc", {
      headers: { cookie: "access_token=fake-token" },
    });
    const res = middleware(req);
    expect(res.status).toBe(200);
  });
});
