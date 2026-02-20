import os
from anime.tasks import update_anime_data
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anime_project.settings')
django.setup()


if __name__ == '__main__':
    update_anime_data.send()
