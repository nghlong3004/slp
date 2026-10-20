# Coding tools for Lead and Peer

## Ponytail

Before implementation, refactoring, or dependency selection, read
`../skills/ponytail/SKILL.md` relative to this file. Use `full` unless the user
selects another mode or switches Ponytail off.

## RTK

Use RTK for supported commands with long or repetitive output, such as
`rtk git status` or `rtk pytest`. See `rtk --help` for supported commands.

Use original commands for complete instruction and source reads, exact diffs,
logs or tracebacks, and data consumed by scripts or pipelines. Rerun unfiltered
when a summary omits required evidence. Preserve exit codes when recording checks.

If `rtk` is absent from PATH, use `"$HOME/.local/bin/rtk"`. If unavailable,
continue with normal commands.
