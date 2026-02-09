module.exports = {
    testEnvironment: 'jsdom',
    rootDir: '../',
    testMatch: [
        '<rootDir>/tests/unit/**/*.test.js',
        '<rootDir>/tests/integration/**/*.test.js'
    ],
    collectCoverageFrom: [
        'assets/js/**/*.js',
        '!assets/js/**/*.min.js',
        '!assets/js/vendor/**'
    ],
    coverageDirectory: '<rootDir>/tests/coverage',
    coverageReporters: ['html', 'text', 'lcov'],
    setupFilesAfterEnv: ['<rootDir>/tests/jest.setup.js'],
    moduleNameMapper: {
        '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    },
    transform: {
        '^.+\\.js$': 'babel-jest',
    },
    testTimeout: 10000,
    verbose: true
};
