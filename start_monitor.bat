@echo off
cd /d "D:\my_project\ung360"
python ung360_monitor.py >> logs\task_scheduler.log 2>&1
