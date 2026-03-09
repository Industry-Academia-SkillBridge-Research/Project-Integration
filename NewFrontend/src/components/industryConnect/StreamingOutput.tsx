import { useRef, useEffect, Fragment } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface StreamingOutputProps {
  text: string;
  isStreaming: boolean;
}

/** Render a single inline span, handling **bold** and *italic* */
function renderInline(line: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  // Split on **bold** and *italic*
  const regex = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let key = 0;
  while ((match = regex.exec(line)) !== null) {
    if (match.index > last) {
      parts.push(<Fragment key={key++}>{line.slice(last, match.index)}</Fragment>);
    }
    if (match[2]) {
      parts.push(<strong key={key++} className="font-semibold">{match[2]}</strong>);
    } else if (match[3]) {
      parts.push(<em key={key++}>{match[3]}</em>);
    } else if (match[4]) {
      parts.push(
        <code key={key++} className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">
          {match[4]}
        </code>
      );
    }
    last = match.index + match[0].length;
  }
  if (last < line.length) {
    parts.push(<Fragment key={key++}>{line.slice(last)}</Fragment>);
  }
  return parts.length === 1 ? parts[0] : <>{parts}</>;
}

function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split('\n');
  const nodes: React.ReactNode[] = [];
  let listItems: string[] = [];
  let listOrdered = false;
  let nodeKey = 0;

  const flushList = () => {
    if (listItems.length === 0) return;
    const Tag = listOrdered ? 'ol' : 'ul';
    nodes.push(
      <Tag
        key={nodeKey++}
        className={`my-2 pl-5 space-y-0.5 text-sm ${listOrdered ? 'list-decimal' : 'list-disc'}`}
      >
        {listItems.map((item, i) => (
          <li key={i}>{renderInline(item)}</li>
        ))}
      </Tag>
    );
    listItems = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Headings
    const h3 = line.match(/^###\s+(.*)/);
    const h2 = line.match(/^##\s+(.*)/);
    const h1 = line.match(/^#\s+(.*)/);

    if (h1 || h2 || h3) {
      flushList();
      const content = (h1 ?? h2 ?? h3)![1];
      if (h1) {
        nodes.push(<h1 key={nodeKey++} className="text-lg font-bold mt-4 mb-1 text-foreground">{renderInline(content)}</h1>);
      } else if (h2) {
        nodes.push(<h2 key={nodeKey++} className="text-base font-semibold mt-3 mb-1 text-foreground">{renderInline(content)}</h2>);
      } else {
        nodes.push(<h3 key={nodeKey++} className="text-sm font-semibold mt-2 mb-0.5 text-foreground">{renderInline(content)}</h3>);
      }
      continue;
    }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) {
      flushList();
      nodes.push(<hr key={nodeKey++} className="my-3 border-border" />);
      continue;
    }

    // Unordered list
    const ulMatch = line.match(/^[\s]*[-*+]\s+(.*)/);
    if (ulMatch) {
      if (listItems.length > 0 && listOrdered) flushList();
      listOrdered = false;
      listItems.push(ulMatch[1]);
      continue;
    }

    // Ordered list
    const olMatch = line.match(/^[\s]*\d+[.)]\s+(.*)/);
    if (olMatch) {
      if (listItems.length > 0 && !listOrdered) flushList();
      listOrdered = true;
      listItems.push(olMatch[1]);
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      flushList();
      nodes.push(<div key={nodeKey++} className="h-2" />);
      continue;
    }

    // Normal paragraph line
    flushList();
    nodes.push(
      <p key={nodeKey++} className="text-sm leading-relaxed text-foreground/90">
        {renderInline(line)}
      </p>
    );
  }

  flushList();
  return nodes;
}

export default function StreamingOutput({ text, isStreaming }: StreamingOutputProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [text]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          Generating Plan
          {isStreaming && (
            <span className="inline-block h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          )}
          {!isStreaming && text && (
            <span className="text-xs font-normal text-muted-foreground ml-1">Complete</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="max-h-[32rem] overflow-y-auto rounded-md border bg-muted/30 px-5 py-4">
          {renderMarkdown(text)}
          {isStreaming && (
            <span className="inline-block w-0.5 h-4 bg-foreground/70 animate-pulse align-middle ml-0.5" />
          )}
          <div ref={bottomRef} />
        </div>
      </CardContent>
    </Card>
  );
}
