@echo off
D:
cd \PythonScripts
python tabelog_top200.py
rem python tabelog_scraper.py
git add .
git commit -m "AutoUpdate"
git push

pause