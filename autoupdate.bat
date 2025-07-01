@echo off
D:
cd \PythonScripts
python tabelog_top150.py
rem python tabelog_scraper.py
git add .
git commit -m "AutoUpdate"
git push

pause