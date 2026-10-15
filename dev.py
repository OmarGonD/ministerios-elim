#!/usr/bin/env python3
"""Cross-platform local setup and management without activating a virtualenv."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
ENV = ROOT / '.venv'
PYTHON = ENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def run(*args):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, check=True)


def require_environment():
    if not PYTHON.is_file():
        raise RuntimeError('Primero ejecuta: python dev.py setup')
    probe = subprocess.run(
        [str(PYTHON), '-c', 'import sys; print(sys.platform)'],
        cwd=ROOT, capture_output=True, text=True,
    )
    if probe.returncode or probe.stdout.strip() != sys.platform:
        raise RuntimeError(
            'El entorno .venv no pertenece a este sistema. Renómbralo o elimínalo '
            'y ejecuta nuevamente: python dev.py setup'
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['setup', 'run', 'manage'])
    parser.add_argument('--demo', action='store_true', help='Cargar contenido de demostración durante setup')
    args, extra = parser.parse_known_args()
    if args.command == 'setup':
        if extra:
            parser.error('setup solo admite --demo')
        if sys.version_info[:2] != (3, 12):
            raise RuntimeError('Usa Python 3.12 para instalar las dependencias de este proyecto.')
        if not ENV.exists():
            venv.EnvBuilder(with_pip=True).create(ENV)
        require_environment()
        run(PYTHON, '-m', 'pip', 'install', '--upgrade', 'pip')
        run(PYTHON, '-m', 'pip', 'install', '-r', ROOT / 'requirements.txt')
        run(PYTHON, ROOT / 'manage.py', 'migrate', '--noinput')
        run(PYTHON, ROOT / 'manage.py', 'replace_homepage')
        if args.demo:
            run(PYTHON, ROOT / 'manage.py', 'demo_seed')
        print('Proyecto preparado. Inicia con: python dev.py run')
    else:
        require_environment()
        if args.command == 'run':
            run(PYTHON, ROOT / 'manage.py', 'runserver', *(extra or ['127.0.0.1:8000']))
        else:
            if not extra:
                parser.error('Indica un comando de Django, por ejemplo: manage check')
            run(PYTHON, ROOT / 'manage.py', *extra)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
