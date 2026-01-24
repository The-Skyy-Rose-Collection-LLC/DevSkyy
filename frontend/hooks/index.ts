/**
 * Custom React hooks for DevSkyy frontend.
 *
 * @example
 * import { useDebounce, useToggle, useQuery, useAssets } from '@/hooks';
 */

export { useDebounce } from './useDebounce';
export { useToggle } from './useToggle';
export { useQuery } from './useQuery';
export {
  useAssets,
  useBatchJob,
  type Collection,
  type AssetType,
  type ViewMode,
} from './useAssets';
export { useWebSocket, useRoundTableWS, use3DPipelineWS } from './useWebSocket';
export { useIsMobile } from './use-mobile';
