"use client";

import { SourceChips, type SourceRef } from "./SourceChips";

export type TimelineStep = {
  step_id: string;
  type: string;
  label: string;
  status: "running" | "completed" | "failed";
  detail?: {
    query?: string;
    sources?: SourceRef[];
    tool_name?: string | null;
    error?: string | null;
  };
};

export function StepNode({ step }: { step: TimelineStep }) {
  const statusColor =
    step.status === "failed"
      ? "border-red-300 bg-red-50"
      : step.status === "running"
        ? "border-sky-300 bg-sky-50"
        : "border-neutral-200 bg-neutral-50";

  return (
    <li className={`rounded border px-3 py-2 text-sm ${statusColor}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-neutral-900">{step.label}</span>
        <span className="text-xs uppercase tracking-wide text-neutral-500">{step.status}</span>
      </div>
      {step.detail?.query && (
        <p className="mt-1 font-mono text-xs text-neutral-700">query: {step.detail.query}</p>
      )}
      {step.detail?.tool_name && (
        <p className="mt-1 text-xs text-neutral-600">tool: {step.detail.tool_name}</p>
      )}
      {step.detail?.error && (
        <p className="mt-1 text-xs text-red-700">{step.detail.error}</p>
      )}
      {step.detail?.sources && <SourceChips sources={step.detail.sources} />}
    </li>
  );
}
