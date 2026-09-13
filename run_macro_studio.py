"""PyInstaller / 직접 실행용 진입점 (패키지 상대 import 회피)."""

from __future__ import annotations

from macro_studio.__main__ import main

if __name__ == "__main__":
    main()
