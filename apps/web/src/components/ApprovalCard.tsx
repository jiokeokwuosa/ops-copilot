"use client";

import { useApprove } from "@/hooks/useApprove";

type PendingApproval = {
  id: string;
  tool_name: string;
  payload: Record<string, unknown>;
  rationale: string;
  status: string;
};

export function ApprovalCard({
  threadId,
  approval,
}: {
  threadId: string;
  approval: PendingApproval;
}) {
  const approve = useApprove(threadId);

  return (
    <aside className="mt-4 rounded border border-amber-300 bg-amber-50 p-4 text-sm">
      <h2 className="font-semibold text-amber-950">Approval required</h2>
      <p className="mt-1 text-amber-900">{approval.rationale}</p>
      <p className="mt-2 text-xs text-amber-800">
        Tool: <code>{approval.tool_name}</code>
      </p>
      <pre className="mt-2 overflow-x-auto rounded bg-white p-2 text-xs text-neutral-800 ring-1 ring-amber-200">
        {JSON.stringify(approval.payload, null, 2)}
      </pre>
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          disabled={approve.isPending}
          onClick={() => approve.mutate({ approvalId: approval.id, decision: "approve" })}
          className="rounded bg-neutral-900 px-3 py-1.5 text-white disabled:opacity-50"
        >
          Approve
        </button>
        <button
          type="button"
          disabled={approve.isPending}
          onClick={() => approve.mutate({ approvalId: approval.id, decision: "reject" })}
          className="rounded border border-neutral-400 bg-white px-3 py-1.5 text-neutral-800 disabled:opacity-50"
        >
          Reject
        </button>
      </div>
      {approve.error && (
        <p className="mt-2 text-red-600">
          {approve.error instanceof Error ? approve.error.message : "Decision failed"}
        </p>
      )}
    </aside>
  );
}
