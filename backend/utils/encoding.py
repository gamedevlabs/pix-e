"""
Encoding utilities to handle Unicode characters safely on different platforms.
"""

import os
import sys


def safe_print(*args, **kwargs):
    """
    Safe print function that handles Unicode characters properly on Windows.
    Falls back to ASCII representations if Unicode fails.
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Convert Unicode symbols to ASCII alternatives
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace common Unicode symbols with ASCII alternatives
                safe_arg = (
                    arg.replace("✅", "[SUCCESS]")
                    .replace("⚠️", "[WARNING]")
                    .replace("❌", "[ERROR]")
                    .replace("🚨", "[ALERT]")
                    .replace("🔄", "[LOADING]")
                    .replace("📊", "[DATA]")
                    .replace("🎯", "[TARGET]")
                    .replace("💡", "[INFO]")
                    .replace("🚀", "[START]")
                    .replace("🏁", "[FINISH]")
                    .encode("ascii", "replace")
                    .decode("ascii")
                )
                safe_args.append(safe_arg)
            else:
                safe_args.append(arg)
        print(*safe_args, **kwargs)


def is_windows_console():
    """Check if running in Windows console with potential encoding issues."""
    return (
        os.name == "nt"
        and hasattr(sys.stdout, "encoding")
        and sys.stdout.encoding.lower().startswith("cp")
    )


def configure_console_encoding():
    """
    Configure console encoding for Unicode support on Windows.
    Should be called early in application startup.
    """
    if is_windows_console():
        try:
            # Try to set environment variable for Python IO encoding
            os.environ["PYTHONIOENCODING"] = "utf-8"

            # Try to change console code page to UTF-8
            import subprocess

            subprocess.run(
                ["chcp", "65001"], shell=True, capture_output=True, check=False
            )
        except Exception:
            pass  # Ignore errors, fallback will handle it
