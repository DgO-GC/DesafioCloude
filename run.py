"""Atalho para rodar a CLI sem instalar nada: python run.py calcular --input ... --output ..."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from reembolso.cli import main  # noqa: E402

sys.exit(main())
