import os
import subprocess
import sys

VENV_DIR = '.venv'


def venv_python(*parts):
    folder = 'Scripts' if os.name == 'nt' else 'bin'
    return os.path.join(VENV_DIR, folder, *parts)


if not os.path.isdir(VENV_DIR):
    subprocess.check_call([sys.executable, '-m', 'venv', VENV_DIR])
    subprocess.check_call([venv_python('pip'), 'install', '-r', 'requirements.txt'])

subprocess.check_call([venv_python('python'), 'app.py'])
