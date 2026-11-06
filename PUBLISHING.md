# Publishing policy

Published version manifests are immutable. Never delete or rewrite
`packages/<name>/versions/<version>/dpm.toml`; publish corrected metadata or
artifacts under a new version instead.

To withdraw a published version from normal resolution, change only
`yanked = false` to `yanked = true` and add a non-empty `yank_reason`. A yanked
version remains in history for installed-state and incident review.

Every change must pass registry structure validation and artifact SHA-256
verification. The `Registry` workflow also runs the ripgrep lifecycle on macOS
Apple silicon. Repository administrators must configure that workflow as a
required check on protected `master` before accepting contributions.
