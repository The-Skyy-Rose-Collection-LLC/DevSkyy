'use client';

import { useState } from 'react';
import {
  Activity,
  Users,
  Plug,
  Cpu,
  ShieldCheck,
  Brain,
  Sparkles,
  Store,
  MousePointerClick,
  UsersRound,
  Terminal,
  TrendingUp,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { StatsCard } from '@/components/dashboard/StatsCard';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  ResponsiveContainer,
} from 'recharts';

/*--------------------------------------------------------------
 * Mock Data (replace with API calls to /api/experience/*)
 *--------------------------------------------------------------*/

const dailyEvents = [
  { date: 'Mar 7', events: 2100 },
  { date: 'Mar 8', events: 2800 },
  { date: 'Mar 9', events: 3200 },
  { date: 'Mar 10', events: 2900 },
  { date: 'Mar 11', events: 4100 },
  { date: 'Mar 12', events: 3800 },
  { date: 'Mar 13', events: 4600 },
  { date: 'Mar 14', events: 5100 },
  { date: 'Mar 15', events: 4200 },
  { date: 'Mar 16', events: 4800 },
  { date: 'Mar 17', events: 5500 },
  { date: 'Mar 18', events: 6200 },
  { date: 'Mar 19', events: 5800 },
  { date: 'Mar 20', events: 6420 },
  { date: 'Mar 21', events: 7100 },
];

const collectionEngagement = [
  { collection: 'Love Hurts', engagement: 92, fill: '#DC143C' },
  { collection: 'Black Rose', engagement: 84, fill: '#C0C0C0' },
  { collection: 'Signature', engagement: 61, fill: '#D4AF37' },
  { collection: 'Kids Capsule', engagement: 38, fill: '#FFB6C1' },
];

const areaChartConfig: ChartConfig = {
  events: { label: 'Events', color: '#B76E79' },
};

const barChartConfig: ChartConfig = {
  engagement: { label: 'Engagement %' },
};

interface Module {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  priority: number;
  iconColor: string;
  iconBg: string;
}

const modules: Module[] = [
  {
    id: 'performance_guardian',
    name: 'Performance Guardian',
    description: 'Auto-throttles animations based on client framerate drops.',
    icon: ShieldCheck,
    priority: 1,
    iconColor: 'text-emerald-400',
    iconBg: 'bg-emerald-500/10 border-emerald-500/20',
  },
  {
    id: 'experience_analyzer',
    name: 'Experience Analyzer',
    description: 'Behavioral tracking — scroll, hover, click, exit intent.',
    icon: Brain,
    priority: 2,
    iconColor: 'text-blue-400',
    iconBg: 'bg-blue-500/10 border-blue-500/20',
  },
  {
    id: 'brand_atmosphere',
    name: 'Brand Atmosphere',
    description: 'Canvas particles per collection — petals, embers, gold dust.',
    icon: Sparkles,
    priority: 3,
    iconColor: 'text-rose-400',
    iconBg: 'bg-rose-500/10 border-rose-500/20',
  },
  {
    id: 'smart_showcase',
    name: 'Smart Showcase',
    description: 'Quick-view dialog for product cards with size selection.',
    icon: Store,
    priority: 4,
    iconColor: 'text-amber-400',
    iconBg: 'bg-amber-500/10 border-amber-500/20',
  },
  {
    id: 'micro_interactions',
    name: 'Micro-Interactions',
    description: 'Cart fly-to, wishlist burst, CTA magnetism.',
    icon: MousePointerClick,
    priority: 5,
    iconColor: 'text-purple-400',
    iconBg: 'bg-purple-500/10 border-purple-500/20',
  },
  {
    id: 'personalization',
    name: 'Personalization',
    description: 'Collection affinity scoring and Curated For You section.',
    icon: UsersRound,
    priority: 6,
    iconColor: 'text-cyan-400',
    iconBg: 'bg-cyan-500/10 border-cyan-500/20',
  },
];

interface Directive {
  id: string;
  summary: string;
  status: 'accepted' | 'pending' | 'conflict';
  module: string;
  time: string;
}

const directives: Directive[] = [
  {
    id: '1',
    summary: 'Harden edges on core collection.',
    status: 'accepted',
    module: 'Atmosphere',
    time: '10:42 AM',
  },
  {
    id: '2',
    summary: 'Pre-load structural assets for returning users.',
    status: 'pending',
    module: 'Guardian',
    time: '09:15 AM',
  },
  {
    id: '3',
    summary: 'Override typography to serif on mobile.',
    status: 'conflict',
    module: 'Showcase',
    time: 'Yesterday',
  },
];

/*--------------------------------------------------------------
 * Page Component
 *--------------------------------------------------------------*/

export default function ExperiencePage() {
  const [moduleStates, setModuleStates] = useState<Record<string, boolean>>(
    Object.fromEntries(modules.map((m) => [m.id, true]))
  );
  const [narrativeText, setNarrativeText] = useState('');

  const toggleModule = (id: string) => {
    setModuleStates((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const activeCount = Object.values(moduleStates).filter(Boolean).length;

  return (
    <div className="flex flex-col gap-8 max-w-[1600px]">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-rose-400 font-mono text-xs tracking-wider uppercase bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
              System Core
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white mb-2">
            Experience Engine
          </h1>
          <p className="text-sm text-gray-400 max-w-xl font-light">
            Real-time UX orchestration for SkyyRose digital properties.
          </p>
        </div>
        <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-gray-900/50 border border-gray-800 backdrop-blur-md">
          <div className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-400" />
          </div>
          <span className="text-xs font-mono text-gray-300">v1.0.0</span>
        </div>
      </div>

      {/* Section 1: Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatsCard
          title="Total Events"
          value="4.89M"
          description="30-day behavioral events"
          icon={Activity}
          trend="+14.2%"
          trendDirection="up"
        />
        <StatsCard
          title="Unique Visitors"
          value="12,482"
          description="Anonymous visitor hashes"
          icon={Users}
          trend="+8.1%"
          trendDirection="up"
        />
        <StatsCard
          title="FastAPI Status"
          value="Connected"
          description="devskyy.app"
          icon={Plug}
          trend="Online"
          trendDirection="up"
        />
        <StatsCard
          title="Active Modules"
          value={`${activeCount}/6`}
          description="Modules loaded"
          icon={Cpu}
          trendDirection="neutral"
        />
      </div>

      {/* Section 2: Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Area Chart */}
        <Card className="lg:col-span-8 bg-gray-900/50 border-gray-800 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-lg text-white">Interaction Velocity</CardTitle>
            <CardDescription className="font-mono text-xs">
              30-day cumulative behavioral actions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={areaChartConfig} className="h-[250px] w-full">
              <AreaChart data={dailyEvents} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="roseGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#B76E79" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#B76E79" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                  axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#6b7280', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Area
                  type="monotone"
                  dataKey="events"
                  stroke="#B76E79"
                  strokeWidth={2}
                  fill="url(#roseGradient)"
                />
              </AreaChart>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Bar Chart — Collection Engagement */}
        <Card className="lg:col-span-4 bg-gray-900/50 border-gray-800 backdrop-blur-xl">
          <CardHeader>
            <CardTitle className="text-lg text-white">Collection Engagement</CardTitle>
            <CardDescription className="font-mono text-xs">
              Dwell time &amp; interaction density
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={barChartConfig} className="h-[250px] w-full">
              <BarChart
                data={collectionEngagement}
                layout="vertical"
                margin={{ top: 0, right: 20, left: 0, bottom: 0 }}
              >
                <CartesianGrid horizontal={false} stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="collection"
                  tick={{ fill: '#d1d5db', fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                  width={100}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="engagement" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Section 3: Module Control Grid */}
      <div>
        <div className="flex items-center gap-3 mb-6 border-b border-gray-800 pb-3">
          <h2 className="text-xl font-bold text-white">Orchestration Layers</h2>
          <Badge variant="secondary" className="font-mono text-[10px]">
            Live Configuration
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {modules.map((mod) => {
            const Icon = mod.icon;
            const isActive = moduleStates[mod.id];
            return (
              <Card
                key={mod.id}
                className={`bg-gray-900/30 border-gray-800 transition-all duration-300 hover:shadow-[0_0_20px_-5px_rgba(183,110,121,0.25)] hover:border-rose-500/40 ${
                  !isActive ? 'opacity-50' : ''
                }`}
              >
                <CardContent className="p-5">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-start gap-4">
                      <div
                        className={`w-10 h-10 rounded-lg border flex items-center justify-center ${mod.iconBg}`}
                      >
                        <Icon className={`h-5 w-5 ${mod.iconColor}`} />
                      </div>
                      <div>
                        <h4 className="font-bold text-sm text-gray-100">{mod.name}</h4>
                        <p className="text-xs text-gray-500 mt-1 font-light leading-relaxed">
                          {mod.description}
                        </p>
                      </div>
                    </div>
                    <Badge
                      variant="outline"
                      className="font-mono text-[10px] border-gray-700 text-gray-400"
                    >
                      P-{mod.priority}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-gray-800">
                    <div className="flex items-center gap-1.5 text-xs font-mono text-gray-400">
                      <div
                        className={`w-1.5 h-1.5 rounded-full ${
                          isActive ? 'bg-emerald-500' : 'bg-gray-600'
                        }`}
                      />
                      {isActive ? 'Active' : 'Suspended'}
                    </div>
                    <Switch
                      checked={isActive}
                      onCheckedChange={() => toggleModule(mod.id)}
                      className="data-[state=checked]:bg-rose-500"
                    />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Section 4 + 5: Narrative + Performance */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        {/* Design Narrative Panel */}
        <Card className="xl:col-span-8 bg-gray-900/50 border-gray-800 backdrop-blur-xl">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-lg text-white flex items-center gap-2">
                <Terminal className="h-4 w-4 text-rose-400" />
                Narrative Directives
              </CardTitle>
              <Badge variant="secondary" className="font-mono text-[10px]">
                AI Agent: Active
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            {/* Input */}
            <div className="relative rounded-xl border border-gray-700 bg-gray-950 p-1 focus-within:border-rose-500/40 focus-within:shadow-[0_0_20px_-5px_rgba(183,110,121,0.25)] transition-all">
              <Textarea
                value={narrativeText}
                onChange={(e) => setNarrativeText(e.target.value)}
                placeholder="// Enter brand tonal shifts... e.g. 'Increase visual tension for Love Hurts visitors by intensifying shadow depth.'"
                className="bg-transparent border-0 font-mono text-sm text-gray-200 placeholder-gray-600 resize-none focus-visible:ring-0"
                rows={3}
              />
              <div className="flex justify-end px-3 pb-2">
                <button className="bg-rose-500/10 text-rose-400 hover:bg-rose-500 hover:text-white border border-rose-500/30 px-4 py-1.5 rounded-md text-xs font-bold uppercase tracking-wider transition-all duration-200">
                  Inject Directive
                </button>
              </div>
            </div>

            {/* Directive History */}
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-800 text-[10px] uppercase font-mono text-gray-500 tracking-wider">
                    <th className="pb-3 px-2 font-medium">Status</th>
                    <th className="pb-3 px-2 font-medium">Directive</th>
                    <th className="pb-3 px-2 font-medium text-center">Module</th>
                    <th className="pb-3 px-2 font-medium text-right">Time</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  {directives.map((d) => {
                    const statusStyles = {
                      accepted:
                        'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
                      pending:
                        'text-amber-400 bg-amber-400/10 border-amber-400/20',
                      conflict:
                        'text-red-400 bg-red-400/10 border-red-400/20',
                    };
                    return (
                      <tr
                        key={d.id}
                        className="border-b border-gray-800/50 hover:bg-white/[0.02] transition-colors"
                      >
                        <td className="py-3 px-2">
                          <span
                            className={`inline-flex items-center gap-1.5 text-[10px] font-mono font-medium px-2 py-1 rounded border capitalize ${statusStyles[d.status]}`}
                          >
                            <div
                              className={`w-1.5 h-1.5 rounded-full ${
                                d.status === 'accepted'
                                  ? 'bg-emerald-400'
                                  : d.status === 'pending'
                                  ? 'bg-amber-400'
                                  : 'bg-red-400'
                              }`}
                            />
                            {d.status}
                          </span>
                        </td>
                        <td
                          className={`py-3 px-2 text-gray-300 font-medium truncate max-w-[200px] ${
                            d.status === 'conflict' ? 'line-through decoration-red-400/50' : ''
                          }`}
                        >
                          {d.summary}
                        </td>
                        <td className="py-3 px-2 text-center text-xs text-gray-400">
                          {d.module}
                        </td>
                        <td className="py-3 px-2 text-right text-xs font-mono text-gray-500">
                          {d.time}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Performance Guardian Metrics */}
        <div className="xl:col-span-4 flex flex-col gap-5">
          <Card className="bg-gray-900/50 border-gray-800 backdrop-blur-xl">
            <CardHeader className="pb-2">
              <CardTitle className="text-lg text-white">Guardian Telemetry</CardTitle>
              <CardDescription className="font-mono text-xs">
                Live client-side performance
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {/* Animation Budget */}
              <div className="bg-gray-950 rounded-xl border border-gray-800 p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">
                    Anim Budget
                  </div>
                  <div className="text-xl font-bold font-mono text-white">
                    60<span className="text-gray-500 text-sm">%</span>
                  </div>
                </div>
                <div className="relative w-12 h-12">
                  <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-white/10"
                      strokeWidth="4"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className="text-rose-400"
                      strokeDasharray="60, 100"
                      strokeWidth="4"
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono text-gray-300">
                    3/5
                  </span>
                </div>
              </div>

              {/* FPS */}
              <div className="bg-gray-950 rounded-xl border border-gray-800 p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1 flex items-center gap-1.5">
                    Client FPS
                    <TrendingUp className="h-3 w-3 text-emerald-400" />
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold font-mono text-emerald-400">118</span>
                    <span className="text-gray-500 font-mono text-xs">/120</span>
                  </div>
                </div>
                <div className="flex items-end gap-1 h-8">
                  <div className="w-1.5 h-4 bg-emerald-500/40 rounded-t-sm" />
                  <div className="w-1.5 h-6 bg-emerald-500/60 rounded-t-sm" />
                  <div className="w-1.5 h-8 bg-emerald-400 rounded-t-sm shadow-[0_0_5px_rgba(52,211,153,0.5)]" />
                  <div className="w-1.5 h-7 bg-emerald-400 rounded-t-sm" />
                </div>
              </div>

              {/* CLS */}
              <div className="bg-gray-950 rounded-xl border border-gray-800 p-4">
                <div className="flex justify-between items-center mb-3">
                  <div className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
                    Layout Shift (CLS)
                  </div>
                  <span className="text-lg font-bold font-mono text-amber-400">0.04</span>
                </div>
                <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden flex">
                  <div className="h-full bg-emerald-500" style={{ width: '10%' }} />
                  <div className="h-full bg-amber-400" style={{ width: '15%' }} />
                  <div className="h-full bg-red-500" style={{ width: '75%' }} />
                </div>
                <div className="relative mt-1 h-3">
                  <div
                    className="absolute top-0 w-0.5 h-2 bg-white shadow-[0_0_5px_white]"
                    style={{ left: '16%' }}
                  />
                  <span
                    className="absolute top-2 text-[8px] font-mono text-gray-500 -translate-x-1/2"
                    style={{ left: '16%' }}
                  >
                    Current
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
