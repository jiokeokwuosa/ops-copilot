"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { resolveApproval } from "@/lib/api";

export function useApprove(threadId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      approvalId,
      decision,
    }: {
      approvalId: string;
      decision: "approve" | "reject";
    }) => resolveApproval(threadId, approvalId, decision),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["thread", threadId] });
      void qc.invalidateQueries({ queryKey: ["threads"] });
    },
  });
}
