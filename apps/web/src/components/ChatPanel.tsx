"use client";

import { FormEvent, useState } from "react";
import { useSendMessage } from "@/hooks/useSendMessage";

export function ChatPanel({ threadId }: { threadId: string }) {
  const [text, setText] = useState("");
  const send = useSendMessage(threadId);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    send.mutate(text.trim(), { onSuccess: () => setText("") });
  }

  return (
    <form onSubmit={onSubmit} className="mt-4 flex gap-2 border-t border-neutral-200 pt-4">
      <input
        className="flex-1 rounded border border-neutral-300 px-3 py-2 text-sm"
        placeholder="Ask about internal support topics…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={send.isPending}
      />
      <button
        type="submit"
        disabled={send.isPending}
        className="rounded bg-neutral-900 px-3 py-2 text-sm text-white disabled:opacity-50"
      >
        {send.isPending ? "…" : "Send"}
      </button>
      {send.error && (
        <p className="basis-full text-sm text-red-600">
          {send.error instanceof Error ? send.error.message : "Chat failed"}
        </p>
      )}
    </form>
  );
}
