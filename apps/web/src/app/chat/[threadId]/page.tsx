"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ApprovalCard } from "@/components/ApprovalCard";
import { ChatPanel } from "@/components/ChatPanel";
import { ChatTimeline } from "@/components/ChatTimeline";
import { SourceChips } from "@/components/SourceChips";
import { useRequireMe } from "@/hooks/useMe";
import { useThread } from "@/hooks/useThread";
import type { TimelineStep } from "@/components/StepNode";

function messageSteps(steps: unknown): TimelineStep[] {
  if (!Array.isArray(steps)) return [];
  return steps.map((raw) => {
    const s = raw as Record<string, unknown>;
    const detail = (s.detail as TimelineStep["detail"]) ?? undefined;
    return {
      step_id: String(s.id ?? s.step_id ?? crypto.randomUUID()),
      type: String(s.type ?? "tool"),
      label: String(s.label ?? s.type ?? "Step"),
      status: (s.status as TimelineStep["status"]) ?? "completed",
      detail,
    };
  });
}

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
          <div key={m.id}>
            {m.role === "assistant" && m.steps && (
              <ChatTimeline steps={messageSteps(m.steps)} />
            )}
            <div
              className={`rounded px-3 py-2 text-sm whitespace-pre-wrap ${
                m.role === "user" ? "ml-8 bg-neutral-900 text-white" : "mr-8 bg-neutral-100"
              }`}
            >
              {m.content}
              {m.sources && m.sources.length > 0 && (
                <SourceChips
                  sources={m.sources.map((s) => ({
                    id: String(s.id ?? ""),
                    title: String(s.title ?? ""),
                    uri: String(s.uri ?? ""),
                  }))}
                />
              )}
            </div>
          </div>
        ))}
      </div>
      {threadId && thread.data?.pending_approval && (
        <ApprovalCard threadId={threadId} approval={thread.data.pending_approval} />
      )}
      {threadId && thread.data?.status !== "pending_approval" && <ChatPanel threadId={threadId} />}
    </main>
  );
}
