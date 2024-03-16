import typescript from '@rollup/plugin-typescript';
import terser from '@rollup/plugin-terser';

export default {
  input: 'assets/typescript/main.ts',
  output: {
    file: 'cerberus_crm/static/js/main.min.js',
    format: 'iife',
    plugins: [terser()]
  },
  plugins: [typescript()]
};
