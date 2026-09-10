import { expect, test } from './fixtures';

test('popup renders a greeting', async ({ context, extensionId }) => {
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  await expect(page.locator('#app')).toHaveText(
    'Hello from {{ cookiecutter.project_name }}!',
  );
});
