#!/usr/bin/env python3
"""Run the XMET ontology spec checks (kept for `make validate-redesign`).

The checks live in :mod:`xenosite.xmet.validate`; use ``xmet-validate`` for
sibling-repository checks.
"""

import sys

from xenosite.xmet.validate.cli import main

if __name__ == "__main__":
    sys.exit(main(["ontology", *sys.argv[1:]]))
