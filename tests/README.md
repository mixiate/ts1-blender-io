These tests are designed to be ran over directories containing extracted files from The Sims and The Sims Online.

The `bcf`, `cmx`, `bmf`, `skn` and `cfp` tests are for The Sims 1.
The `skel`, `mesh` and `anim` tests are for The Sims Online.

For example:
`pytest --files-directory "path/to/The Sims Files/" tests/test_bcf.py`
`pytest --files-directory "path/to/The Sims Online Files/" tests/test_skel.py`
