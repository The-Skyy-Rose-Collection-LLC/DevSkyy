/**
 * Command Palette Component
 * ==========================
 * Full-featured command palette with search, keyboard navigation, and recent commands.
 */

'use client';

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Search, Clock, Command as CommandIcon } from 'lucide-react';
import { Card } from '@/components/ui';
import { useCommandPalette } from '@/lib/hooks/useCommandPalette';
import type { Command } from '@/lib/commands';

interface CommandPaletteProps {
  commands: Command[];
  onCommandExecute?: (commandId: string) => void;
}

function searchCommands(commands: Command[], query: string): Command[] {
  const lowerQuery = query.toLowerCase().trim();
  return commands.filter((cmd) => {
    const searchableText = [cmd.label, cmd.description, ...(cmd.keywords || [])].join(' ').toLowerCase();
    return searchableText.includes(lowerQuery);
  });
}

function groupCommandsByCategory(commands: Command[]): Record<string, Command[]> {
  const groups: Record<string, Command[]> = {};
  commands.forEach((cmd) => {
    const category = cmd.category || 'Other';
    if (!groups[category]) groups[category] = [];
    groups[category].push(cmd);
  });
  return groups;
}

export function CommandPalette({ commands, onCommandExecute }: CommandPaletteProps) {
  const { isOpen, close, recentCommands, executeCommand, clearRecentCommands } = useCommandPalette();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const filteredCommands = useMemo(() => {
    if (!searchQuery.trim()) return commands;
    return searchCommands(commands, searchQuery);
  }, [commands, searchQuery]);

  const groupedCommands = useMemo(() => groupCommandsByCategory(filteredCommands), [filteredCommands]);

  const recentCommandObjects = useMemo(() => {
    return recentCommands
      .map((id) => commands.find((cmd) => cmd.id === id))
      .filter((cmd): cmd is Command => cmd !== undefined)
      .slice(0, 3);
  }, [recentCommands, commands]);

  const handleCommandSelect = useCallback(
    async (command: Command) => {
      await executeCommand(command.id, commands);
      onCommandExecute?.(command.id);
    },
    [executeCommand, commands, onCommandExecute]
  );

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
      setSearchQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      const totalCommands = filteredCommands.length;
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % totalCommands);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + totalCommands) % totalCommands);
      } else if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
        e.preventDefault();
        handleCommandSelect(filteredCommands[selectedIndex]);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex, handleCommandSelect]);

  useEffect(() => {
    if (!isOpen) return;
    const selectedElement = listRef.current?.querySelector(`[data-index="${selectedIndex}"]`);
    selectedElement?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }, [selectedIndex, isOpen]);

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" onClick={close} />
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
        <Card className="w-full max-w-2xl mx-4 shadow-2xl overflow-hidden">
          <div className="flex items-center gap-3 p-4 border-b">
            <Search className="h-5 w-5 text-gray-400" />
            <input
              ref={inputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Type a command or search..."
              className="flex-1 bg-transparent border-none outline-none text-sm"
            />
            <kbd className="hidden sm:inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-500 bg-gray-100 dark:bg-gray-800 rounded">
              <CommandIcon className="h-3 w-3" />K
            </kbd>
          </div>
          <div ref={listRef} className="max-h-[400px] overflow-y-auto overscroll-contain">
            {!searchQuery && recentCommandObjects.length > 0 && (
              <div className="p-2">
                <div className="flex items-center justify-between px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  <div className="flex items-center gap-2">
                    <Clock className="h-3 w-3" />
                    Recent
                  </div>
                  <button onClick={clearRecentCommands} className="text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400">
                    Clear
                  </button>
                </div>
                <div className="space-y-1">
                  {recentCommandObjects.map((cmd, index) => (
                    <button
                      key={cmd.id}
                      data-index={index}
                      onClick={() => handleCommandSelect(cmd)}
                      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                        index === selectedIndex && !searchQuery ? 'bg-blue-50 dark:bg-blue-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                      }`}
                    >
                      <span className="text-lg">{cmd.icon}</span>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium">{cmd.label}</div>
                        <div className="text-xs text-gray-500 truncate">{cmd.description}</div>
                      </div>
                      {cmd.shortcut && <kbd className="px-2 py-1 text-xs text-gray-500 bg-gray-100 dark:bg-gray-800 rounded">{cmd.shortcut}</kbd>}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {Object.entries(groupedCommands).map(([category, categoryCommands]) => (
              <div key={category} className="p-2">
                <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wide">{category}</div>
                <div className="space-y-1">
                  {categoryCommands.map((cmd) => {
                    const globalIndex = filteredCommands.indexOf(cmd);
                    return (
                      <button
                        key={cmd.id}
                        data-index={globalIndex}
                        onClick={() => handleCommandSelect(cmd)}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                          globalIndex === selectedIndex ? 'bg-blue-50 dark:bg-blue-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                        }`}
                      >
                        <span className="text-lg">{cmd.icon}</span>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium">{cmd.label}</div>
                          <div className="text-xs text-gray-500 truncate">{cmd.description}</div>
                        </div>
                        {cmd.shortcut && <kbd className="px-2 py-1 text-xs text-gray-500 bg-gray-100 dark:bg-gray-800 rounded">{cmd.shortcut}</kbd>}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
            {filteredCommands.length === 0 && (
              <div className="p-8 text-center">
                <Search className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                <p className="text-sm text-gray-500">No commands found</p>
                <p className="text-xs text-gray-400 mt-1">Try a different search term</p>
              </div>
            )}
          </div>
          <div className="flex items-center justify-between px-4 py-2 border-t bg-gray-50 dark:bg-gray-800/50 text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-800 rounded">↑</kbd>
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-800 rounded">↓</kbd>
                Navigate
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-800 rounded">↵</kbd>
                Execute
              </span>
              <span className="flex items-center gap-1">
                <kbd className="px-1.5 py-0.5 bg-white dark:bg-gray-800 rounded">Esc</kbd>
                Close
              </span>
            </div>
            <span>{filteredCommands.length} commands</span>
          </div>
        </Card>
      </div>
    </>
  );
}
