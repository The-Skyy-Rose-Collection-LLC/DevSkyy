// TypeScript resolves `@/lib/api` to this file before the `api/` directory.
// Forward everything through so all imports get the full api object.
export * from './api/index';
export { default } from './api/index';
