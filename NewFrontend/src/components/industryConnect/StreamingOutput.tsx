import { useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface StreamingOutputProps {
  text: string;
  isStreaming: boolean;
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
          Analysis Stream
          {isStreaming && (
            <span className="inline-block h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <pre className="whitespace-pre-wrap font-mono text-sm max-h-96 overflow-y-auto bg-muted/50 rounded-md p-4">
          {text}
          {isStreaming && <span className="animate-pulse">|</span>}
        </pre>
        <div ref={bottomRef} />
      </CardContent>
    </Card>
  );
}
