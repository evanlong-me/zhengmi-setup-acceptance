# zhengmi setup acceptance

Three-OS acceptance matrix for the one-click setup scripts served by the zhengmi
gateway. Every job downloads the script from the production gateway (or the CDN
mirror), runs it, and verifies that the written config points at the gateway.

This repo holds no source of truth: `matrix.yml` and the two `verify_*.py`
files are copies of `.agents/skills/setup-script-ci/matrix/` in the main
repository and are overwritten on every run.
