/**
 * RoundTableViewer Component
 * ==========================
 * Displays the LLM Round Table competition with real-time updates.
 */

'use client';

import { useState } from 'react';
import {
  Trophy,
  Clock,
  DollarSign,
  Sparkles,
  Target,
  Zap,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Crown,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import type {
  RoundTableEntry,
  RoundTableParticipant,
  LLMProvider,
} from '@/lib/types';
import {
  formatDuration,
  formatCurrency,
  formatPercent,
  getProviderDisplayName,
  truncate,
} from '@/lib/utils';

const providerColors: Record<LLMProvider, string> = {
  anthropic: 'bg-llm-anthropic',
  openai: 'bg-llm-openai',
  google: 'bg-llm-google',
  mistral: 'bg-llm-mistral',
  cohere: 'bg-llm-cohere',
  groq: 'bg-llm-groq',
};

const statusLabels = {
  pending: 'Pending',
  collecting: 'Collecting Responses',
  scoring: 'Scoring',
  ab_testing: 'A/B Testing',
  completed: 'Completed',
  failed: 'Failed',
};

interface RoundTableViewerProps {
  entry: RoundTableEntry;
  expanded?: boolean;
}

export function RoundTableViewer({
  entry,
  expanded: initialExpanded = false,
}: RoundTableViewerProps) {
  const [expanded, setExpanded] = useState(initialExpanded);

  const isInProgress =
    entry.status === 'collecting' ||
    entry.status === 'scoring' ||
    entry.status === 'ab_testing';

  return (
    <Card className="relative overflow-hidden">
      {/* Status indicator */}
      <div
        className={`absolute left-0 top-0 h-full w-1 ${
          entry.status === 'completed'
            ? 'bg-green-500'
            : entry.status === 'failed'
              ? 'bg-red-500'
              : 'bg-yellow-500'
        }`}
      />

      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-500" />
            <CardTitle className="text-base">Round Table Competition</CardTitle>
            <Badge
              variant={
                entry.status === 'completed'
                  ? 'success'
                  : entry.status === 'failed'
                    ? 'destructive'
                    : 'warning'
              }
            >
              {statusLabels[entry.status]}
            </Badge>
          </div>
          {entry.winner && (
            <div className="flex items-center gap-2">
              <Crown className="h-4 w-4 text-yellow-500" />
              <Badge variant={entry.winner.provider as LLMProvider}>
                {getProviderDisplayName(entry.winner.provider)}
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Prompt */}
        <div className="space-y-1">
          <p className="text-xs text-gray-500 flex items-center gap-1">
            <MessageSquare className="h-3 w-3" />
            Prompt
          </p>
          <p className="text-sm bg-gray-50 dark:bg-gray-900 rounded-md p-2">
            {truncate(entry.prompt, expanded ? 1000 : 150)}
          </p>
        </div>

        {/* Metrics Summary */}
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-1">
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <Clock className="h-3 w-3" />
              Duration
            </p>
            <p className="font-semibold text-sm">
              {entry.totalDurationMs
                ? formatDuration(entry.totalDurationMs)
                : '-'}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              Total Cost
            </p>
            <p className="font-semibold text-sm">
              {entry.totalCostUsd ? formatCurrency(entry.totalCostUsd) : '-'}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <Sparkles className="h-3 w-3" />
              Participants
            </p>
            <p className="font-semibold text-sm">{entry.participants.length}</p>
          </div>
        </div>

        {/* Progress indicator for in-progress competitions */}
        {isInProgress && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Progress</span>
              <span>
                {entry.status === 'collecting'
                  ? 'Collecting responses...'
                  : entry.status === 'scoring'
                    ? 'Scoring responses...'
                    : 'Running A/B test...'}
              </span>
            </div>
            <Progress
              value={
                entry.status === 'collecting'
                  ? 33
                  : entry.status === 'scoring'
                    ? 66
                    : 90
              }
              className="h-2"
              indicatorClassName="bg-yellow-500"
            />
          </div>
        )}

        {/* Participant Rankings */}
        {entry.participants.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-gray-500 font-medium">Rankings</p>
            <div className="space-y-2">
              {entry.participants
                .sort((a, b) => a.rank - b.rank)
                .slice(0, expanded ? undefined : 3)
                .map((participant, idx) => (
                  <ParticipantRow
                    key={participant.provider}
                    participant={participant}
                    isWinner={entry.winner?.provider === participant.provider}
                    rank={idx + 1}
                  />
                ))}
            </div>
          </div>
        )}

        {/* A/B Test Result */}
        {entry.abTestResult && (
          <div className="border-t pt-4">
            <p className="text-xs text-gray-500 font-medium mb-2">
              A/B Test Result
            </p>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-3 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Winner</span>
                <Badge
                  variant={
                    entry.abTestResult.winner === 'A'
                      ? (entry.abTestResult.variantA.provider as LLMProvider)
                      : (entry.abTestResult.variantB.provider as LLMProvider)
                  }
                >
                  {entry.abTestResult.winner === 'A'
                    ? getProviderDisplayName(
                        entry.abTestResult.variantA.provider
                      )
                    : entry.abTestResult.winner === 'B'
                      ? getProviderDisplayName(
                          entry.abTestResult.variantB.provider
                        )
                      : 'Tie'}
                </Badge>
              </div>
              <div className="flex justify-between text-sm">
                <span>Confidence</span>
                <span className="font-medium">
                  {formatPercent(entry.abTestResult.confidence)}
                </span>
              </div>
              {entry.abTestResult.reasoning && (
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                  {truncate(entry.abTestResult.reasoning, 200)}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Expand/Collapse Button */}
        <Button
          variant="ghost"
          size="sm"
          className="w-full"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <>
              <ChevronUp className="mr-1 h-4 w-4" />
              Show Less
            </>
          ) : (
            <>
              <ChevronDown className="mr-1 h-4 w-4" />
              Show More
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}

interface ParticipantRowProps {
  participant: RoundTableParticipant;
  isWinner: boolean;
  rank: number;
}

function ParticipantRow({ participant, isWinner, rank }: ParticipantRowProps) {
  const [showResponse, setShowResponse] = useState(false);

  return (
    <div
      className={`rounded-md border p-2 ${
        isWinner ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20' : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-gray-400">#{rank}</span>
          <div
            className={`h-2 w-2 rounded-full ${providerColors[participant.provider]}`}
          />
          <span className="font-medium text-sm">
            {getProviderDisplayName(participant.provider)}
          </span>
          {isWinner && <Crown className="h-4 w-4 text-yellow-500" />}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <Target className="h-3 w-3" />
            {(participant.scores.overall * 100).toFixed(0)}
          </span>
          <span className="flex items-center gap-1">
            <Zap className="h-3 w-3" />
            {formatDuration(participant.latencyMs)}
          </span>
          <span className="flex items-center gap-1">
            <DollarSign className="h-3 w-3" />
            {formatCurrency(participant.costUsd)}
          </span>
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="grid grid-cols-4 gap-2 mt-2 text-xs">
        <div>
          <span className="text-gray-500">Relevance</span>
          <Progress
            value={participant.scores.relevance * 100}
            className="h-1 mt-1"
          />
        </div>
        <div>
          <span className="text-gray-500">Coherence</span>
          <Progress
            value={participant.scores.coherence * 100}
            className="h-1 mt-1"
          />
        </div>
        <div>
          <span className="text-gray-500">Complete</span>
          <Progress
            value={participant.scores.completeness * 100}
            className="h-1 mt-1"
          />
        </div>
        <div>
          <span className="text-gray-500">Creative</span>
          <Progress
            value={participant.scores.creativity * 100}
            className="h-1 mt-1"
          />
        </div>
      </div>

      {/* Response Preview */}
      <Button
        variant="ghost"
        size="sm"
        className="mt-2 w-full text-xs"
        onClick={() => setShowResponse(!showResponse)}
      >
        {showResponse ? 'Hide Response' : 'Show Response'}
      </Button>
      {showResponse && (
        <div className="mt-2 text-xs bg-white dark:bg-gray-950 rounded p-2 max-h-40 overflow-y-auto">
          {participant.response}
        </div>
      )}
    </div>
  );
}
