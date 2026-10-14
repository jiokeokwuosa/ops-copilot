import { NextResponse } from "next/server";

const API_URL = process.env.API_URL ?? "http://localhost:8000";
const COOKIE_NAME = "access_token";

function sessionMaxAgeSeconds(): number {
  const minutes = Number(process.env.JWT_EXPIRE_MINUTES ?? 1440);
  if (!Number.isFinite(minutes) || minutes <= 0) return 60 * 60 * 24;
  return Math.floor(minutes * 60);
}

export function apiOrigin(): string {
  return API_URL.replace(/\/$/, "");
}

export function setSessionCookie(response: NextResponse, token: string) {
  response.cookies.set(COOKIE_NAME, token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
    maxAge: sessionMaxAgeSeconds(),
  });
}

export function clearSessionCookie(response: NextResponse) {
  response.cookies.set(COOKIE_NAME, "", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
    maxAge: 0,
  });
}

export function readSessionCookie(request: {
  cookies: { get: (name: string) => { value: string } | undefined };
}) {
  return request.cookies.get(COOKIE_NAME)?.value ?? null;
}
