# Item 00 — bootstrap, preflight, and notebook initialization

Run only this item. Do not start a model. First run the bootstrapper with its
safe default scan roots. It must either create `.tmp/showboat-private-config.json`
without printing a path or stop with only an eligible-candidate count. If it
creates the config, run the privacy-safe preflight. Then initialize
`.tmp/gemma4-comparison.showboat.md`, add the privacy note, and append the
successful preflight through `showboat exec`. If an entry fails, immediately
use `showboat pop`; never leave failed output in the notebook. Stage only the
growing Showboat notebook with `git add -f` after success. Report only public
safe output, exit codes, and whether this item completed.
