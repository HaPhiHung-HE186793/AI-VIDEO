#!/usr/bin/env python3
"""AI Video Studio CLI — điểm vào giữ tương thích. Mã nguồn nằm trong scripts/studio/.

Ví dụ:
  python scripts/studio_helper.py status --project t-rex-24h-in-hell-creek
  python scripts/studio_helper.py --help
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from studio.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
