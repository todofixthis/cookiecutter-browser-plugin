export default defineBackground(() => {
  // Placeholder startup log, matching cookiecutter-py's placeholder test:
  // just enough to prove the scaffold works.
  console.log('{{ cookiecutter.project_name }} background started', {
    id: browser.runtime.id,
  });
});
