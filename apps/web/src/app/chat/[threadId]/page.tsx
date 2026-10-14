"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ApprovalCard } from "@/components/ApprovalCard";
import { ChatPanel } from "@/components/ChatPanel";
import { useRequireMe } from "@/hooks/useMe";
import { useThread } from "@/hooks/useThread";

export default function ChatThreadPage() {
  const params = useParams<{ threadId: string }>();
  const threadId = params.threadId;
  const profile = useRequireMe();
  const thread = useThread(threadId, profile.isSuccess);

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col p-6">
      <Link href="/" className="mb-4 text-sm text-neutral-600 underline">
        ← Threads
      </Link>
      <h1 className="mb-4 text-lg font-semibold">{thread.data?.title ?? "Chat"}</h1>
      <div className="flex flex-1 flex-col gap-3">
        {(thread.data?.messages ?? []).map((m) => (
          <div
            key={m.id}
            className={`rounded px-3 py-2 text-sm whitespace-pre-wrap ${
              m.role === "user" ? "ml-8 bg-neutral-900 text-white" : "mr-8 bg-neutral-100"
            }`}
          >
            {m.content}
            {m.sources && m.sources.length > 0 && (
              <ul className="mt-2 flex flex-wrap gap-1">
                {m.sources.map((s) => (
                  <li
                    key={String(s.id ?? s.uri)}
                    className="rounded bg-white px-2 py-0.5 text-xs text-neutral-700 ring-1 ring-neutral-200"
                  >
                    {String(s.title ?? s.uri)}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
      {threadId && thread.data?.pending_approval && (
        <ApprovalCard threadId={threadId} approval={thread.data.pending_approval} />
      )}
      {threadId && thread.data?.status !== "pending_approval" && (
        <ChatPanel threadId={threadId} />
      )}
    </main>
  );
}
