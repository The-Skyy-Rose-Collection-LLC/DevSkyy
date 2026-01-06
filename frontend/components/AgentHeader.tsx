/**
 * AgentHeader Component
 * =====================
 * Header for agent chat interface showing agent status and info.
 */

'use client';

import Link from 'next/link';
import {
  ArrowLeft,
  ShoppingCart,
  Palette,
  Megaphone,
  HeadphonesIcon,
  Settings,
  BarChart3,
  Circle,
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import type { SuperAgentType } from '@/lib/types';

const agentIcons: Record<SuperAgentType, React.ElementType> = {
  commerce: ShoppingCart,
  creative: Palette,
  marketing: Megaphone,
  support: HeadphonesIcon,
  operations: Settings,
  analytics: BarChart3,
};

const agentNames: Record<SuperAgentType, string> = {
  commerce: 'Commerce Agent',
  creative: 'Creative Agent',
  marketing: 'Marketing Agent',
  support: 'Support Agent',
  operations: 'Operations Agent',
  analytics: 'Analytics Agent',
};

const agentDescriptions: Record<SuperAgentType, string> = {
  commerce: 'E-commerce operations and product management',
  creative: '3D generation, images, and visual content',
  marketing: 'Content creation and marketing campaigns',
  support: 'Customer service and ticket management',
  operations: 'DevOps, deployment, and WordPress management',
  analytics: 'Data analysis, reports, and forecasting',
};

interface AgentHeaderProps {
  agentId: SuperAgentType;
  status?: 'online' | 'offline' | 'busy';
}

export function AgentHeader({ agentId, status = 'online' }: AgentHeaderProps) {
  const Icon = agentIcons[agentId];
  const name = agentNames[agentId];
  const description = agentDescriptions[agentId];

  const statusColors = {
    online: 'text-green-500',
    offline: 'text-gray-400',
    busy: 'text-yellow-500',
  };

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/agents">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>

          <div className="flex items-center gap-3">
            <div className="relative">
              <div className={`h-12 w-12 rounded-lg bg-agent-${agentId} bg-opacity-10 flex items-center justify-center`}>
                <Icon className={`h-6 w-6 text-agent-${agentId}`} />
              </div>
              <Circle
                className={`absolute -bottom-1 -right-1 h-4 w-4 fill-current ${statusColors[status]}`}
              />
            </div>

            <div>
              <h1 className="text-xl font-bold">{name}</h1>
              <p className="text-sm text-gray-500">{description}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge
            variant={status === 'online' ? 'success' : status === 'busy' ? 'warning' : 'secondary'}
          >
            {status}
          </Badge>
        </div>
      </div>
    </div>
  );
}
