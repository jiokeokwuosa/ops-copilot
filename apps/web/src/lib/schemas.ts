import { z } from "zod";

export const loginRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export const userProfileSchema = z.object({
  id: z.string(),
  email: z.string(),
  display_name: z.string(),
  tenant_id: z.string(),
  tenant_name: z.string(),
});

export const loginResponseSchema = z.object({
  user: userProfileSchema,
});

export const threadSummarySchema = z.object({
  id: z.string(),
  title: z.string().nullable(),
  status: z.string(),
  updated_at: z.string(),
});

export const messageSchema = z.object({
  id: z.string(),
  role: z.string(),
  content: z.string(),
  steps: z.array(z.record(z.string(), z.unknown())).nullable().optional(),
  sources: z.array(z.record(z.string(), z.unknown())).nullable().optional(),
  created_at: z.string(),
});

export const pendingApprovalSchema = z.object({
  id: z.string(),
  tool_name: z.string(),
  payload: z.record(z.string(), z.unknown()),
  rationale: z.string(),
  status: z.string(),
});

export const threadDetailSchema = threadSummarySchema.extend({
  messages: z.array(messageSchema),
  pending_approval: pendingApprovalSchema.nullable().optional(),
});

export const chatResponseSchema = z.object({
  message_id: z.string(),
  content: z.string(),
  sources: z.array(z.record(z.string(), z.unknown())).nullable().optional(),
  refused: z.boolean(),
  pending_approval: pendingApprovalSchema.nullable().optional(),
});

export const approvalResultSchema = z.object({
  status: z.string(),
  applied: z.boolean(),
});

export type UserProfile = z.infer<typeof userProfileSchema>;
export type ThreadSummary = z.infer<typeof threadSummarySchema>;
export type ThreadDetail = z.infer<typeof threadDetailSchema>;
export type ChatResponse = z.infer<typeof chatResponseSchema>;
export type PendingApproval = z.infer<typeof pendingApprovalSchema>;
export type ApprovalResult = z.infer<typeof approvalResultSchema>;
