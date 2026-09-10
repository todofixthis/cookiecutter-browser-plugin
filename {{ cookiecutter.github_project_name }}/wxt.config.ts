import { defineConfig } from 'wxt';

// Manifest V3 for both targets — WXT resolves the Firefox
// (background.scripts) vs. Chromium (background.service_worker) split per
// build target from this one config (see docs/adr/001).
export default defineConfig({
  manifestVersion: 3,
  manifest: {
    name: '{{ cookiecutter.project_name }}',
    description: '{{ cookiecutter.project_short_description }}',
    browser_specific_settings: {
      gecko: {
        id: '{{ cookiecutter.gecko_extension_id }}',
        // Required for new Firefox extensions since 3 November 2025; this
        // placeholder collects nothing, so "none" is accurate as shipped —
        // update it if a real entrypoint starts collecting data.
        data_collection_permissions: {
          required: ['none'],
        },
      },
    },
  },
});
