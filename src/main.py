"""Main CLI entry point for the static site generator.

Kept for backwards compatibility - delegates to the single pipeline in
``generate.py`` so there is only one source of truth for the build.
"""

import sys
import os

# Add project root to path.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from generate import run_cli


def main():
    run_cli()


if __name__ == "__main__":
    main()