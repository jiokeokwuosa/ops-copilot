"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export function useLogin() {
  const router = useRouter();

  return useMutation({
    mutationFn: (input: { email: string; password: string }) => login(input.email, input.password),
    onSuccess: () => router.push("/"),
  });
}
