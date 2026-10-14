"use client";

import { useQuery } from "@tanstack/react-query";
import { listThreads } from "@/lib/api";

export function useThreads(enabled: boolean) {
  return useQuery({
    queryKey: ["threads"],
    queryFn: listThreads,
    enabled,
  });
}
