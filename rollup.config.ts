import typescript from '@rollup/plugin-typescript';

export default {
  input: 'assets/typescript/main.ts',
  output: {
    dir: 'cerberus_crm/static/js/',
    format: 'iife'
  },
  plugins: [typescript()]
};
