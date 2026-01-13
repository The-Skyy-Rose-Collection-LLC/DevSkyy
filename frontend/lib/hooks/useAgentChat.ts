/**
 * Agent Chat Hook
 * ================
 * Custom hook for managing agent chat state and streaming.
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import type { ChatMessage, SuperAgentType, StreamChunk, ToolCall } from '@/lib/types';

interface UseAgentChatOptions {
  agentType: SuperAgentType;
  onError?: (error: Error) => void;
}

export function useAgentChat({ agentType, onError }: UseAgentChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (content: string) => {
      // Add user message
      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        timestamp: Date.now(),
        agentType,
      };
      setMessages(prev => [...prev, userMessage]);
      setStreaming(true);

      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController();

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/v1/agents/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_type: agentType,
            message: content,
            stream: true,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }

        // Process streaming response
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          agentType,
          toolCalls: [],
        };

        let buffer = '';

        while (true) {
          const { done, value } = await reader!.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || trimmed === 'data: [DONE]') continue;

            try {
              // Parse SSE format: "data: {json}"
              const data = trimmed.startsWith('data: ') ? trimmed.slice(6) : trimmed;
              const chunk: StreamChunk = JSON.parse(data);

              if (chunk.type === 'content') {
                assistantMessage.content += chunk.content || '';
              } else if (chunk.type === 'tool_call' && chunk.toolCall) {
                if (!assistantMessage.toolCalls) {
                  assistantMessage.toolCalls = [];
                }
                const existingIndex = assistantMessage.toolCalls.findIndex(
                  t => t.id === chunk.toolCall!.id
                );
                if (existingIndex >= 0) {
                  assistantMessage.toolCalls[existingIndex] = chunk.toolCall;
                } else {
                  assistantMessage.toolCalls.push(chunk.toolCall);
                }
              } else if (chunk.type === 'tool_result' && chunk.toolCall) {
                if (assistantMessage.toolCalls) {
                  const toolIndex = assistantMessage.toolCalls.findIndex(
                    t => t.id === chunk.toolCall!.id
                  );
                  if (toolIndex >= 0) {
                    assistantMessage.toolCalls[toolIndex] = {
                      ...assistantMessage.toolCalls[toolIndex],
                      ...chunk.toolCall,
                    };
                  }
                }
              } else if (chunk.type === 'error') {
                assistantMessage.content += `\n\n[Error: ${chunk.error}]`;
              }

              // Update message in state
              setMessages(prev => {
                const existing = prev.find(m => m.id === assistantMessage.id);
                if (existing) {
                  return prev.map(m =>
                    m.id === assistantMessage.id ? { ...assistantMessage } : m
                  );
                }
                return [...prev, { ...assistantMessage }];
              });
            } catch (e) {
              console.error('Failed to parse chunk:', trimmed, e);
            }
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          // Request was cancelled
          return;
        }

        console.error('Chat error:', error);
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `Sorry, I encountered an error: ${
            error instanceof Error ? error.message : 'Unknown error'
          }`,
          timestamp: Date.now(),
          agentType,
        };
        setMessages(prev => [...prev, errorMessage]);

        if (onError && error instanceof Error) {
          onError(error);
        }
      } finally {
        setStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [agentType, onError]
  );

  const cancelStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setStreaming(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    streaming,
    sendMessage,
    cancelStreaming,
    clearMessages,
  };
}
