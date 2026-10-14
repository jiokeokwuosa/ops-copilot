"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { logout, me } from "@/lib/api";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: me,
    retry: false,
  });
}

export function useRequireMe() {
  const router = useRouter();
  const profile = useMe();

  useEffect(() => {
    if (profile.isError) router.replace("/login");
  }, [profile.isError, router]);

  return profile;
}

export function useSignOut() {
  const router = useRouter();
  const queryClient = useQueryClient();
  return async () => {
    await logout();
    queryClient.clear();
    router.push("/login");
  };
}
