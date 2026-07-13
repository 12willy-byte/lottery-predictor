@echo off
cd /d "C:\Users\Administrator\Documents\彩票选票机"
git config --global credential.helper
git config user.name
git config user.email
git remote -v
git push -u origin master 2>&1
