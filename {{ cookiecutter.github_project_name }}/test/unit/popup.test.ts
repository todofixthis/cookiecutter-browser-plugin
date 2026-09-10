import { describe, expect, it } from 'vitest';

describe('popup', () => {
  it('renders a greeting into #app', async () => {
    document.body.innerHTML = '<div id="app"></div>';
    await import('../../entrypoints/popup/main');
    const app = document.querySelector('#app');
    expect(app?.textContent).toBe(
      'Hello from {{ cookiecutter.project_name }}!',
    );
  });
});
