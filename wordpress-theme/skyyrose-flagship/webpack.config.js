/**
 * Webpack configuration for SkyyRose Flagship Theme
 * Auto-discovers and minifies all JS source files with source maps
 */

const path = require('path');
const glob = require('glob');
const TerserPlugin = require('terser-webpack-plugin');

// Auto-discover all .js files, exclude .min.js
const entries = {};
glob.sync('./assets/js/*.js', { ignore: './assets/js/*.min.js' }).forEach(file => {
  const name = path.basename(file, '.js');
  entries[name] = file;
});

module.exports = {
  mode: 'production',
  entry: entries,
  output: {
    path: path.resolve(__dirname, 'assets/js'),
    filename: '[name].min.js',
    clean: false, // Don't delete source files -- output dir IS source dir
    iife: true, // Wrap in IIFE -- these are vanilla browser scripts, not ES modules
  },
  devtool: 'source-map', // BUILD-03: generate external .map files
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: false,
            drop_debugger: true,
            pure_funcs: ['console.debug'],
          },
          format: { comments: false },
        },
        extractComments: false,
      }),
    ],
  },
  performance: {
    maxAssetSize: 500000, // 500KB warning threshold
    maxEntrypointSize: 500000,
    hints: 'warning',
  },
};
