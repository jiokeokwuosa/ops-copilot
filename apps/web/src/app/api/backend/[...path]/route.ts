import { NextRequest, NextResponse } from "next/server";
import { apiOrigin, readSessionCookie } from "@/lib/server/session";

type RouteContext = { params: Promise<{ path: string[] }> };

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function forward(req: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  if (path.some((segment) => segment === ".." || segment.includes("/"))) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  const targetPath = `/${path.join("/")}`;
  if (targetPath === "/v1/auth/login") {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const token = readSessionCookie(req);
  if (token) headers.set("authorization", `Bearer ${token}`);

  const hasBody = req.method !== "GET" && req.method !== "HEAD";
  let upstream: Response;
  try {
    upstream = await fetch(`${apiOrigin()}${targetPath}${req.nextUrl.search}`, {
      method: req.method,
      headers,
      body: hasBody ? await req.text() : undefined,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "API unavailable" }, { status: 502 });
  }

  const upstreamType = upstream.headers.get("content-type") ?? "application/json";
  const responseHeaders: Record<string, string> = {
    "content-type": upstreamType,
    "cache-control": "no-store",
  };

  // Pass through SSE streams without buffering the whole body.
  if (upstreamType.includes("text/event-stream") && upstream.body) {
    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: {
        ...responseHeaders,
        connection: "keep-alive",
        "x-accel-buffering": "no",
      },
    });
  }

  return new NextResponse(await upstream.text(), {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const PUT = forward;
export const DELETE = forward;
