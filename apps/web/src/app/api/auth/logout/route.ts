import { NextResponse } from "next/server";
import { clearSessionCookie } from "@/lib/server/session";

export async function POST() {
  const response = NextResponse.json({ ok: true });
  response.headers.set("Cache-Control", "no-store");
  clearSessionCookie(response);
  return response;
}
