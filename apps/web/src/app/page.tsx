"use client";

import Link from "next/link";
import { useCreateThread } from "@/hooks/useCreateThread";
import { useRequireMe, useSignOut } from "@/hooks/useMe";
import { useThreads } from "@/hooks/useThreads";

export default function HomePage() {
  const profile = useRequireMe();
  const threads = useThreads(profile.isSuccess);
  const create = useCreateThread();
  const signOut = useSignOut();

  if (profile.isLoading || profile.isError) {
    return <main className="p-6 text-sm text-neutral-600">Loading…</main>;
  }

  return (
    <main className="mx-auto max-w-2xl p-6">
      <header className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Ops Copilot</h1>
          <p className="text-sm text-neutral-600">
            {profile.data?.display_name} · {profile.data?.tenant_name}
          </p>
        </div>
        <button type="button" className="text-sm text-neutral-600 underline" onClick={signOut}>
          Sign out
        </button>
      </header>
      <button
        type="button"
        onClick={() => create.mutate()}
        className="mb-4 rounded bg-neutral-900 px-3 py-2 text-sm text-white"
      >
        New thread
      </button>
      <ul className="divide-y divide-neutral-200 rounded border border-neutral-200">
        {(threads.data ?? []).map((t) => (
          <li key={t.id}>
            <Link className="block px-3 py-3 text-sm hover:bg-neutral-50" href={`/chat/${t.id}`}>
              {t.title ?? "Untitled"} · {t.status}
            </Link>
          </li>
        ))}
        {threads.isSuccess && threads.data.length === 0 && (
          <li className="px-3 py-6 text-sm text-neutral-500">No threads yet</li>
        )}
      </ul>
    </main>
  );
}
