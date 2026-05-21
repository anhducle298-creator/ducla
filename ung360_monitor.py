import os
import runpy


PROJECT_DIR = r"D:\my_project\ung360"
SCRIPT_PATH = os.path.join(PROJECT_DIR, "ung360_monitor.py")

os.chdir(PROJECT_DIR)
runpy.run_path(SCRIPT_PATH, run_name="__main__")
