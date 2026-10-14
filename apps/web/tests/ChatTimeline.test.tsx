import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChatTimeline } from "@/components/ChatTimeline";

describe("ChatTimeline", () => {
  it("renders step labels and source chips", () => {
    render(
      <ChatTimeline
        steps={[
          {
            step_id: "s1",
            type: "searching",
            label: "Searching docs",
            status: "completed",
            detail: { query: "reset MFA" },
          },
          {
            step_id: "s2",
            type: "reading",
            label: "Reading sources",
            status: "completed",
            detail: {
              sources: [{ id: "c1", title: "MFA Reset", uri: "docs/corpus/mfa-reset.md" }],
            },
          },
        ]}
        streamingText="To reset MFA..."
      />,
    );

    expect(screen.getByText("Searching docs")).toBeInTheDocument();
    expect(screen.getByText("query: reset MFA")).toBeInTheDocument();
    expect(screen.getByText("Reading sources")).toBeInTheDocument();
    expect(screen.getByText("MFA Reset")).toBeInTheDocument();
    expect(screen.getByText("To reset MFA...")).toBeInTheDocument();
  });
});
