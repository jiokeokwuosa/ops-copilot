"use client";

import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { TimelineStep } from "@/components/StepNode";
import type { PendingApproval } from "@/lib/schemas";
import { threadQueryKey } from "./useThread";

type StreamState = {
  steps: TimelineStep[];
  text: string;
  pendingApproval: PendingApproval | null;
  error: string | null;
  isStreaming: boolean;
};

const initial: StreamState = {
  steps: [],
  text: "",
  pendingApproval: null,
  error: null,
  isStreaming: false,
};

function upsertStep(steps: TimelineStep[], incoming: TimelineStep): TimelineStep[] {
  const idx = steps.findIndex((s) => s.step_id === incoming.step_id);
  if (idx === -1) return [...steps, incoming];
  const next = [...steps];
  next[idx] = { ...next[idx], ...incoming, detail: { ...next[idx].detail, ...incoming.detail } };
  return next;
}

export function useChatStream(threadId: string) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<StreamState>(initial);

  const send = useCallback(
    async (message: string) => {
      setState({ ...initial, isStreaming: true });
      try {
        const res = await fetch(`/api/backend/v1/threads/${threadId}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "same-origin",
          body: JSON.stringify({ message }),
        });
        if (!res.ok || !res.body) {
          throw new Error((await res.text()) || `HTTP ${res.status}`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let eventName = "message";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const chunks = buffer.split("\n\n");
          buffer = chunks.pop() ?? "";
          for (const chunk of chunks) {
            const lines = chunk.split("\n");
            let dataRaw = "";
            for (const line of lines) {
              if (line.startsWith("event:")) eventName = line.slice(6).trim();
              if (line.startsWith("data:")) dataRaw += line.slice(5).trim();
            }
            if (!dataRaw) continue;
            const data = JSON.parse(dataRaw) as Record<string, unknown>;

            if (eventName === "step") {
              setState((prev) => ({
                ...prev,
                steps: upsertStep(prev.steps, {
                  step_id: String(data.step_id),
                  type: String(data.type),
                  label: String(data.label),
                  status: data.status as TimelineStep["status"],
                }),
              }));
            } else if (eventName === "step_detail") {
              setState((prev) => ({
                ...prev,
                steps: upsertStep(prev.steps, {
                  step_id: String(data.step_id),
                  type: "tool",
                  label: "",
                  status: "running",
                  detail: data.detail as TimelineStep["detail"],
                }),
              }));
            } else if (eventName === "token") {
              setState((prev) => ({
                ...prev,
                text: prev.text + String(data.delta ?? ""),
              }));
            } else if (eventName === "approval_required") {
              setState((prev) => ({
                ...prev,
                pendingApproval: {
                  id: String(data.approval_id),
                  tool_name: String(data.tool_name),
                  payload: (data.payload as Record<string, unknown>) ?? {},
                  rationale: String(data.rationale ?? ""),
                  status: "pending",
                },
              }));
            } else if (eventName === "error") {
              setState((prev) => ({
                ...prev,
                error: String(data.message ?? "Stream error"),
                steps: upsertStep(prev.steps, {
                  step_id: String(data.step_id ?? "error"),
                  type: "error",
                  label: "Error",
                  status: "failed",
                  detail: { error: String(data.message ?? "") },
                }),
              }));
            }
          }
        }

        await queryClient.invalidateQueries({ queryKey: threadQueryKey(threadId) });
        await queryClient.invalidateQueries({ queryKey: ["threads"] });
      } catch (err) {
        setState((prev) => ({
          ...prev,
          error: err instanceof Error ? err.message : "Chat failed",
        }));
      } finally {
        setState((prev) => ({ ...prev, isStreaming: false }));
      }
    },
    [queryClient, threadId],
  );

  const reset = useCallback(() => setState(initial), []);

  return { ...state, send, reset };
}
