"use client";

import { FormEvent, useState } from "react";
import { ApprovalCard } from "@/components/ApprovalCard";
import { ChatTimeline } from "@/components/ChatTimeline";
import { useChatStream } from "@/hooks/useChatStream";

export function ChatPanel({ threadId }: { threadId: string }) {
  const [text, setText] = useState("");
  const stream = useChatStream(threadId);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim() || stream.isStreaming) return;
    const message = text.trim();
    setText("");
    await stream.send(message);
  }

  return (
    <div className="mt-4 border-t border-neutral-200 pt-4">
      <ChatTimeline steps={stream.steps} streamingText={stream.text} />
      {stream.pendingApproval && (
        <ApprovalCard threadId={threadId} approval={stream.pendingApproval} />
      )}
      {!stream.pendingApproval && (
        <form onSubmit={onSubmit} className="flex gap-2">
          <input
            className="flex-1 rounded border border-neutral-300 px-3 py-2 text-sm"
            placeholder="Ask about internal support topics…"
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={stream.isStreaming}
          />
          <button
            type="submit"
            disabled={stream.isStreaming}
            className="rounded bg-neutral-900 px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            {stream.isStreaming ? "…" : "Send"}
          </button>
        </form>
      )}
      {stream.error && <p className="mt-2 text-sm text-red-600">{stream.error}</p>}
    </div>
  );
}
