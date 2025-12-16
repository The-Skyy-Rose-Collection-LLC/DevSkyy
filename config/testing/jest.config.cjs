module.exports = {
  // Root directory is repository root
  rootDir: '../..',

  // Test environment
  testEnvironment: 'node',

  // TypeScript support - use regular preset for CJS compatibility
  preset: 'ts-jest',

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],

  // Transform files
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: 'config/typescript/tsconfig.json',
      isolatedModules: true,
    }],
  },

  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.(ts|tsx|js|jsx)',
    '**/*.(test|spec).(ts|tsx|js|jsx)',
  ],

  // Module name mapping for path aliases and .js extension handling
  moduleNameMapper: {
    // Handle .js extensions in TypeScript imports (ESM compatibility)
    '^(\\.{1,2}/.*)\\.js$': '$1',
    // Path aliases
    '^@/(.*)$': '<rootDir>/src/$1',
    '^@/components/(.*)$': '<rootDir>/src/components/$1',
    '^@/utils/(.*)$': '<rootDir>/src/utils/$1',
    '^@/types/(.*)$': '<rootDir>/src/types/$1',
    '^@/services/(.*)$': '<rootDir>/src/services/$1',
    '^@/hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^@/store/(.*)$': '<rootDir>/src/store/$1',
    '^@/api/(.*)$': '<rootDir>/src/api/$1',
    '^@/config/(.*)$': '<rootDir>/src/config/$1',
    '^@/security/(.*)$': '<rootDir>/src/security/$1',
  },

  // Setup files disabled temporarily
  // setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],

  // Coverage configuration
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{ts,tsx,js,jsx}',
    '!src/**/*.d.ts',
    '!src/**/*.config.{ts,js}',
    '!src/**/index.{ts,js}',
    '!src/**/*.stories.{ts,tsx,js,jsx}',
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html', 'json'],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/',
    '/.next/',
    '/.nuxt/',
  ],

  // Module directories
  moduleDirectories: ['node_modules', '<rootDir>/src'],

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks after each test
  restoreMocks: true,

  // Verbose output
  verbose: true,

  // Test timeout
  testTimeout: 10000,

  // Global setup and teardown disabled temporarily
  // globalSetup: '<rootDir>/tests/globalSetup.js',
  // globalTeardown: '<rootDir>/tests/globalTeardown.js',

  // TypeScript configuration removed - using inline transform options

  // Error handling
  errorOnDeprecated: true,

  // Watch plugins disabled for now
  // watchPlugins: [
  //   'jest-watch-typeahead/filename',
  //   'jest-watch-typeahead/testname',
  // ],
};
