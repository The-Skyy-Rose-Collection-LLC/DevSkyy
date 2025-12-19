/**
 * Component Exports
 * Centralized exports for all UI components
 *
 * @author DevSkyy Platform Team
 * @version 1.0.0
 */

// Product Configurator Component
export { ProductConfigurator } from './ProductConfigurator.js';
export type { ProductConfig, ProductConfiguratorProps } from './ProductConfigurator.js';

// 3D Price Tag Component
export {
  PriceTag3D,
  createPriceTag3DObject,
  setupCSS2DRenderer,
  updateCSS2DRenderer,
} from './PriceTag3D.js';
export type { PriceTag3DProps } from './PriceTag3D.js';
