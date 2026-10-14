"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { sendMessage } from "@/lib/api";
import { threadQueryKey } from "./useThread";

export function useSendMessage(threadId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (message: string) => sendMessage(threadId, message),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: threadQueryKey(threadId) });
    },
  });
}
