/**
 * useCommandPalette Hook
 * ======================
 * State management for Command Palette (Cmd+K).
 * Handles open/close, recent commands, keyboard shortcuts, and command execution.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import type { Command } from '@/lib/commands';

const RECENT_COMMANDS_KEY = 'devskyy-recent-commands';
const MAX_RECENT_COMMANDS = 5;

export interface UseCommandPaletteReturn {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  recentCommands: string[];
  executeCommand: (commandId: string, commands: Command[]) => Promise<void>;
  clearRecentCommands: () => void;
}

export function useCommandPalette(): UseCommandPaletteReturn {
  const [isOpen, setIsOpen] = useState(false);
  const [recentCommands, setRecentCommands] = useState<string[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(RECENT_COMMANDS_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
          setRecentCommands(parsed.slice(0, MAX_RECENT_COMMANDS));
        }
      }
    } catch (error) {
      console.error('Failed to load recent commands:', error);
    }
  }, []);

  const saveRecentCommands = useCallback((commands: string[]) => {
    try {
      localStorage.setItem(RECENT_COMMANDS_KEY, JSON.stringify(commands));
    } catch (error) {
      console.error('Failed to save recent commands:', error);
    }
  }, []);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen((prev) => !prev), []);

  const executeCommand = useCallback(
    async (commandId: string, commands: Command[]) => {
      const command = commands.find((cmd) => cmd.id === commandId);
      if (!command) {
        console.error(`Command not found: ${commandId}`);
        return;
      }
      try {
        await command.action();
        setRecentCommands((prev) => {
          const filtered = prev.filter((id) => id !== commandId);
          const updated = [commandId, ...filtered].slice(0, MAX_RECENT_COMMANDS);
          saveRecentCommands(updated);
          return updated;
        });
        setIsOpen(false);
      } catch (error) {
        console.error(`Failed to execute command ${commandId}:`, error);
      }
    },
    [saveRecentCommands]
  );

  const clearRecentCommands = useCallback(() => {
    setRecentCommands([]);
    saveRecentCommands([]);
  }, [saveRecentCommands]);

  return { isOpen, open, close, toggle, recentCommands, executeCommand, clearRecentCommands };
}
