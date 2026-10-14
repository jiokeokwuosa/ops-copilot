import { NextRequest, NextResponse } from "next/server";
import { apiOrigin, setSessionCookie } from "@/lib/server/session";

export async function POST(req: NextRequest) {
  const body = await req.text();
  let upstream: Response;
  try {
    upstream = await fetch(`${apiOrigin()}/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "API unavailable" }, { status: 502 });
  }

  const data: unknown = await upstream.json().catch(() => null);
  if (!upstream.ok) {
    return NextResponse.json(data ?? { detail: "Login failed" }, { status: upstream.status });
  }

  const token =
    data &&
    typeof data === "object" &&
    "access_token" in data &&
    typeof data.access_token === "string"
      ? data.access_token
      : null;
  const user = data && typeof data === "object" && "user" in data ? data.user : null;
  if (!token || !user) {
    return NextResponse.json({ detail: "Login failed" }, { status: 502 });
  }

  const response = NextResponse.json({ user: user });
  response.headers.set("Cache-Control", "no-store");
  setSessionCookie(response, token);
  return response;
}
