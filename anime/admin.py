from django.contrib import admin

from .models import Anime
from .tasks import update_anime_data


@admin.action(description="Обновить данные с Shikimori")
def update_from_shikimori(modeladmin, request, queryset):
    update_anime_data.send()

    modeladmin.message_user(request, "Задача обновления запущена!")


class AnimeAdmin(admin.ModelAdmin):
    actions = [update_from_shikimori]


admin.site.register(Anime, AnimeAdmin)
