'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Zap,
  Trophy,
  Clock,
  DollarSign,
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
  Sparkles,
} from 'lucide-react';
import { api, type ProviderInfo, type ProviderStats, type HistoryEntry, type CompetitionResponse } from '@/lib/api';
import { useRoundTableWS } from '@/hooks/useWebSocket';

export default function RoundTablePage() {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [stats, setStats] = useState<ProviderStats[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [competing, setCompeting] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [lastResult, setLastResult] = useState<CompetitionResponse | null>(null);

  const { status: wsStatus, lastMessage } = useRoundTableWS();

  useEffect(() => {
    async function fetchData() {
      try {
        const [providersData, statsData, historyData] = await Promise.all([
          api.roundTable.getProviders(),
          api.roundTable.getStats(),
          api.roundTable.getHistory(10),
        ]);
        setProviders(providersData);
        setStats(statsData);
        setHistory(historyData);
      } catch (err) {
        console.error('Failed to load Round Table data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  useEffect(() => {
    if (lastMessage?.data?.event === 'competition_completed') {
      api.roundTable.getStats().then(setStats);
      api.roundTable.getHistory(10).then(setHistory);
    }
  }, [lastMessage]);

  async function runCompetition() {
    if (!prompt.trim()) return;
    setCompeting(true);
    try {
      const result = await api.roundTable.compete({ prompt: prompt.trim() });
      setLastResult(result);
      setHistory((prev) => [{ ...result, results: result.results } as HistoryEntry, ...prev.slice(0, 9)]);
      const newStats = await api.roundTable.getStats();
      setStats(newStats);
    } catch (err) {
      console.error('Competition failed:', err);
    } finally {
      setCompeting(false);
    }
  }

  if (loading) {
    return <RoundTableSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">LLM Round Table</h1>
          <p className="text-gray-400 mt-1">Compare 6 LLM providers in real-time competitions</p>
        </div>
        <Badge
          variant="outline"
          className={wsStatus === 'connected' ? 'border-green-500 text-green-400' : 'border-yellow-500 text-yellow-400'}
        >
          <div className={`h-2 w-2 rounded-full mr-2 ${wsStatus === 'connected' ? 'bg-green-500' : 'bg-yellow-500'}`} />
          {wsStatus === 'connected' ? 'Live' : 'Connecting...'}
        </Badge>
      </div>

      {/* Competition Form */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-rose-400" />
            Run Competition
          </CardTitle>
          <CardDescription className="text-gray-400">
            Enter a prompt to compete all 6 LLM providers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="prompt" className="text-gray-300">Prompt</Label>
              <Input
                id="prompt"
                placeholder="Enter your prompt for the LLM competition..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="mt-2 bg-gray-800 border-gray-700 text-white placeholder:text-gray-500"
                onKeyDown={(e) => e.key === 'Enter' && !competing && runCompetition()}
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={runCompetition}
                disabled={competing || !prompt.trim()}
                className="bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-600 hover:to-rose-700"
              >
                {competing ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Competing...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Run Competition
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Last Result */}
      {lastResult && (
        <Card className="bg-gray-900 border-gray-800 border-rose-500/50">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-400" />
              Latest Competition Result
            </CardTitle>
            <CardDescription className="text-gray-400">
              Winner: <span className="text-rose-400 font-medium">{lastResult.winner}</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {lastResult.results
                .sort((a, b) => b.score - a.score)
                .map((result, index) => (
                  <div
                    key={result.provider_id}
                    className={`rounded-lg p-4 ${
                      index === 0 ? 'bg-rose-500/10 border border-rose-500/30' : 'bg-gray-800'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-white">{result.provider_id}</span>
                      {index === 0 && <Trophy className="h-4 w-4 text-yellow-400" />}
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Score:</span>
                        <span className="text-white">{result.score.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Latency:</span>
                        <span className="text-white">{result.latency_ms}ms</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Cost:</span>
                        <span className="text-white">${result.cost.toFixed(4)}</span>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="providers" className="space-y-4">
        <TabsList className="bg-gray-800">
          <TabsTrigger value="providers" className="data-[state=active]:bg-gray-700">
            Providers
          </TabsTrigger>
          <TabsTrigger value="stats" className="data-[state=active]:bg-gray-700">
            Statistics
          </TabsTrigger>
          <TabsTrigger value="history" className="data-[state=active]:bg-gray-700">
            History
          </TabsTrigger>
        </TabsList>

        <TabsContent value="providers">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {providers.map((provider) => (
              <Card key={provider.provider_id} className="bg-gray-900 border-gray-800">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg text-white">{provider.name}</CardTitle>
                    <Badge
                      variant="outline"
                      className={
                        provider.status === 'online'
                          ? 'border-green-500 text-green-400'
                          : provider.status === 'degraded'
                          ? 'border-yellow-500 text-yellow-400'
                          : 'border-red-500 text-red-400'
                      }
                    >
                      {provider.status}
                    </Badge>
                  </div>
                  <CardDescription className="text-gray-500">{provider.model}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Cost/1K tokens:</span>
                      <span className="text-white">${provider.cost_per_1k_tokens.toFixed(4)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Avg Latency:</span>
                      <span className="text-white">{provider.avg_latency_ms}ms</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-3">
                      {provider.capabilities.slice(0, 3).map((cap) => (
                        <Badge key={cap} variant="secondary" className="bg-gray-800 text-gray-300 text-xs">
                          {cap}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="stats">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Provider Performance</CardTitle>
              <CardDescription className="text-gray-400">
                Aggregated statistics from all competitions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {stats.map((stat) => (
                  <div key={stat.provider_id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-white">{stat.name}</span>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-gray-400">
                          <Trophy className="inline h-4 w-4 mr-1 text-yellow-400" />
                          {stat.wins} wins
                        </span>
                        <span className="text-gray-400">
                          <Clock className="inline h-4 w-4 mr-1" />
                          {stat.avg_latency_ms}ms avg
                        </span>
                        <span className="text-gray-400">
                          <DollarSign className="inline h-4 w-4 mr-1" />
                          ${stat.total_cost.toFixed(4)} total
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex-1 h-3 rounded-full bg-gray-800 overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-rose-500 to-rose-400"
                          style={{ width: `${stat.win_rate * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-white w-16 text-right">
                        {(stat.win_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
                {stats.length === 0 && (
                  <p className="text-center text-gray-500 py-8">
                    No statistics yet. Run competitions to see provider performance.
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Competition History</CardTitle>
              <CardDescription className="text-gray-400">
                Recent Round Table competitions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {history.map((entry) => (
                  <div key={entry.id} className="rounded-lg bg-gray-800 p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <p className="text-white font-medium line-clamp-2">{entry.prompt}</p>
                        <p className="text-sm text-gray-500 mt-1">
                          {new Date(entry.created_at).toLocaleString()}
                        </p>
                      </div>
                      <Badge className="bg-rose-500/10 text-rose-400 border-rose-500/30">
                        <Trophy className="h-3 w-3 mr-1" />
                        {entry.winner}
                      </Badge>
                    </div>
                  </div>
                ))}
                {history.length === 0 && (
                  <p className="text-center text-gray-500 py-8">
                    No competition history yet. Run your first competition above!
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function RoundTableSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-48 bg-gray-800" />
        <Skeleton className="h-4 w-64 mt-2 bg-gray-800" />
      </div>
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <Skeleton className="h-6 w-40 bg-gray-800" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-full bg-gray-800" />
        </CardContent>
      </Card>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="bg-gray-900 border-gray-800">
            <CardHeader>
              <Skeleton className="h-6 w-32 bg-gray-800" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-20 w-full bg-gray-800" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
