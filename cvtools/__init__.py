"""Minimal workspace-support package for editable install.

Install with `pip install -e .` from the repository root so subfolders
can import `cvtools` and share a single environment.
"""
__all__ = ["get_requirements", "__version__"]

__version__ = "0.1.0"

from pathlib import Path


def get_requirements(path: str | None = None) -> list[str]:
    """Return lines from top-level `requirements.txt` if present.

    path: optional path to a directory inside the repo; defaults to package parent.
    """
    repo_root = Path(path) if path else Path(__file__).resolve().parents[1]
    req = repo_root / "requirements.txt"
    if not req.exists():
        return []
    return [ln.strip() for ln in req.read_text(encoding="utf8").splitlines() if ln.strip() and not ln.strip().startswith("#")]
