"use client";

import { useState, useCallback, useRef } from "react";

export interface AgentMessage {
  type: "thinking" | "text" | "tool_use" | "tool_result" | "progress" | "result" | "error";
  content: string;
  tool?: string;
  input?: Record<string, unknown>;
  session_id?: string;
  cost_usd?: number;
}

export type AgentStatus = "idle" | "running" | "done" | "error";

export function useWordPressAgent() {
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  const execute = useCallback(
    async (intent: string, prompt: string, context?: Record<string, unknown>) => {
      setStatus("running");
      setMessages([]);

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await fetch("/api/v1/agent/execute", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ intent, prompt, context }),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Agent error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6).trim();
              if (data === "[DONE]") {
                setStatus("done");
                return;
              }
              try {
                const event: AgentMessage = JSON.parse(data);
                setMessages((prev) => [...prev, event]);
              } catch {
                // Skip malformed events
              }
            }
          }
        }

        setStatus("done");
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          setStatus("error");
          setMessages((prev) => [
            ...prev,
            { type: "error", content: (error as Error).message },
          ]);
        }
      }
    },
    [],
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
    setStatus("idle");
  }, []);

  const reset = useCallback(() => {
    setStatus("idle");
    setMessages([]);
  }, []);

  return { status, messages, execute, abort, reset };
}
