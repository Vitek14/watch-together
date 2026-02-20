// Глобальные переменные для хранения текущего состояния
let playerData = null;
let currentSeason = 1;
let currentEpisode = 1;
let currentTranslator = null;
let streamUrl = null;

let currentRoomId = null;
let socket = null;
let isSyncing = false;
let isRoomOwner = false;

function initializePlayer(animeName, animeLink) {
    const playerControls = document.getElementById('player-controls');
    const episodeControls = document.getElementById('episode-controls');
    const loadingOverlay = document.getElementById('loading-overlay');
    const mainPlayer = document.querySelector('media-player');

    // Загружаем данные о плеере
    loadPlayerData();

    function showLoading() {
        loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        loadingOverlay.remove()
    }

    function renderEpisodes(episodes) {
        episodeControls.innerHTML = '<div class="d-flex flex-wrap gap-2 mb-3" id="episodes-container"></div>';
        const container = document.getElementById('episodes-container');

        episodes.forEach(episode => {
            const btn = document.createElement('button');
            btn.className = 'btn btn-outline-secondary episode-btn';
            btn.dataset.episodeId = episode.id;
            btn.textContent = episode.name;

            btn.addEventListener('click', () => {
                document.querySelectorAll('.episode-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                // Получаем выбранный сезон
                const seasonSelect = document.getElementById('season-select');
                const seasonNum = seasonSelect.value;
                currentEpisode = episode.id;

                // Загружаем стрим
                loadStream({
                    link: playerData.link,
                    season: currentSeason,
                    episode: currentEpisode,
                    translator_id: currentTranslator
                });
            });

            container.appendChild(btn);
        });


        // Активируем первую кнопку эпизода
        if (container.firstChild) {
            container.firstChild.classList.add('active');
        }

        const translatorsDiv = document.createElement('div');
        translatorsDiv.className = 'd-flex flex-wrap gap-2 mb-3';
        translatorsDiv.innerHTML = '<strong>Озвучка:</strong>';

        episodes[0].translators.forEach((translator, index) => {
            const btn = document.createElement('button');
            if (index === 0) {
                btn.className = 'btn btn-outline-primary btn-sm active translator-btn';
            } else {
                btn.className = 'btn btn-outline-primary btn-sm translator-btn';
            }
            btn.id = 'translation_' + index
            btn.dataset.translatorId = translator.id;
            btn.textContent = translator.name;
            btn.addEventListener('click', () => {
                currentTranslator = translator.id;
                document.querySelectorAll('.translator-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                loadStream({
                    link: playerData.link,
                    season: currentSeason,
                    episode: currentEpisode,
                    translator_id: currentTranslator
                });
            });

            translatorsDiv.appendChild(btn);
            playerControls.appendChild(translatorsDiv);
        });

    }

    function renderPlayerUI(data) {
        playerControls.innerHTML = '';

        if (data.type === 'tv_series') {
            currentSeason = data.seasons["0"]["season"];
            currentTranslator = playerData.seasons["0"]["episodes"]["0"]["translators"]["0"]["id"];
            console.log("translator: ", currentTranslator)

            // Создаем элементы для сериала
            const seasonSelect = document.createElement('select');
            seasonSelect.className = 'form-select mb-3';
            seasonSelect.id = 'season-select';

            // Добавляем сезоны
            data.seasons.forEach(season => {
                const option = document.createElement('option');
                option.value = season.season;
                option.textContent = season.name;
                seasonSelect.appendChild(option);
            });

            playerControls.appendChild(seasonSelect);

            // Обработчик изменения сезона
            seasonSelect.addEventListener('change', () => {
                const seasonNum = seasonSelect.value;
                const season = data.seasons.find(s => s.season == seasonNum);
                currentSeason = data.seasons.find(s => s.season == seasonNum);
                console.log("Changed season to: ", currentSeason);
                renderEpisodes(season.episodes);
            });

            // Рендерим эпизоды для первого сезона
            const firstSeason = data.seasons[0];
            renderEpisodes(firstSeason.episodes);

            // Показываем блок с эпизодами
            episodeControls.style.display = 'block';


        } else {
            // Создаем кнопки озвучки для фильма
            currentSeason = null;
            currentTranslator = data.translators["0"]["id"]

            const translatorsDiv = document.createElement('div');
            translatorsDiv.className = 'd-flex flex-wrap gap-2 mb-3';
            translatorsDiv.innerHTML = '<strong>Озвучка:</strong>';

            data.translators.forEach(translator => {
                const btn = document.createElement('button');
                if (index === 0) {
                    btn.className = 'btn btn-outline-primary btn-sm active';
                } else {
                    btn.className = 'btn btn-outline-primary btn-sm';
                }
                btn.dataset.translatorId = translator.id;
                btn.textContent = translator.name;
                btn.addEventListener('click', () => {
                    loadStream({
                        link: data.link,
                        translator_id: translator.id
                    });
                });
                translatorsDiv.appendChild(btn);
            });

            playerControls.appendChild(translatorsDiv);
        }
    }

    async function loadStream(params) {
        showLoading();
        try {
            const response = await fetch('/anime/getStream?' + new URLSearchParams(params));
            const streamData = await response.json();

            const provider = mainPlayer.querySelector('media-provider');
            mainPlayer.startLoading();

            // Вызывается когда постер надо загрузить
            mainPlayer.src = [
                {
                    src: streamData["1080p"],
                    type: 'video/mp4',
                    width: 1920,
                    height: 1080,
                },
                {
                    src: streamData["720p"],
                    type: 'video/mp4',
                    width: 1280,
                    height: 720,
                },
                {
                    src: streamData["360p"],
                    type: 'video/mp4',
                    width: 640,
                    height: 360,
                },
            ];

            console.log(streamData);
            streamUrl = streamData  // Для соединения по вебсокетам

        } catch (error) {
            console.error('Ошибка загрузки видео:', error);
        } finally {
            hideLoading();
        }
    }

    function loadDefaultStream(data) {
        if (data.type === 'tv_series') {
            const seasonNum = document.getElementById('season-select').value;
            const season = data.seasons.find(s => s.season == seasonNum);

            loadStream({
                link: data.link,
                season: seasonNum,
                episode: season.episodes[0].id,
                translator_id: season.episodes[0].translators[0].id
            });
        } else {
            loadStream({
                link: data.link,
                translator_id: data.translators[0].id
            });
        }
    }

    async function loadPlayerData() {
        showLoading();
        try {
            const response = await fetch(`/anime/getPlayerInfo/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: animeName,
                    link: animeLink || undefined
                })
            });
            playerData = await response.json();

            renderPlayerUI(playerData);

            loadDefaultStream(playerData);

        } catch (error) {
            console.error('Ошибка загрузки данных:', error);
        }
    }

    return {
        initializePlayer
    };
}

function initializeRoom() {
    const createRoomBtn = document.getElementById('createRoomBtn');
    const joinRoomBtn = document.getElementById('joinRoomBtn');
    const roomIdInput = document.getElementById('roomIdInput');
    const roomInfo = document.getElementById('roomInfo');
    const currentRoomIdSpan = document.getElementById('currentRoomId');
    const usersCountSpan = document.getElementById('usersCount');
    const copyRoomIdBtn = document.getElementById('copyRoomIdBtn');
    const mainPlayer = document.querySelector('media-player');
    const toastLiveExample = document.getElementById('liveToast')

    // 1. Создание комнаты
    createRoomBtn.addEventListener('click', async () => {
        if (!playerData) {
            alert('Сначала загрузите данные о видео');
            return;
        }

        // console.log("Player", mainPlayer);
        // console.log("Playing?", !mainPlayer.paused);
        // console.log("src: ", mainPlayer.src);

        try {
            const response = await fetch('/video_room/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // 'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    video_url: playerData.link,
                    stream_url: streamUrl,
                    anime_title: animeName,
                    current_season: currentSeason,
                    current_episode: currentEpisode,
                    current_translator: currentTranslator,
                    is_playing: !mainPlayer.paused,
                    current_time: mainPlayer.currentTime,
                })
            });

            const data = await response.json();
            currentRoomId = data.room_id;
            isRoomOwner = true;

            // Обновляем UI
            currentRoomIdSpan.textContent = currentRoomId;
            roomInfo.classList.remove('d-none');
            connectToRoom(currentRoomId);

        } catch (error) {
            console.error('Ошибка создания комнаты:', error);
        }
    });

    // 2. Присоединение к комнате
    joinRoomBtn.addEventListener('click', async () => {
        const roomId = roomIdInput.value.trim();
        if (!roomId) return;

        try {
            const response = await fetch(`/video_room/${roomId}/info/`);
            const data = await response.json();

            if (data.exists) {
                currentRoomId = roomId;
                isRoomOwner = false;

                // Обновляем UI
                currentRoomIdSpan.textContent = currentRoomId;
                roomInfo.classList.remove('d-none');
                connectToRoom(roomId);

                // Если нужно сменить эпизод/озвучку под комнату
                // if (playerData.type === 'tv_series') {
                //     console.log("МЕНЯЕМ под tv_series")
                //     updatePlayerToMatchRoom(data);
                // }
            } else {
                alert('Комната не найдена!');
            }
        } catch (error) {
            console.error('Ошибка подключения:', error);
        }
    });

    // 3. Копирование ID комнаты
    copyRoomIdBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(currentRoomId);
        const originalText = copyRoomIdBtn.textContent;
        copyRoomIdBtn.textContent = 'Скопировано!';
        setTimeout(() => copyRoomIdBtn.textContent = originalText, 2000);
    });

    function connectToRoom(roomId) {
        if (socket != null) {
            socket.close();
        }

        socket = new WebSocket(
            `ws://${window.location.host}/ws/video_room/${roomId}/`  // window.location.host - localhost в моём случае
        );

        mainPlayer.addEventListener('play', () => {
            if (isSyncing) {
                isSyncing = false;
                return;
            }
            mainPlayer.paused = true;
            isSyncing = true;
            console.log("Starting play");
            const eventData = {
              type: 'sync_event',
              event: "play",
              time: mainPlayer.currentTime
            };
            socket.send(JSON.stringify(eventData));
            mainPlayer.paused = false;
        });

        mainPlayer.addEventListener('pause', () => {
            if (isSyncing) {
                isSyncing = false;
                return;
            }
            isSyncing = true;
            console.log("Paused.");
            const eventData = {
              type: 'sync_event',
              event: "pause",
              time: mainPlayer.currentTime
            };
            socket.send(JSON.stringify(eventData));
        });

        mainPlayer.addEventListener('waiting', () => {
            console.log("loading media...");
        });

        // Когда получаем ответ от вебсокета
        socket.onmessage = function (message) {
            const data = JSON.parse(message.data);

            if (data.type === 'initial_state') {

                if (isRoomOwner) {
                    return;
                }

                // Первоначальная синхронизация

                // Нужно, ибо если втупую поставить src и после этого время, то оно не сработает. Баг или нет хз.
                // Видимо плеер не успевает прогрузить видос
                mainPlayer.addEventListener('loaded-metadata', () => {
                    mainPlayer.currentTime = data.current_time;
                    mainPlayer.paused = !data.is_playing;
                });

                mainPlayer.src = [
                    {
                        src: data.stream_url["1080p"],
                        type: 'video/mp4',
                        width: 1920,
                        height: 1080,
                    },
                    {
                        src: data.stream_url["720p"],
                        type: 'video/mp4',
                        width: 1280,
                        height: 720,
                    },
                    {
                        src: data.stream_url["360p"],
                        type: 'video/mp4',
                        width: 640,
                        height: 360,
                    },
                ];

            } else if (data.type === 'sync_event') {
                if (isSyncing) {
                    isSyncing = false;
                    return;
                }

                isSyncing = true;
                // Обработка событий от других участников
                if (data.event === "play") {
                    mainPlayer.paused = false;
                }
                else if (data.event === "pause") {
                    mainPlayer.paused = true;
                    mainPlayer.currentTime = data.time;
                }
            }
            else if (data.type === 'users_update') {
                usersCountSpan.value = data.count;
                const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastLiveExample);
                toastBootstrap.show();
            }
        };

        socket.onclose = function (e) {
            console.error('Socket closed unexpectedly');
        };
    }

    function sync_video(data) {

    }

}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {

    // Инициализируем плеер
    const player = initializePlayer(animeName, animeLink);

    const room = initializeRoom();
});
