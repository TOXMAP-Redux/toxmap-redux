module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    // dangerouslySetInnerHTML enforcement: CI grep checks frontend/src/ instead
    // (eslint-plugin-react not installed; react/no-danger cannot be used)
    // No any types
    '@typescript-eslint/no-explicit-any': 'error',
  },
}
