import os
import runpy


PROJECT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "my project", "ung360")
SCRIPT_PATH = os.path.join(PROJECT_DIR, "ung360_monitor.py")

os.chdir(PROJECT_DIR)
runpy.run_path(SCRIPT_PATH, run_name="__main__")
