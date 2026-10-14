import { NextRequest, NextResponse } from "next/server";

const SESSION_COOKIE = "access_token";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const isAuthed = Boolean(req.cookies.get(SESSION_COOKIE)?.value);

  if (pathname.startsWith("/chat") || pathname === "/") {
    if (!isAuthed) {
      const login = new URL("/login", req.url);
      login.searchParams.set("next", pathname);
      return NextResponse.redirect(login);
    }
  }

  if (pathname === "/login" && isAuthed) {
    return NextResponse.redirect(new URL("/", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/chat/:path*", "/login"],
};
