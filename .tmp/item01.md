# Item 01 — prepare and TurboFieldfare warmup

Run only this item after item 00 completed. Append one Showboat note and one
Showboat exec for private corpus preparation, then inspect its safe output.
Append a second note and execute exactly one discarded TurboFieldfare warmup
on chunk 00. Use the private runner's built-in timeout and do not begin a
measured chunk. Check `memory_pressure -Q` and model-owner state before the
warmup. Pop any failed Showboat entry. Stage the Showboat notebook after every
successful append and report only the safe captured output and exit code.
