import threading
import subprocess
import sys
import os

PYTHON = sys.executable
DIR = os.path.dirname(__file__)


def run_admin():
    subprocess.run([PYTHON, os.path.join(DIR, "admin.py")])


def run_webapp():
    subprocess.run([PYTHON, os.path.join(DIR, "webapp.py")])


def run_bot():
    subprocess.run([PYTHON, os.path.join(DIR, "bot.py")])


if __name__ == "__main__":
    print("=" * 40)
    print("  Speak Bot ishga tushmoqda...")
    print("  Admin panel: http://localhost:3000")
    print("  Mini App:    http://localhost:8080")
    print("=" * 40)

    threading.Thread(target=run_admin, daemon=True).start()
    threading.Thread(target=run_webapp, daemon=True).start()
    run_bot()
