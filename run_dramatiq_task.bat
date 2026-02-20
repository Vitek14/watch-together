@echo off
call G:\pythonProjects\anime_project\.venv\Scripts\activate.bat

cd G:\pythonProjects\anime_project

python manage.py shell -c "from anime.tasks import update_anime_data; update_anime_data.send()"

pause
