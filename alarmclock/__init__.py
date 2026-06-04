"""A dependency-free command-line alarm clock."""

__version__ = "1.0.0"


def main():
    import sys
    from .cli import main as _main
    sys.exit(_main())
