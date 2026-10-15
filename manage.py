#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def use_local_virtualenv():
    """Re-run management commands with the project's environment when needed."""
    try:
        import django  # noqa: F401
        return
    except ImportError:
        pass

    project_dir = Path(__file__).resolve().parent
    executable_name = "python.exe" if os.name == "nt" else "python"
    script_dir = "Scripts" if os.name == "nt" else "bin"
    candidates = (
        project_dir / ".venv" / script_dir / executable_name,
        project_dir / "venv-ministerioselim" / script_dir / executable_name,
    )
    current_executable = Path(sys.executable).resolve()
    for executable in candidates:
        if executable.is_file() and executable.resolve() != current_executable:
            os.execv(str(executable), [str(executable), str(Path(__file__).resolve()), *sys.argv[1:]])


def main():
    """Run administrative tasks."""
    use_local_virtualenv()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ministerios_elim.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
