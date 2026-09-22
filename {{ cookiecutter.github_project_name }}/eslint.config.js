// @ts-check
import js from '@eslint/js';
import eslintConfigPrettier from 'eslint-config-prettier';
import globals from 'globals';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: [
      '.output/**',
      '.wxt/**',
      'node_modules/**',
      'coverage/**',
      'docs/_build/**',
    ],
  },
  js.configs.recommended,
  tseslint.configs.recommendedTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
      globals: {
        ...globals.browser,
        ...globals.webextensions,
      },
    },
  },
  eslintConfigPrettier,
  {
    // eslint.config.js itself (and any other plain .js file) isn't part of
    // the typed program tsconfig.json describes — drop typed-linting rules
    // for it rather than have projectService fail to place it in a project.
    files: ['**/*.js'],
    ...tseslint.configs.disableTypeChecked,
  },
);
