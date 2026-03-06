import { useState, useCallback, useRef, useEffect } from 'react';
import { parseResponse } from '@/lib/parsers';
import type { AnalysisResult } from '@/types/industryConnect';

type Fetcher = (signal: AbortSignal) => AsyncGenerator<string>;

interface UseStreamingReturn {
  streamingText: string;
  parsedResult: AnalysisResult | null;
  isStreaming: boolean;
  error: string | null;
  /** Pass a fetcher produced by industryConnectService — e.g. (signal) => generateProject(req, signal) */
  startStream: (fetcher: Fetcher) => Promise<void>;
  reset: () => void;
}

export function useStreaming(): UseStreamingReturn {
  const [streamingText, setStreamingText] = useState('');
  const [parsedResult, setParsedResult] = useState<AnalysisResult | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setStreamingText('');
    setParsedResult(null);
    setError(null);
    setIsStreaming(false);
  }, []);

  const startStream = useCallback(async (fetcher: Fetcher) => {
    reset();
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      let fullText = '';
      for await (const chunk of fetcher(controller.signal)) {
        fullText += chunk;
        setStreamingText(fullText);
      }

      const parsed = parseResponse(fullText);
      setParsedResult(parsed);
      if (parsed.error) {
        setError(parsed.error);
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      setError(e instanceof Error ? e.message : 'Stream failed');
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [reset]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
  }, []);

  return { streamingText, parsedResult, isStreaming, error, startStream, reset };
}
