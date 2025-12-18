/**
 * Tools Library Page
 * ==================
 * Browse and test all available tools across SuperAgents.
 */

'use client';

import { useState } from 'react';
import {
  Wrench,
  Search,
  Play,
  Filter,
  CheckCircle,
  XCircle,
  Loader2,
  Code,
  Copy,
  Check,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  Button,
  Badge,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui';
import { useTools, useTestTool } from '@/lib/hooks';
import type { ToolInfo, SuperAgentType } from '@/lib/types';

const categories = [
  'all',
  'commerce',
  'creative',
  'marketing',
  'support',
  'operations',
  'analytics',
];

export default function ToolsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [selectedTool, setSelectedTool] = useState<ToolInfo | null>(null);

  const { data: tools, isLoading } = useTools();

  const filteredTools = tools?.filter((tool) => {
    const matchesSearch =
      tool.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory =
      categoryFilter === 'all' || tool.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const groupedTools = filteredTools?.reduce(
    (acc, tool) => {
      if (!acc[tool.category]) acc[tool.category] = [];
      acc[tool.category].push(tool);
      return acc;
    },
    {} as Record<string, ToolInfo[]>
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Wrench className="h-8 w-8" />
            Tool Library
          </h1>
          <p className="text-gray-500 mt-1">
            Browse and test all {tools?.length || 0}+ tools available to SuperAgents
          </p>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search tools..."
            className="w-full pl-10 pr-4 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-transparent focus:outline-none focus:ring-2 focus:ring-brand-primary"
          />
        </div>
        <div className="flex gap-2">
          {categories.map((cat) => (
            <Button
              key={cat}
              variant={categoryFilter === cat ? 'default' : 'outline'}
              size="sm"
              onClick={() => setCategoryFilter(cat)}
            >
              {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </Button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Tools List */}
        <div className="lg:col-span-2 space-y-6">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Card key={i} className="h-[200px] animate-pulse bg-gray-100 dark:bg-gray-800" />
            ))
          ) : Object.keys(groupedTools || {}).length === 0 ? (
            <Card className="p-8 text-center">
              <Wrench className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500">No tools found</p>
            </Card>
          ) : (
            Object.entries(groupedTools || {}).map(([category, categoryTools]) => (
              <div key={category}>
                <h2 className="text-lg font-bold mb-3 flex items-center gap-2">
                  <div className={`h-3 w-3 rounded-full bg-agent-${category}`} />
                  {category.charAt(0).toUpperCase() + category.slice(1)} Tools
                  <Badge variant="secondary">{categoryTools.length}</Badge>
                </h2>
                <div className="grid gap-3 md:grid-cols-2">
                  {categoryTools.map((tool) => (
                    <Card
                      key={tool.name}
                      className={`cursor-pointer transition-all hover:shadow-md ${
                        selectedTool?.name === tool.name
                          ? 'ring-2 ring-brand-primary'
                          : ''
                      }`}
                      onClick={() => setSelectedTool(tool)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium">{tool.name}</h3>
                          <Badge variant="outline" className="text-xs">
                            {tool.parameters.length} params
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-500 line-clamp-2">
                          {tool.description}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Tool Detail / Tester */}
        <div className="lg:col-span-1">
          {selectedTool ? (
            <ToolTester tool={selectedTool} />
          ) : (
            <Card className="sticky top-8">
              <CardContent className="p-8 text-center">
                <Wrench className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-500">Select a tool to view details and test</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

interface ToolTesterProps {
  tool: ToolInfo;
}

function ToolTester({ tool }: ToolTesterProps) {
  const [params, setParams] = useState<Record<string, string>>({});
  const [copied, setCopied] = useState(false);
  const { trigger: testTool, isMutating, data: result } = useTestTool();

  const handleTest = async () => {
    const parsedParams: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(params)) {
      try {
        parsedParams[key] = JSON.parse(value);
      } catch {
        parsedParams[key] = value;
      }
    }
    await testTool({ toolName: tool.name, parameters: parsedParams });
  };

  const copyCode = () => {
    const code = `# Using ${tool.name}
await agent.use_tool("${tool.name}", {
${tool.parameters.map((p) => `    "${p.name}": ${p.type === 'string' ? `"value"` : 'value'}`).join(',\n')}
})`;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="sticky top-8">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>{tool.name}</span>
          <Badge variant={tool.category as SuperAgentType}>{tool.category}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-gray-500">{tool.description}</p>

        {/* Parameters */}
        <div className="space-y-3">
          <h4 className="font-medium text-sm">Parameters</h4>
          {tool.parameters.length === 0 ? (
            <p className="text-sm text-gray-500">No parameters required</p>
          ) : (
            tool.parameters.map((param) => (
              <div key={param.name} className="space-y-1">
                <label className="text-sm flex items-center gap-2">
                  {param.name}
                  <Badge
                    variant={param.required ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    {param.type}
                  </Badge>
                  {param.required && (
                    <span className="text-red-500 text-xs">*</span>
                  )}
                </label>
                <input
                  type="text"
                  value={params[param.name] || ''}
                  onChange={(e) =>
                    setParams({ ...params, [param.name]: e.target.value })
                  }
                  placeholder={param.description}
                  className="w-full px-3 py-2 text-sm rounded-md border border-gray-300 dark:border-gray-700 bg-transparent focus:outline-none focus:ring-2 focus:ring-brand-primary"
                />
              </div>
            ))
          )}
        </div>

        {/* Code Example */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="font-medium text-sm">Code Example</h4>
            <Button variant="ghost" size="sm" onClick={copyCode}>
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
          <pre className="bg-gray-100 dark:bg-gray-900 rounded-md p-3 text-xs overflow-x-auto">
            <code>{`await agent.use_tool("${tool.name}", {
${tool.parameters.map((p) => `  "${p.name}": ...`).join(',\n')}
})`}</code>
          </pre>
        </div>

        {/* Test Result */}
        {result && (
          <div className="space-y-2">
            <h4 className="font-medium text-sm flex items-center gap-2">
              Result
              {result.error ? (
                <XCircle className="h-4 w-4 text-red-500" />
              ) : (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
            </h4>
            <pre
              className={`rounded-md p-3 text-xs overflow-x-auto ${
                result.error
                  ? 'bg-red-50 dark:bg-red-900/20 text-red-600'
                  : 'bg-green-50 dark:bg-green-900/20 text-green-600'
              }`}
            >
              {result.error || JSON.stringify(result.result, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button onClick={handleTest} disabled={isMutating} className="w-full">
          {isMutating ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Testing...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4" />
              Test Tool
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
