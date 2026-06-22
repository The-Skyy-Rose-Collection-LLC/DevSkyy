'use client';

import { useCallback, useEffect, useState } from 'react';

interface McpTool {
  name: string;
  description?: string;
}

interface ToolResultContent {
  type: string;
  text?: string;
}

export default function McpConsolePage() {
  const [tools, setTools] = useState<McpTool[]>([]);
  const [selected, setSelected] = useState<string>('');
  const [argsText, setArgsText] = useState<string>('{}');
  const [result, setResult] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [loadingTools, setLoadingTools] = useState<boolean>(true);
  const [invoking, setInvoking] = useState<boolean>(false);

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const res = await fetch('/api/mcp', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'list' }),
        });
        const data: { tools?: McpTool[]; error?: string } = await res.json();
        if (!res.ok) throw new Error(data.error ?? 'failed to load tools');
        if (active) {
          setTools(data.tools ?? []);
          if (data.tools?.[0]) setSelected(data.tools[0].name);
        }
      } catch (err: unknown) {
        if (active) setError(err instanceof Error ? err.message : 'failed to load tools');
      } finally {
        if (active) setLoadingTools(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const invoke = useCallback(async () => {
    setError('');
    setResult('');
    let args: Record<string, unknown>;
    try {
      args = argsText.trim() ? (JSON.parse(argsText) as Record<string, unknown>) : {};
    } catch {
      setError('Arguments must be valid JSON.');
      return;
    }
    setInvoking(true);
    try {
      const res = await fetch('/api/mcp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'call', name: selected, args }),
      });
      const data: { result?: { content?: ToolResultContent[] }; error?: string } = await res.json();
      if (!res.ok) throw new Error(data.error ?? 'tool call failed');
      const content = data.result?.content ?? [];
      const text = content
        .map((item) => (item.type === 'text' ? item.text : JSON.stringify(item)))
        .join('\n');
      setResult(text || JSON.stringify(data.result, null, 2));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'tool call failed');
    } finally {
      setInvoking(false);
    }
  }, [argsText, selected]);

  const current = tools.find((tool) => tool.name === selected);

  return (
    <main className="mx-auto max-w-3xl p-6 text-neutral-100">
      <h1 className="mb-1 text-2xl font-semibold">MCP Console</h1>
      <p className="mb-6 text-sm text-neutral-400">
        Invoke any DevSkyy MCP tool over the deployed <code>/mcp</code> endpoint.
      </p>

      {loadingTools ? (
        <p className="text-neutral-400">Loading tools…</p>
      ) : (
        <div className="space-y-4">
          <label className="block">
            <span className="mb-1 block text-sm text-neutral-300">Tool ({tools.length})</span>
            <select
              value={selected}
              onChange={(event) => setSelected(event.target.value)}
              className="w-full rounded border border-neutral-700 bg-neutral-900 p-2"
            >
              {tools.map((tool) => (
                <option key={tool.name} value={tool.name}>
                  {tool.name}
                </option>
              ))}
            </select>
          </label>

          {current?.description && <p className="text-sm text-neutral-400">{current.description}</p>}

          <label className="block">
            <span className="mb-1 block text-sm text-neutral-300">Arguments (JSON)</span>
            <textarea
              value={argsText}
              onChange={(event) => setArgsText(event.target.value)}
              rows={6}
              spellCheck={false}
              className="w-full rounded border border-neutral-700 bg-neutral-900 p-2 font-mono text-sm"
            />
          </label>

          <button
            type="button"
            onClick={() => void invoke()}
            disabled={invoking || !selected}
            className="rounded px-4 py-2 font-medium text-black disabled:opacity-50"
            style={{ backgroundColor: '#B76E79' }}
          >
            {invoking ? 'Invoking…' : 'Invoke'}
          </button>
        </div>
      )}

      {error && (
        <pre className="mt-4 whitespace-pre-wrap rounded border border-red-800 bg-red-950/40 p-3 text-sm text-red-300">
          {error}
        </pre>
      )}
      {result && (
        <pre className="mt-4 max-h-96 overflow-auto whitespace-pre-wrap rounded border border-neutral-700 bg-neutral-900 p-3 text-sm">
          {result}
        </pre>
      )}
    </main>
  );
}
