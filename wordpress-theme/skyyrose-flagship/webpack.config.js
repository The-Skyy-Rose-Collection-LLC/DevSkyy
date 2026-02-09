/**
 * Webpack configuration for SkyyRose Flagship Theme
 * Minifies JavaScript assets for production deployment
 */

const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = {
  mode: 'production',
  entry: {
    'main': './assets/js/main.js',
    'navigation': './assets/js/navigation.js',
    'woocommerce': './assets/js/woocommerce.js',
    'wishlist': './assets/js/wishlist.js',
    'three-init': './assets/js/three-init.js',
    'accessibility': './assets/js/accessibility.js',
  },
  output: {
    path: path.resolve(__dirname, 'assets/js'),
    filename: '[name].min.js',
    clean: false, // Don't delete source files
  },
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: false, // Keep console for debugging
            drop_debugger: true,
            pure_funcs: ['console.debug'],
          },
          format: {
            comments: false, // Remove comments
          },
        },
        extractComments: false, // Don't create separate license files
      }),
    ],
  },
  performance: {
    maxAssetSize: 500000, // 500KB warning threshold
    maxEntrypointSize: 500000,
    hints: 'warning',
  },
};
