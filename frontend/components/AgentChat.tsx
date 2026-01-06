/**
 * AgentChat Component
 * ===================
 * Main chat interface component combining all chat UI elements.
 */

'use client';

import { AgentHeader } from './AgentHeader';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import type { ChatMessage, SuperAgentType } from '@/lib/types';

interface AgentChatProps {
  agentId: SuperAgentType;
  messages: ChatMessage[];
  onSend: (message: string) => void;
  streaming?: boolean;
  status?: 'online' | 'offline' | 'busy';
}

export function AgentChat({
  agentId,
  messages,
  onSend,
  streaming = false,
  status = 'online',
}: AgentChatProps) {
  return (
    <div className="h-screen flex flex-col">
      <AgentHeader agentId={agentId} status={status} />

      <div className="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-950">
        <div className="max-w-4xl mx-auto">
          <MessageList messages={messages} />
        </div>
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6">
        <div className="max-w-4xl mx-auto">
          <ChatInput
            onSend={onSend}
            disabled={streaming}
            placeholder={`Ask the ${agentId} agent...`}
          />
          {streaming && (
            <p className="text-xs text-gray-500 mt-2 text-center">
              Agent is typing...
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
