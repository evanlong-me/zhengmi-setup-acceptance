# zhengmi setup acceptance

Three-OS acceptance matrix for the one-click setup scripts served by the zhengmi
gateway. Every job downloads the per-system script from the production gateway
(`/api/setup-scripts/<system>/<tool>.<ext>`) or the CDN mirror, runs it, records
the exit code in `~/zs.exit`, and verifies that the written config points at the
gateway (or, for Claude Desktop behind a plain-http gateway, that the script refused).

This repo holds no source of truth: `matrix.yml` and the two `verify_*.py`
files are copies of `.agents/skills/setup-script-ci/matrix/` in the main
repository and are overwritten on every run.
