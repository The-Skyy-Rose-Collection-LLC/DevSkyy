/**
 * MessageList Component
 * =====================
 * Displays a list of chat messages with proper formatting.
 */

'use client';

import { useEffect, useRef } from 'react';
import { User, Bot, Wrench, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Badge } from './ui/badge';
import type { ChatMessage } from '@/lib/types';
import { formatDistanceToNow } from 'date-fns';

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="text-center">
          <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p>No messages yet. Start a conversation!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  const isTool = message.role === 'tool';

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex-shrink-0">
          <div className="h-8 w-8 rounded-full bg-brand-primary flex items-center justify-center">
            {isTool ? (
              <Wrench className="h-4 w-4 text-white" />
            ) : (
              <Bot className="h-4 w-4 text-white" />
            )}
          </div>
        </div>
      )}

      <div className={`flex flex-col gap-1 max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? 'bg-brand-primary text-white'
              : isTool
                ? 'bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800'
                : 'bg-gray-100 dark:bg-gray-800'
          }`}
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {/* Tool calls */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="space-y-2 w-full">
            {message.toolCalls.map((toolCall) => (
              <ToolCallDisplay key={toolCall.id} toolCall={toolCall} />
            ))}
          </div>
        )}

        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>{formatDistanceToNow(message.timestamp, { addSuffix: true })}</span>
          {message.agentType && (
            <Badge variant="outline" className="text-xs">
              {message.agentType}
            </Badge>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0">
          <div className="h-8 w-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
            <User className="h-4 w-4 text-gray-700 dark:text-gray-300" />
          </div>
        </div>
      )}
    </div>
  );
}

function ToolCallDisplay({ toolCall }: { toolCall: any }) {
  const statusIcons: Record<string, any> = {
    pending: Loader2,
    running: Loader2,
    completed: CheckCircle,
    failed: AlertCircle,
  };

  const StatusIcon = statusIcons[toolCall.status] || AlertCircle;
  const isLoading = toolCall.status === 'pending' || toolCall.status === 'running';

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-white dark:bg-gray-900">
      <div className="flex items-center gap-2 mb-2">
        <StatusIcon
          className={`h-4 w-4 ${
            isLoading
              ? 'animate-spin text-blue-500'
              : toolCall.status === 'completed'
                ? 'text-green-500'
                : 'text-red-500'
          }`}
        />
        <span className="font-medium text-sm">{toolCall.name}</span>
        <Badge variant="outline" className="text-xs">
          {toolCall.status}
        </Badge>
      </div>

      {toolCall.arguments && (
        <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">
          <pre className="bg-gray-50 dark:bg-gray-800 p-2 rounded overflow-x-auto">
            {JSON.stringify(toolCall.arguments, null, 2)}
          </pre>
        </div>
      )}

      {toolCall.result && (
        <div className="text-xs">
          <span className="text-gray-500 dark:text-gray-400">Result:</span>
          <pre className="bg-green-50 dark:bg-green-900/20 p-2 rounded mt-1 overflow-x-auto">
            {typeof toolCall.result === 'string'
              ? toolCall.result
              : JSON.stringify(toolCall.result, null, 2)}
          </pre>
        </div>
      )}

      {toolCall.error && (
        <div className="text-xs text-red-600 dark:text-red-400 mt-2">
          <span className="font-medium">Error:</span> {toolCall.error}
        </div>
      )}

      {toolCall.startTime && toolCall.endTime && (
        <div className="text-xs text-gray-500 mt-2">
          Duration: {toolCall.endTime - toolCall.startTime}ms
        </div>
      )}
    </div>
  );
}
