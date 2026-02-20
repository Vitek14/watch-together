import uuid

from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from django.db import models
# from django.contrib.postgres.fields import ArrayField


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    video_url = models.URLField(max_length=500)
    stream_url = models.JSONField(max_length=500, default=list, null=True, blank=True)
    anime_title = models.CharField(max_length=255, null=True, blank=True)
    current_season = models.IntegerField(null=True, blank=True)
    current_episode = models.IntegerField(null=True, blank=True)
    current_translator = models.CharField(max_length=100, null=True, blank=True)
    current_time = models.FloatField(default=0)
    is_playing = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    password = models.CharField(max_length=128, null=True, blank=True)
    participants_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Room {self.id} - {self.video_url}"

    def set_password(self, raw_password):
        if not raw_password:
            self.password = None  # Удаляем пароль если передана пустота
        else:
            self.password = make_password(raw_password)  # Хешируем пароль

    # Проверяет переданный пароль
    def check_password(self, raw_password):
        if not self.password:  # Если пароль комнаты не установлен
            return not raw_password  # Разрешаем доступ только при пустом пароле
        return check_password(raw_password, self.password)  # Сверяем хеш


class DateModel(models.Model):
    year = models.IntegerField(null=True, blank=True)
    month = models.IntegerField(null=True, blank=True)
    day = models.IntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)

    # class Meta:
    #     abstract = True


class FanDubber(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, null=True, blank=True)


class Genre(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=50)
    russian = models.CharField(max_length=50, null=True, blank=True)
    kind = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.russian or self.name


class Studio(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=255)
    image_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.name


class Poster(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    original_url = models.URLField(max_length=500)

    def __str__(self):
        return f"Poster {self.id}"


class Screenshot(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    original_url = models.URLField(max_length=500)
    x332_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return f"Screenshot {self.id}"


class ScoreStat(models.Model):
    score = models.IntegerField()
    count = models.IntegerField()

    def __str__(self):
        return f"Score: {self.score}, Count: {self.count}"


class Related(models.Model):
    RELATION_KINDS = (
        ('prequel', 'Предыстория'),
        ('sequel', 'Продолжение'),
        ('adaptation', 'Адаптация'),
        ('other', 'Другое'),
    )

    id = models.CharField(max_length=20, primary_key=True)
    relation_kind = models.CharField(max_length=20, choices=RELATION_KINDS)
    relation_text = models.CharField(max_length=100, null=True, blank=True)
    anime_id = models.CharField(max_length=20, null=True, blank=True)
    anime_name = models.CharField(max_length=255, null=True, blank=True)
    manga_id = models.CharField(max_length=20, null=True, blank=True)
    manga_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.get_relation_kind_display()} - {self.anime_name or self.manga_name}"


class Anime(models.Model):
    KINDS = (
        ('tv', 'TV Сериал'),
        ('movie', 'Фильм'),
        ('ova', 'OVA'),
        ('ona', 'ONA'),
        ('special', 'Спешл'),
    )

    STATUSES = (
        ('anons', 'Анонсировано'),
        ('ongoing', 'Выходит'),
        ('released', 'Завершено'),
    )

    RATINGS = (
        ('g', 'G'),
        ('pg', 'PG'),
        ('pg_13', 'PG-13'),
        ('r', 'R-17'),
        ('r_plus', 'R+'),
        ('rx', 'Rx'),
    )

    id = models.CharField(max_length=10, primary_key=True)
    mal_id = models.CharField(max_length=20, null=True, blank=True)
    name = models.CharField(max_length=255)
    russian = models.CharField(max_length=255, null=True, blank=True)
    license_name_ru = models.CharField(max_length=255, null=True, blank=True)
    english = models.CharField(max_length=255, null=True, blank=True)
    japanese = models.CharField(max_length=255, null=True, blank=True)
    # synonyms = ArrayField(
    #     models.CharField(max_length=255),
    #     default=list,
    #     blank=True
    # )
    kind = models.CharField(max_length=20, choices=KINDS)
    rating = models.CharField(max_length=10, choices=RATINGS, null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES)
    episodes = models.IntegerField(null=True, blank=True)
    episodes_aired = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(help_text="Длительность в минутах", null=True, blank=True)
    aired_on = models.ForeignKey(
        'DateModel',
        on_delete=models.SET_NULL,
        related_name='anime_aired_on',
        null=True,
        blank=True
    )
    released_on = models.ForeignKey(
        'DateModel',
        on_delete=models.SET_NULL,
        related_name='anime_released_on',
        null=True,
        blank=True
    )
    url = models.URLField(max_length=500)
    season = models.CharField(max_length=50, null=True, blank=True)
    poster = models.ForeignKey(
        'Poster',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    # fansubbers = ArrayField(
    #     models.CharField(max_length=100),
    #     default=list,
    #     blank=True
    # )
    # fandubbers = ArrayField(
    #     models.CharField(max_length=100),
    #     default=list,
    #     blank=True
    # )
    # licensors = ArrayField(
    #     models.CharField(max_length=100),
    #     default=list,
    #     blank=True
    # )
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    next_episode_at = models.DateTimeField(null=True, blank=True)
    is_censored = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    description_html = models.TextField(null=True, blank=True)
    description_source = models.TextField(null=True, blank=True)

    # Связи ManyToMany
    genres = models.ManyToManyField(Genre)
    studios = models.ManyToManyField(Studio)
    screenshots = models.ManyToManyField(Screenshot)
    score_stats = models.ManyToManyField(ScoreStat)
    related = models.ManyToManyField(Related)
    fundubbers = models.ManyToManyField(FanDubber)
    hdrezka_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.russian or self.name

    class Meta:
        ordering = ['-id']
