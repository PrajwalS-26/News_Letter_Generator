#!/usr/bin/env python3
"""Newsletter Generator - Entry Point

Usage:
    python generate.py                    # Generate newsletter
    python generate.py --preview          # Preview without sending
    python generate.py --send email slack # Send to channels
    python generate.py --no-pdf           # Skip PDF generation
    python generate.py --model mistral    # Use different model
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main

if __name__ == "__main__":
    main()
