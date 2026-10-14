"use client";

import { FormEvent, useState } from "react";
import { useLogin } from "@/hooks/useLogin";

export default function LoginPage() {
  const login = useLogin();
  const [email, setEmail] = useState("alice@tenant-a.example");
  const [password, setPassword] = useState("password123");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    login.mutate({ email, password });
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-6 p-6">
      <h1 className="text-2xl font-semibold tracking-tight">Ops Copilot</h1>
      <p className="text-sm text-neutral-600">Sign in to continue</p>
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <label className="flex flex-col gap-1 text-sm">
          Email
          <input
            className="rounded border border-neutral-300 px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Password
          <input
            className="rounded border border-neutral-300 px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
          />
        </label>
        {login.error && (
          <p className="text-sm text-red-600">
            {login.error instanceof Error ? login.error.message : "Login failed"}
          </p>
        )}
        <button
          type="submit"
          disabled={login.isPending}
          className="rounded bg-neutral-900 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {login.isPending ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
