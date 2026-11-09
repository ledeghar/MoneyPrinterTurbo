# DISI · Free Claude Code proof-of-concept (read-only)

Upstream: https://github.com/Alishahryar1/free-claude-code
Pinned FCC package: 6.19.4 (2026-11-09), requires Python 3.14.10.
Tool: Claude Code CLI front-end, model routed through Free Claude Code proxy.
Initial provider/model: NVIDIA NIM / `nvidia/nemotron-3-ultra-550b-a55b`.

## Intent and security boundary

Test an additional **code-review worker**, not a second unrestricted owner
of the GitHub account. This workflow runs only by manual dispatch and has
`contents: read` plus `persist-credentials: false`. It cannot push
repository changes. Claude Code's allowed toolset is restricted to
`Read,Grep,Glob` and its permission mode is `plan`. It does not run the
video generator, post content or touch the private DISIM repository.

The workflow disables the proxy's built-in web tools, binds the FCC proxy
to localhost, and creates an ephemeral proxy token on the runner.
The NVIDIA key is passed only as a masked Actions secret. Note that
retrieved repository content and prompts are still transmitted to the
external selected model. Do not use this configuration with sensitive code.
The upstream binaries are third-party dependencies: review and pin
the Claude Code CLI version before production use.

## Setup needed from the owner

1. Obtain a NVIDIA NIM API key for an eligible **free** plan at
   https://build.nvidia.com/settings/api-keys ; confirm actual quota and terms.
   Do not enable billing.
2. In this repository, go to **Settings → Secrets and variables → Actions →
   New repository secret**, name it `NVIDIA_NIM_API_KEY`, and paste the key.
   Do not put it in a file, issue, chat or README.
3. Once the pilot workflow is reviewed and merged, open
   **Actions → DISI - Free Claude Code read-only pilot → Run workflow**.
4. Download the `DISI-FCC-ReadOnly-Review-...` workflow artifact and inspect
   `report.md`. Compare agent suggestions against the actual repository.
   Review failures in Actions logs. No publication or merge happens.

GitHub's free Actions quotas and NVIDIA free-model availability can vary.
An absent key stops execution before installing dependencies. This workflow
should be kept manual; if free quotas are exhausted, stop rather than pay.

## Interpretation

**Not yet verified:** workflow execution, account-specific quotas, model
availability, successful noninteractive Claude Code onboarding and quality
of generated reports. A committed workflow is not an executed integration.
No model is granted code write permissions. A second, separately approved
workflow would be needed for isolated branches and pull requests.

Initial target: `scripts/mn_short_image_search.py`, the existing editorial
image-search pipeline, not a hardcoded person-specific search.

Orchestration contract: ChatGPT defines the task and reviews the report;
Free Claude Code runs it under GitHub Actions only when manually dispatched;
any code changes remain a future, separately permissioned stage.
