/**
 * Agents Section
 * ==============
 * Async server component that fetches and displays agents grid.
 */

import { Bot } from 'lucide-react';
import { AgentCard } from '@/components';
import { Button } from '@/components/ui';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function getAgents() {
  try {
    const res = await fetch(`${API_URL}/api/v1/agents`, {
      next: { revalidate: 300 }, // Cache for 5 minutes
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) return [];
    return res.json();
  } catch (error) {
    console.error('Failed to fetch agents:', error);
    return [];
  }
}

export async function AgentsSection() {
  const agents = await getAgents();

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Bot className="h-5 w-5" />
          SuperAgents
        </h2>
        <form action="/agents" method="GET">
          <Button variant="outline" size="sm" type="submit">
            View All
          </Button>
        </form>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agents.length > 0 ? (
          agents.slice(0, 6).map((agent: any) => (
            <AgentCard key={agent.id} agent={agent} onRefresh={() => {}} />
          ))
        ) : (
          <div className="col-span-full text-center py-12 text-gray-500">
            No agents available
          </div>
        )}
      </div>
    </div>
  );
}
