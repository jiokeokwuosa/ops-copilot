"use client";

import { StepNode, type TimelineStep } from "./StepNode";

export function ChatTimeline({
  steps,
  streamingText,
}: {
  steps: TimelineStep[];
  streamingText?: string;
}) {
  if (!steps.length && !streamingText) return null;

  return (
    <div className="my-3 space-y-2">
      <ol className="flex flex-col gap-2">
        {steps.map((step) => (
          <StepNode key={step.step_id} step={step} />
        ))}
      </ol>
      {streamingText !== undefined && streamingText !== "" && (
        <div className="rounded bg-neutral-100 px-3 py-2 text-sm whitespace-pre-wrap text-neutral-900">
          {streamingText}
        </div>
      )}
    </div>
  );
}
