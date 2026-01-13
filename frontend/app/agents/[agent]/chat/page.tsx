/**
 * Agent Chat Page
 * ===============
 * Real-time chat interface with streaming and tool execution visibility.
 */

'use client';

import { use } from 'react';
import { AgentChat } from '@/components';
import { useAgentChat } from '@/lib/hooks';
import type { SuperAgentType } from '@/lib/types';
import { useRouter } from 'next/navigation';

interface AgentChatPageProps {
  params: Promise<{ agent: string }>;
}

export default function AgentChatPage({ params }: AgentChatPageProps) {
  const { agent: agentType } = use(params);
  const router = useRouter();

  const { messages, streaming, sendMessage } = useAgentChat({
    agentType: agentType as SuperAgentType,
    onError: (error) => {
      console.error('Chat error:', error);
    },
  });

  // Validate agent type
  const validAgents: SuperAgentType[] = [
    'commerce',
    'creative',
    'marketing',
    'support',
    'operations',
    'analytics',
  ];

  if (!validAgents.includes(agentType as SuperAgentType)) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Invalid Agent</h1>
          <p className="text-gray-500 mb-4">
            Agent type &quot;{agentType}&quot; is not recognized.
          </p>
          <button
            onClick={() => router.push('/agents')}
            className="px-4 py-2 bg-brand-primary text-white rounded-lg"
          >
            Back to Agents
          </button>
        </div>
      </div>
    );
  }

  return (
    <AgentChat
      agentId={agentType as SuperAgentType}
      messages={messages}
      onSend={sendMessage}
      streaming={streaming}
      status="online"
    />
  );
}
