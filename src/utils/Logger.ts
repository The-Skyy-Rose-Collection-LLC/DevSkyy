/**
 * DevSkyy Logger Utility
 * Structured logging with multiple transports and log levels
 */

import type { LogEntry } from '../types/index.js';
import { monitoringConfig } from '../config/index.js';

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

export interface LoggerOptions {
  service?: string;
  level?: LogLevel;
  enableConsole?: boolean;
  enableFile?: boolean;
  filePath?: string | undefined;
}

export class Logger {
  private service: string;
  private level: LogLevel;
  private enableConsole: boolean;
  private enableFile: boolean;
  private filePath?: string | undefined;

  private static readonly LOG_LEVELS: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
    fatal: 4,
  };

  constructor(service: string, options: LoggerOptions = {}) {
    this.service = service;
    this.level = options.level || (monitoringConfig.logLevel as LogLevel) || 'info';
    this.enableConsole = options.enableConsole ?? true;
    this.enableFile = options.enableFile ?? false;
    this.filePath = options.filePath;
  }

  /**
   * Check if a log level should be logged
   */
  private shouldLog(level: LogLevel): boolean {
    return Logger.LOG_LEVELS[level] >= Logger.LOG_LEVELS[this.level];
  }

  /**
   * Create a log entry
   */
  private createLogEntry(level: LogLevel, message: string, metadata: Record<string, unknown> = {}): LogEntry {
    const entry: LogEntry = {
      level,
      message,
      timestamp: new Date(),
      service: this.service,
      metadata,
    };

    const requestId = metadata['requestId'];
    if (typeof requestId === 'string') {
      entry.requestId = requestId;
    }

    const userId = metadata['userId'];
    if (typeof userId === 'string') {
      entry.userId = userId;
    }

    return entry;
  }

  /**
   * Format log entry for console output
   */
  private formatConsoleLog(entry: LogEntry): string {
    const timestamp = entry.timestamp.toISOString();
    const level = entry.level.toUpperCase().padEnd(5);
    const service = entry.service.padEnd(15);

    let formatted = `${timestamp} [${level}] ${service} ${entry.message}`;

    if (entry.requestId) {
      formatted += ` [req:${entry.requestId}]`;
    }

    if (entry.userId) {
      formatted += ` [user:${entry.userId}]`;
    }

    if (Object.keys(entry.metadata).length > 0) {
      formatted += ` ${JSON.stringify(entry.metadata)}`;
    }

    return formatted;
  }

  /**
   * Get console color for log level
   */
  private getConsoleColor(level: LogLevel): string {
    const colors: Record<LogLevel, string> = {
      debug: '\x1b[36m', // Cyan
      info: '\x1b[32m', // Green
      warn: '\x1b[33m', // Yellow
      error: '\x1b[31m', // Red
      fatal: '\x1b[35m', // Magenta
    };
    return colors[level] || '';
  }

  /**
   * Reset console color
   */
  private resetConsoleColor(): string {
    return '\x1b[0m';
  }

  /**
   * Write log to console
   */
  private writeToConsole(entry: LogEntry): void {
    if (!this.enableConsole) return;

    const color = this.getConsoleColor(entry.level);
    const reset = this.resetConsoleColor();
    const formatted = this.formatConsoleLog(entry);

    console.log(`${color}${formatted}${reset}`);
  }

  /**
   * Write log to file (placeholder - would use fs in Node.js)
   */
  private writeToFile(_entry: LogEntry): void {
    if (!this.enableFile || !this.filePath) return;

    // In a real implementation, you would write to file using fs
    // For now, we'll just store in memory or use a logging library
    // const jsonLog = JSON.stringify(entry);

    // Placeholder for file writing
    // fs.appendFileSync(this.filePath, jsonLog + '\n');
  }

  /**
   * Log a message
   */
  private log(level: LogLevel, message: string, metadata: Record<string, unknown> = {}): void {
    if (!this.shouldLog(level)) return;

    const entry = this.createLogEntry(level, message, metadata);

    this.writeToConsole(entry);
    this.writeToFile(entry);

    // Emit log event for external handlers
    if (typeof window !== 'undefined' && window.dispatchEvent) {
      window.dispatchEvent(new CustomEvent('devskyyLog', { detail: entry }));
    }
  }

  /**
   * Debug level logging
   */
  public debug(message: string, metadata?: Record<string, unknown>): void {
    this.log('debug', message, metadata);
  }

  /**
   * Info level logging
   */
  public info(message: string, metadata?: Record<string, unknown>): void {
    this.log('info', message, metadata);
  }

  /**
   * Warning level logging
   */
  public warn(message: string, metadata?: Record<string, unknown>): void {
    this.log('warn', message, metadata);
  }

  /**
   * Error level logging
   */
  public error(message: string, error?: Error | unknown, metadata?: Record<string, unknown>): void {
    const errorMetadata = { ...metadata };

    if (error instanceof Error) {
      errorMetadata['error'] = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
    } else if (error) {
      errorMetadata['error'] = error;
    }

    this.log('error', message, errorMetadata);
  }

  /**
   * Fatal level logging
   */
  public fatal(message: string, error?: Error | unknown, metadata?: Record<string, unknown>): void {
    const errorMetadata = { ...metadata };

    if (error instanceof Error) {
      errorMetadata['error'] = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
    } else if (error) {
      errorMetadata['error'] = error;
    }

    this.log('fatal', message, errorMetadata);
  }

  /**
   * Create a child logger with additional context
   */
  public child(additionalContext: Record<string, unknown>): Logger {
    const childOptions: LoggerOptions = {
      level: this.level,
      enableConsole: this.enableConsole,
      enableFile: this.enableFile,
    };

    if (this.filePath) {
      childOptions.filePath = this.filePath;
    }

    const childLogger = new Logger(this.service, childOptions);

    // Override log method to include additional context
    const originalLog = childLogger.log.bind(childLogger);
    childLogger.log = (level: LogLevel, message: string, metadata: Record<string, unknown> = {}) => {
      originalLog(level, message, { ...additionalContext, ...metadata });
    };

    return childLogger;
  }

  /**
   * Set log level
   */
  public setLevel(level: LogLevel): void {
    this.level = level;
  }

  /**
   * Get current log level
   */
  public getLevel(): LogLevel {
    return this.level;
  }

  /**
   * Enable/disable console logging
   */
  public setConsoleLogging(enabled: boolean): void {
    this.enableConsole = enabled;
  }

  /**
   * Enable/disable file logging
   */
  public setFileLogging(enabled: boolean, filePath?: string): void {
    this.enableFile = enabled;
    if (filePath) {
      this.filePath = filePath;
    }
  }
}

// Create default logger instance
export const logger = new Logger('DevSkyy');

// Export logger factory
export const createLogger = (service: string, options?: LoggerOptions): Logger => {
  return new Logger(service, options);
};
