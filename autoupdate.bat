@echo off
D:
cd \PythonScripts
rem python tabelog_top150.py
python tabelog_scraper.py
git add .
git commit -m "AutoUpdate"
git push

pause