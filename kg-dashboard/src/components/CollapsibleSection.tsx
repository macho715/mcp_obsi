import { useState } from 'react';
import type { PropsWithChildren, ReactNode } from 'react';

interface CollapsibleSectionProps extends PropsWithChildren {
  sectionId: string;
  title: string;
  summary?: ReactNode;
  defaultOpen?: boolean;
}

export function CollapsibleSection({
  sectionId,
  title,
  summary,
  defaultOpen = false,
  children,
}: CollapsibleSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <details
      className="collapsible-section"
      data-section-id={sectionId}
      open={isOpen}
      onToggle={(event) => setIsOpen(event.currentTarget.open)}
    >
      <summary className="collapsible-section__summary">
        <span className="collapsible-section__title">{title}</span>
        {summary != null ? <span className="collapsible-section__meta">{summary}</span> : null}
      </summary>
      <div className="collapsible-section__body">{children}</div>
    </details>
  );
}