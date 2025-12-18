/**
 * TaskExecutor Component
 * ======================
 * Form for submitting tasks to SuperAgents.
 */

'use client';

import { useState } from 'react';
import {
  Send,
  Loader2,
  CheckCircle,
  XCircle,
  Trophy,
  Settings2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import type { SuperAgentType, TaskCategory, TaskResponse } from '@/lib/types';
import { useSubmitTask } from '@/lib/hooks';
import { getAgentDisplayName, formatDuration, formatCurrency } from '@/lib/utils';

const agentTypes: SuperAgentType[] = [
  'commerce',
  'creative',
  'marketing',
  'support',
  'operations',
  'analytics',
];

const taskCategories: TaskCategory[] = [
  'reasoning',
  'classification',
  'creative',
  'search',
  'qa',
  'extraction',
  'moderation',
  'generation',
  'analysis',
];

interface TaskExecutorProps {
  defaultAgent?: SuperAgentType;
  onTaskComplete?: (response: TaskResponse) => void;
}

export function TaskExecutor({
  defaultAgent,
  onTaskComplete,
}: TaskExecutorProps) {
  const [prompt, setPrompt] = useState('');
  const [agentType, setAgentType] = useState<SuperAgentType>(
    defaultAgent || 'commerce'
  );
  const [category, setCategory] = useState<TaskCategory | ''>('');
  const [useRoundTable, setUseRoundTable] = useState(false);
  const [showOptions, setShowOptions] = useState(false);
  const [result, setResult] = useState<TaskResponse | null>(null);

  const { trigger, isMutating } = useSubmitTask();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isMutating) return;

    try {
      const response = await trigger({
        agentType,
        prompt: prompt.trim(),
        category: category || undefined,
        useRoundTable,
      });
      setResult(response);
      onTaskComplete?.(response);
    } catch (error) {
      console.error('Task submission failed:', error);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Send className="h-5 w-5" />
          Execute Task
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Agent Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Agent</label>
            <div className="flex flex-wrap gap-2">
              {agentTypes.map((type) => (
                <Button
                  key={type}
                  type="button"
                  variant={agentType === type ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setAgentType(type)}
                >
                  {getAgentDisplayName(type).replace(' Agent', '')}
                </Button>
              ))}
            </div>
          </div>

          {/* Prompt Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your task or question..."
              className="w-full min-h-[100px] rounded-md border border-gray-300 dark:border-gray-700 bg-transparent px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-primary"
              disabled={isMutating}
            />
          </div>

          {/* Advanced Options Toggle */}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowOptions(!showOptions)}
          >
            <Settings2 className="mr-1 h-4 w-4" />
            {showOptions ? 'Hide Options' : 'Show Options'}
          </Button>

          {/* Advanced Options */}
          {showOptions && (
            <div className="space-y-4 border-t pt-4">
              {/* Task Category */}
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Task Category (Optional)
                </label>
                <div className="flex flex-wrap gap-2">
                  {taskCategories.map((cat) => (
                    <Button
                      key={cat}
                      type="button"
                      variant={category === cat ? 'secondary' : 'outline'}
                      size="sm"
                      onClick={() => setCategory(category === cat ? '' : cat)}
                    >
                      {cat}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Round Table Option */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="roundTable"
                  checked={useRoundTable}
                  onChange={(e) => setUseRoundTable(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <label htmlFor="roundTable" className="text-sm">
                  <Trophy className="inline h-4 w-4 mr-1 text-yellow-500" />
                  Use LLM Round Table (all providers compete)
                </label>
              </div>
            </div>
          )}
        </form>
      </CardContent>

      <CardFooter className="flex-col gap-4">
        {/* Submit Button */}
        <Button
          onClick={handleSubmit}
          disabled={!prompt.trim() || isMutating}
          className="w-full"
        >
          {isMutating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Send className="mr-2 h-4 w-4" />
              Execute Task
            </>
          )}
        </Button>

        {/* Result Display */}
        {result && (
          <div className="w-full border-t pt-4">
            <div className="flex items-center gap-2 mb-2">
              {result.status === 'completed' ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : result.status === 'failed' ? (
                <XCircle className="h-5 w-5 text-red-500" />
              ) : (
                <Loader2 className="h-5 w-5 animate-spin" />
              )}
              <span className="font-medium">
                Task {result.status}
              </span>
              <Badge variant="secondary">{result.taskId}</Badge>
            </div>

            {result.metrics && (
              <div className="flex gap-4 text-sm text-gray-500 mb-2">
                {result.metrics.durationMs && (
                  <span>Duration: {formatDuration(result.metrics.durationMs)}</span>
                )}
                {result.metrics.costUsd && (
                  <span>Cost: {formatCurrency(result.metrics.costUsd)}</span>
                )}
                {result.metrics.provider && (
                  <span>Provider: {result.metrics.provider}</span>
                )}
              </div>
            )}

            {result.result !== undefined && result.result !== null && (
              <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-3 text-sm max-h-60 overflow-y-auto">
                <pre className="whitespace-pre-wrap">
                  {String(
                    typeof result.result === 'string'
                      ? result.result
                      : JSON.stringify(result.result, null, 2)
                  )}
                </pre>
              </div>
            )}

            {result.error && (
              <div className="bg-red-50 dark:bg-red-900/20 rounded-md p-3 text-sm text-red-600 dark:text-red-400">
                {result.error}
              </div>
            )}
          </div>
        )}
      </CardFooter>
    </Card>
  );
}
