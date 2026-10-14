"use client";

export type SourceRef = {
  id?: string;
  title?: string;
  uri?: string;
};

export function SourceChips({ sources }: { sources: SourceRef[] }) {
  if (!sources.length) return null;
  return (
    <ul className="mt-1 flex flex-wrap gap-1">
      {sources.map((s) => (
        <li
          key={String(s.id ?? s.uri ?? s.title)}
          className="rounded bg-white px-2 py-0.5 text-xs text-neutral-700 ring-1 ring-neutral-200"
          title={s.uri}
        >
          {s.title ?? s.uri ?? s.id}
        </li>
      ))}
    </ul>
  );
}
