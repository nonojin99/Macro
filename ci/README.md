# Windows CI workflow (staging)

GitHub MCP PAT currently lacks **Workflows** write scope, so this YAML could not be written to `.github/workflows/`.

## Activate Actions build

1. In the GitHub UI: create `.github/workflows/build-windows.yml` and paste the contents of `ci/build-windows.yml`, **or**
2. Grant the Cursor GitHub MCP token **Workflows: Read and write**, then move/copy this file to `.github/workflows/build-windows.yml` and push.

After that, every push to `main` (and `workflow_dispatch`) builds `MacroStudio-windows-x64.zip`.
