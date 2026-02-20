import json
import uuid
from datetime import datetime

from HdRezkaApi import HdRezkaSearch, HdRezkaApi
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import render
import requests
from django.views.decorators.csrf import csrf_exempt

from anime.forms import SearchForm
from anime.models import Anime, DateModel, Poster, Genre, Studio, Screenshot, ScoreStat, Related, Room


@csrf_exempt
def create_video_room(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if request.user.is_authenticated:
                room = Room.objects.create(
                    creator=request.user,
                    video_url=data.get('video_url'),
                    stream_url=data.get('stream_url'),
                    anime_title=data.get('anime_title'),
                    current_season=data.get('current_season'),
                    current_episode=data.get('current_episode'),
                    current_translator=data.get('current_translator'),
                    is_playing=data.get('is_playing'),
                    current_time=data.get('current_time'),
                )
            else:
                room = Room.objects.create(
                    video_url=data.get('video_url'),
                    stream_url=data.get('stream_url'),
                    anime_title=data.get('anime_title'),
                    current_season=data.get('current_season'),
                    current_episode=data.get('current_episode'),
                    current_translator=data.get('current_translator'),
                    is_playing=data.get('is_playing'),
                    current_time=data.get('current_time'),
                )
            return JsonResponse({'room_id': str(room.id)})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)


# @csrf_exempt
def get_room_info(request, room_id):
    try:
        room = Room.objects.get(id=uuid.UUID(room_id))
        return JsonResponse({
            'exists': True,
            'video_url': room.video_url,
            'stream_url': room.stream_url,
            'anime_title': room.anime_title,
            'current_season': room.current_season,
            'current_episode': room.current_episode,
            'current_translator': room.current_translator,
            'current_time': room.current_time,
            'is_playing': room.is_playing
        })
    except (Room.DoesNotExist, ValueError):
        return JsonResponse({'exists': False})


# @csrf_exempt
def get_stream(request):
    if request.method == "GET":
        link = request.GET.get('link')
        season = request.GET.get('season')
        episode = request.GET.get('episode')
        translator_id = request.GET.get('translator_id')
        print(link, season, episode, translator_id)
        if link is None or translator_id is None:
            return JsonResponse({'error': 'Invalid Request'}, status=400)
        rezka = HdRezkaApi(link, headers={"User-Agent": "Mozilla/5.0"})
        if season is None or episode is None:
            streams = rezka.getStream(None, None, translator_id).videos
        else:
            streams = rezka.getStream(season, episode, translator_id).videos
        response = {}
        for stream in streams:
            response[stream] = streams[stream][0]
            print(streams[stream][0])
        print(streams)
        return JsonResponse(response, safe=False)
    return JsonResponse({'error': 'Invalid Request'}, status=400)


@csrf_exempt
def player_info(request):
    if request.method == 'POST':
        raw_data = request.body.decode('utf-8')
        data = json.loads(raw_data)
        try:
            name = data["name"]
        except KeyError:
            print("nonono")
            raise Http404

        try:
            link = data["link"]
        except KeyError:
            link = HdRezkaSearch("https://rezka-ua.tv/")(name, find_all=True)[0][0]["url"]

        rezka = HdRezkaApi(link, headers={"User-Agent": "Mozilla/5.0"})
        content_type = rezka.type.name
        # title = rezka.title  # Получаем название аниме

        response_data = {
            "title": name,
            "link": link,
            "type": content_type,
        }

        if content_type == "tv_series":
            # Обработка серийника
            seasons = []
            for season_info in rezka.episodesInfo:
                episodes_list = []
                for episode in season_info["episodes"]:
                    # Формируем информацию о переводчиках для эпизода
                    translators = []
                    for tr in episode["translations"]:
                        translators.append({
                            "id": tr["translator_id"],
                            "name": tr["translator_name"],
                            "premium": tr["premium"]
                        })

                    episodes_list.append({
                        "id": episode["episode"],
                        "name": episode["episode_text"],
                        "translators": translators
                    })

                seasons.append({
                    "season": season_info["season"],
                    "name": season_info["season_text"],
                    "episodes": episodes_list
                })

            response_data["seasons"] = seasons

        else:
            # Обработка полнометражного аниме
            translators = []
            for translator_id, translator_info in rezka.translators.items():
                translators.append({
                    "id": translator_id,
                    "name": translator_info["name"]
                })

            response_data["translators"] = translators

        return JsonResponse(response_data)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def search_view(request):
    results = []
    query = ""

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Anime.objects.filter(name__icontains=query)[:10]
    else:
        form = SearchForm()

    return render(request, 'search.html', {
        'form': form,
        'results': results,
        'query': query
    })


def info(request, anime_id):
    try:
        anime = Anime.objects.get(id=anime_id)
    except Anime.DoesNotExist:
        url = "https://shikimori.one/api/graphql"
        payload = json.dumps({
            "query": "{\n  # look for more query params in the documentation\n  animes(ids: " + '"' + str(anime_id) + '"' + ", limit: 1) {\n    id\n    malId\n    name\n    russian\n    licenseNameRu\n    english\n    japanese\n    synonyms\n    kind\n    rating\n    score\n    status\n    episodes\n    episodesAired\n    duration\n    airedOn { year month day date }\n    releasedOn { year month day date }\n    url\n    season\n\n    poster { id originalUrl mainUrl }\n\n    fansubbers\n    fandubbers\n    licensors\n    createdAt,\n    updatedAt,\n    nextEpisodeAt,\n    isCensored\n\n    genres { id name russian kind }\n    studios { id name imageUrl }\n\n    related {\n      id\n      anime {\n        id\n        name\n      }\n      manga {\n        id\n        name\n      }\n      relationKind\n      relationText\n    }\n\n    screenshots { id originalUrl x332Url }\n\n    scoresStats { score count }\n\n    description\n    descriptionHtml\n    descriptionSource\n  }\n}"
        })
        headers = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Origin': 'https://shikimori.one',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
        }

        response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(data)

        # Обрабатываем только если есть данные в ожидаемом формате
        if not data.get('data') or not isinstance(data['data'].get('animes'), list):
            print("no data")
            raise Http404

        for anime_data in data['data']['animes']:
            with transaction.atomic():
                # Создаем или обновляем основную запись аниме
                anime, created = Anime.objects.update_or_create(
                    id=str(anime_data['id']),
                    defaults={
                        'mal_id': str(anime_data.get('malId', '')),
                        'name': anime_data.get('name', ''),
                        'russian': anime_data.get('russian', ''),
                        'english': anime_data.get('english', ''),
                        'japanese': anime_data.get('japanese', ''),
                        'kind': anime_data.get('kind', 'tv'),
                        'rating': anime_data.get('rating', ''),
                        'score': anime_data.get('score'),
                        'status': anime_data.get('status', 'anons'),
                        'episodes': anime_data.get('episodes'),
                        'episodes_aired': anime_data.get('episodesAired'),
                        'duration': anime_data.get('duration'),
                        'url': anime_data.get('url', ''),
                        'season': anime_data.get('season', ''),
                        'is_censored': anime_data.get('isCensored', False),
                        'description': anime_data.get('description', ''),
                        'description_html': anime_data.get('descriptionHtml', ''),
                        'description_source': anime_data.get('descriptionSource', ''),
                        'created_at': datetime.fromisoformat(anime_data['createdAt']) if anime_data.get(
                            'createdAt') else None,
                        'updated_at': datetime.fromisoformat(anime_data['updatedAt']) if anime_data.get(
                            'updatedAt') else None,
                        'next_episode_at': datetime.fromisoformat(anime_data['nextEpisodeAt']) if anime_data.get(
                            'nextEpisodeAt') else None,
                    }
                )

                # Обрабатываем даты
                if anime_data.get('airedOn'):
                    aired_on, _ = DateModel.objects.get_or_create(
                        year=anime_data['airedOn'].get('year'),
                        month=anime_data['airedOn'].get('month'),
                        day=anime_data['airedOn'].get('day'),
                        date=anime_data['airedOn'].get('date')
                    )
                    anime.aired_on = aired_on

                if anime_data.get('releasedOn'):
                    released_on, _ = DateModel.objects.get_or_create(
                        year=anime_data['releasedOn'].get('year'),
                        month=anime_data['releasedOn'].get('month'),
                        day=anime_data['releasedOn'].get('day'),
                        date=anime_data['releasedOn'].get('date')
                    )
                    anime.released_on = released_on

                # Постер
                if anime_data.get('poster'):
                    poster, _ = Poster.objects.get_or_create(
                        id=str(anime_data['poster']['id']),
                        defaults={'original_url': anime_data['poster']['originalUrl']}
                    )
                    anime.poster = poster

                # Жанры
                if anime_data.get('genres'):
                    for genre_data in anime_data['genres']:
                        genre, _ = Genre.objects.get_or_create(
                            id=str(genre_data['id']),
                            defaults={
                                'name': genre_data.get('name', ''),
                                'russian': genre_data.get('russian', ''),
                                'kind': genre_data.get('kind', ''),
                            }
                        )
                        anime.genres.add(genre)

                # Студии
                if anime_data.get('studios'):
                    for studio_data in anime_data['studios']:
                        studio, _ = Studio.objects.get_or_create(
                            id=str(studio_data['id']),
                            defaults={
                                'name': studio_data.get('name', ''),
                                'image_url': studio_data.get('imageUrl', ''),
                            }
                        )
                        anime.studios.add(studio)

                # Скриншоты
                if anime_data.get('screenshots'):
                    for screenshot_data in anime_data['screenshots']:
                        screenshot, _ = Screenshot.objects.get_or_create(
                            id=str(screenshot_data['id']),
                            defaults={
                                'original_url': screenshot_data['originalUrl'],
                                'x332_url': screenshot_data.get('x332Url', ''),
                            }
                        )
                        anime.screenshots.add(screenshot)

                # Статистика оценок
                if anime_data.get('scoresStats'):
                    for stat_data in anime_data['scoresStats']:
                        stat, _ = ScoreStat.objects.get_or_create(
                            score=stat_data['score'],
                            defaults={'count': stat_data['count']}
                        )
                        anime.score_stats.add(stat)

                # Связанные аниме
                if anime_data.get('related'):
                    for related_data in anime_data['related']:
                        related, _ = Related.objects.get_or_create(
                            id=str(related_data['id']),
                            defaults={
                                'relation_kind': related_data.get('relationKind', ''),
                                'relation_text': related_data.get('relationText', ''),
                                'anime_id': str(related_data['anime']['id']) if related_data.get('anime') else None,
                                'anime_name': related_data['anime']['name'] if related_data.get('anime') else None,
                                'manga_id': str(related_data['manga']['id']) if related_data.get('manga') else None,
                                'manga_name': related_data['manga']['name'] if related_data.get('manga') else None,
                            }
                        )
                        anime.related.add(related)

                anime.save()
    return render(request, 'anime/info.html', {"anime": anime})


def index(request):
    results = []
    # query = ""

    animes = Anime.objects.all().order_by('-score')[:50]
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Anime.objects.filter(russian__icontains=query)[:10]
            if not results:
                url = "https://shikimori.one/api/graphql"
                payload = json.dumps({
                    "query": "{\n  # look for more query params in the documentation\n  animes(search: " + '"' + str(
                        query) + '"' + ", limit: 1) {\n    id\n    malId\n    name\n    russian\n    licenseNameRu\n    english\n    japanese\n    synonyms\n    kind\n    rating\n    score\n    status\n    episodes\n    episodesAired\n    duration\n    airedOn { year month day date }\n    releasedOn { year month day date }\n    url\n    season\n\n    poster { id originalUrl mainUrl }\n\n    fansubbers\n    fandubbers\n    licensors\n    createdAt,\n    updatedAt,\n    nextEpisodeAt,\n    isCensored\n\n    genres { id name russian kind }\n    studios { id name imageUrl }\n\n    related {\n      id\n      anime {\n        id\n        name\n      }\n      manga {\n        id\n        name\n      }\n      relationKind\n      relationText\n    }\n\n    screenshots { id originalUrl x332Url }\n\n    scoresStats { score count }\n\n    description\n    descriptionHtml\n    descriptionSource\n  }\n}"
                })
                headers = {
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Connection': 'keep-alive',
                    'DNT': '1',
                    'Origin': 'https://shikimori.one',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
                }

                response = requests.request("POST", url, headers=headers, data=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
                print(data)
                if not data.get('data') or not isinstance(data['data'].get('animes'), list):
                    print("not found")
                    return render(request, 'anime/results.html', {'animes': animes,
                                                        'form': form,
                                                        'results': results,
                                                        'query': query})
                results = [
                    {
                        "id": data['data']['animes'][0]['id'],
                        "russian": data['data']['animes'][0]['russian'] if not None else data['data']['animes'][0]['name'],
                    }
                ]

            # print(results)
            # print(query)
            return render(request, 'anime/results.html', {'animes': animes,
                                                        'form': form,
                                                        'results': results,
                                                        'query': query})
    else:
        query = None
        form = SearchForm()

    return render(request, 'anime/index.html', {'animes': animes,
                                                'form': form,
                                                'results': results,
                                                'query': query})
