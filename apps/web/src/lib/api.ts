import {
  approvalResultSchema,
  chatResponseSchema,
  loginResponseSchema,
  threadDetailSchema,
  threadSummarySchema,
  type ApprovalResult,
  type ChatResponse,
  type ThreadDetail,
  type ThreadSummary,
  type UserProfile,
  userProfileSchema,
} from "./schemas";

function clearLegacyToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  schema?: { parse: (data: unknown) => T },
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");

  const res = await fetch(path, { ...options, headers, credentials: "same-origin" });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const data = await res.json();
  return schema ? schema.parse(data) : (data as T);
}

export async function login(email: string, password: string) {
  const data = await apiFetch(
    "/api/auth/login",
    { method: "POST", body: JSON.stringify({ email, password }) },
    loginResponseSchema,
  );
  clearLegacyToken();
  return data;
}

export async function logout() {
  clearLegacyToken();
  await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" });
}

export async function me(): Promise<UserProfile> {
  return apiFetch("/api/backend/v1/auth/me", {}, userProfileSchema);
}

export async function listThreads(): Promise<ThreadSummary[]> {
  const data = await apiFetch<{ items: ThreadSummary[] }>("/api/backend/v1/threads");
  return data.items.map((t) => threadSummarySchema.parse(t));
}

export async function createThread(title?: string): Promise<ThreadSummary> {
  return apiFetch(
    "/api/backend/v1/threads",
    { method: "POST", body: JSON.stringify({ title: title ?? null }) },
    threadSummarySchema,
  );
}

export async function getThread(threadId: string): Promise<ThreadDetail> {
  return apiFetch(`/api/backend/v1/threads/${threadId}`, {}, threadDetailSchema);
}

export async function sendMessage(threadId: string, message: string): Promise<ChatResponse> {
  return apiFetch(
    `/api/backend/v1/threads/${threadId}/chat`,
    { method: "POST", body: JSON.stringify({ message }) },
    chatResponseSchema,
  );
}

export async function resolveApproval(
  threadId: string,
  approvalId: string,
  decision: "approve" | "reject",
): Promise<ApprovalResult> {
  return apiFetch(
    `/api/backend/v1/threads/${threadId}/approvals/${approvalId}`,
    { method: "POST", body: JSON.stringify({ decision }) },
    approvalResultSchema,
  );
}
