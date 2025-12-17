/**
 * Unit Tests for Logger Utility
 * @jest-environment jsdom
 */

import { Logger, createLogger, logger } from '../Logger';

// Mock config
jest.mock('../../config/index', () => ({
  monitoringConfig: {
    logLevel: 'info',
  },
}));

describe('Logger', () => {
  let consoleSpy: jest.SpyInstance;

  beforeEach(() => {
    consoleSpy = jest.spyOn(console, 'log').mockImplementation();
  });

  afterEach(() => {
    consoleSpy.mockRestore();
  });

  describe('constructor', () => {
    it('should create logger with service name', () => {
      const log = new Logger('TestService');
      expect(log).toBeDefined();
    });

    it('should use default log level from config', () => {
      const log = new Logger('TestService');
      expect(log.getLevel()).toBe('info');
    });

    it('should accept custom log level', () => {
      const log = new Logger('TestService', { level: 'debug' });
      expect(log.getLevel()).toBe('debug');
    });

    it('should enable console logging by default', () => {
      const log = new Logger('TestService');
      log.info('Test message');
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should disable console logging when configured', () => {
      const log = new Logger('TestService', { enableConsole: false });
      log.info('Test message');
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should fall back to info level when config has no logLevel', () => {
      // Test the fallback when monitoringConfig.logLevel is empty
      jest.resetModules();
      jest.doMock('../../config/index', () => ({
        monitoringConfig: {
          logLevel: '', // Empty string - falsy
        },
      }));
      const { Logger: LoggerNoConfig } = require('../Logger');
      const log = new LoggerNoConfig('TestService');
      expect(log.getLevel()).toBe('info');
    });
  });

  describe('log levels', () => {
    it('should log debug messages when level is debug', () => {
      const log = new Logger('TestService', { level: 'debug' });
      log.debug('Debug message');
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should not log debug messages when level is info', () => {
      const log = new Logger('TestService', { level: 'info' });
      log.debug('Debug message');
      expect(consoleSpy).not.toHaveBeenCalled();
    });

    it('should log info messages when level is info', () => {
      const log = new Logger('TestService', { level: 'info' });
      log.info('Info message');
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should log warn messages when level is warn', () => {
      const log = new Logger('TestService', { level: 'warn' });
      log.warn('Warning message');
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should log error messages when level is error', () => {
      const log = new Logger('TestService', { level: 'error' });
      log.error('Error message');
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should log fatal messages when level is fatal', () => {
      const log = new Logger('TestService', { level: 'fatal' });
      log.fatal('Fatal message');
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('error logging', () => {
    it('should include error details when Error object provided', () => {
      const log = new Logger('TestService');
      const error = new Error('Test error');
      log.error('Error occurred', error);

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('Error occurred');
    });

    it('should handle non-Error objects', () => {
      const log = new Logger('TestService');
      log.error('Error occurred', { code: 'ERR_001' });
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should handle undefined error', () => {
      const log = new Logger('TestService');
      log.error('Error occurred');
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('fatal logging', () => {
    it('should include error details when Error object provided', () => {
      const log = new Logger('TestService');
      const error = new Error('Fatal error');
      log.fatal('Fatal error occurred', error);
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should handle non-Error objects', () => {
      const log = new Logger('TestService');
      log.fatal('Fatal error occurred', { code: 'FATAL_001' });
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('metadata', () => {
    it('should include metadata in log output', () => {
      const log = new Logger('TestService');
      log.info('Test message', { userId: '123', action: 'test' });

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('userId');
    });

    it('should include requestId when provided', () => {
      const log = new Logger('TestService');
      log.info('Test message', { requestId: 'req-123' });

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('req:req-123');
    });

    it('should include userId when provided', () => {
      const log = new Logger('TestService');
      log.info('Test message', { userId: 'user-456' });

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('user:user-456');
    });
  });

  describe('child logger', () => {
    it('should create child logger with additional context', () => {
      const log = new Logger('TestService');
      const childLog = log.child({ component: 'SubComponent' });

      expect(childLog).toBeInstanceOf(Logger);
    });

    it('should include parent context in child logs', () => {
      const log = new Logger('TestService');
      const childLog = log.child({ component: 'SubComponent' });
      childLog.info('Child message');

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('component');
    });

    it('should inherit parent log level', () => {
      const log = new Logger('TestService', { level: 'warn' });
      const childLog = log.child({ component: 'SubComponent' });

      expect(childLog.getLevel()).toBe('warn');
    });

    it('should inherit file path when set', () => {
      const log = new Logger('TestService', { enableFile: true, filePath: '/tmp/test.log' });
      const childLog = log.child({ component: 'SubComponent' });

      expect(childLog).toBeDefined();
    });
  });

  describe('setLevel', () => {
    it('should change log level', () => {
      const log = new Logger('TestService', { level: 'info' });
      log.setLevel('debug');
      expect(log.getLevel()).toBe('debug');
    });

    it('should affect subsequent log calls', () => {
      const log = new Logger('TestService', { level: 'error' });
      log.debug('Should not log');
      expect(consoleSpy).not.toHaveBeenCalled();

      log.setLevel('debug');
      log.debug('Should log now');
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('setConsoleLogging', () => {
    it('should enable console logging', () => {
      const log = new Logger('TestService', { enableConsole: false });
      log.info('Should not log');
      expect(consoleSpy).not.toHaveBeenCalled();

      log.setConsoleLogging(true);
      log.info('Should log now');
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should disable console logging', () => {
      const log = new Logger('TestService', { enableConsole: true });
      log.setConsoleLogging(false);
      log.info('Should not log');
      expect(consoleSpy).not.toHaveBeenCalled();
    });
  });

  describe('setFileLogging', () => {
    it('should enable file logging', () => {
      const log = new Logger('TestService');
      log.setFileLogging(true, '/tmp/test.log');
      // File logging is a placeholder, just verify no errors
      log.info('Test message');
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should disable file logging', () => {
      const log = new Logger('TestService', { enableFile: true, filePath: '/tmp/test.log' });
      log.setFileLogging(false);
      log.info('Test message');
      expect(consoleSpy).toHaveBeenCalled();
    });

    it('should not write to file when enabled without filePath', () => {
      const log = new Logger('TestService', { enableFile: true });
      log.info('Test message');
      expect(consoleSpy).toHaveBeenCalled();
    });
  });

  describe('log events', () => {
    it('should dispatch custom event when window is available', () => {
      const eventListener = jest.fn();
      window.addEventListener('devskyyLog', eventListener);

      const log = new Logger('TestService');
      log.info('Test message');

      expect(eventListener).toHaveBeenCalled();
      window.removeEventListener('devskyyLog', eventListener);
    });
  });

  describe('log formatting', () => {
    it('should format timestamp in ISO format', () => {
      const log = new Logger('TestService');
      log.info('Test message');

      const logOutput = consoleSpy.mock.calls[0][0];
      // Check for ISO date format pattern
      expect(logOutput).toMatch(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
    });

    it('should include log level in output', () => {
      const log = new Logger('TestService');
      log.info('Test message');

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('INFO');
    });

    it('should include service name in output', () => {
      const log = new Logger('MyService');
      log.info('Test message');

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('MyService');
    });
  });

  describe('console colors', () => {
    it('should use cyan for debug', () => {
      const log = new Logger('TestService', { level: 'debug' });
      log.debug('Debug message');

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('\x1b[36m'); // Cyan
    });

    it('should use green for info', () => {
      const log = new Logger('TestService');
      log.info('Info message');

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('\x1b[32m'); // Green
    });

    it('should use yellow for warn', () => {
      const log = new Logger('TestService');
      log.warn('Warning message');

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('\x1b[33m'); // Yellow
    });

    it('should use red for error', () => {
      const log = new Logger('TestService');
      log.error('Error message');

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('\x1b[31m'); // Red
    });

    it('should use magenta for fatal', () => {
      const log = new Logger('TestService');
      log.fatal('Fatal message');

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('\x1b[35m'); // Magenta
    });

    it('should reset color at end of log', () => {
      const log = new Logger('TestService');
      log.info('Test message');

      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('\x1b[0m'); // Reset
    });
  });

  describe('window event dispatch', () => {
    it('should dispatch devskyyLog event', () => {
      const eventHandler = jest.fn();
      window.addEventListener('devskyyLog', eventHandler);

      const log = new Logger('TestService');
      log.info('Test message');

      expect(eventHandler).toHaveBeenCalled();

      window.removeEventListener('devskyyLog', eventHandler);
    });

    it('should include log entry in event detail', () => {
      let eventDetail: unknown = null;
      const eventHandler = (e: Event) => {
        eventDetail = (e as CustomEvent).detail;
      };
      window.addEventListener('devskyyLog', eventHandler);

      const log = new Logger('TestService');
      log.info('Test message', { key: 'value' });

      expect(eventDetail).toBeDefined();
      expect((eventDetail as Record<string, unknown>).message).toBe('Test message');

      window.removeEventListener('devskyyLog', eventHandler);
    });
  });

  describe('createLogger factory', () => {
    it('should create logger instance', () => {
      const log = createLogger('FactoryService');
      expect(log).toBeInstanceOf(Logger);
    });

    it('should accept options', () => {
      const log = createLogger('FactoryService', { level: 'debug' });
      expect(log.getLevel()).toBe('debug');
    });
  });

  describe('default logger instance', () => {
    it('should export default logger', () => {
      expect(logger).toBeInstanceOf(Logger);
    });

    it('should have DevSkyy as service name', () => {
      logger.info('Test from default logger');
      const logOutput = consoleSpy.mock.calls[0][0];
      expect(logOutput).toContain('DevSkyy');
    });
  });
});
