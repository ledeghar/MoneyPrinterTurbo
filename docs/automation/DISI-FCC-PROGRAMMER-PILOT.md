# DISI Free Claude Code programmer pilot

Companion to the completed read-only analysis run:
https://github.com/ledeghar/MoneyPrinterTurbo/actions/runs/42720144914

The first run proved this agent can read the public code and return analysis.
This second, strictly manual workflow tests whether the same NVIDIA-backed
Claude Code agent can actually **edit** two whitelisted files in a disposable
GitHub runner and produce a patch artifact.

## Permission and acceptance contract

- GitHub token limited to contents:read; checkout credentials not persisted.
- CLI tool names limited to Read, Edit, Write, Grep and Glob. Bash is excluded.
- Changes allowed only in the image search script and its pytest file.
- No automatic pull requests, pushes, deployments or social publication.
- An explicit workflow step checks that no other files were edited.
- The patch, agent report and tests are saved as a short-lived artifact.
- Claude's report is untrusted; tests and review precede applying any patch.
- The NVIDIA free quota and GitHub Actions usage must remain within free limits.

## Start

Actions -> DISI - Free Claude Code programmer pilot (patch artifact only) ->
Run workflow, branch main. Inspect DISI-FCC-Programmer-N artifact.

If the report does not contain a valid patch or tests fail, do not apply the
changes. If the patch is valid, the coordinator can propose a normal PR for
review, but this workflow deliberately has no GitHub write permissions.

The programmer's task focuses on truthful, fail-closed image provenance and
SSRF hardening. A source site or filename alone can never prove a photo's
identity or publication rights.
