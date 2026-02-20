import json
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room


class VideoRoomConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'video_room_{self.room_id}'

        if not await self.room_exists():
            await self.close(
                code=404,
                reason=f'Room {self.room_id} does not exist'
            )
            return

        await self.increment_participants()
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        print("Sending initial state")
        await self.send_initial_state()

    async def disconnect(self, close_code):
        await self.decrement_participants()
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'sync_event':
            await self.handle_sync_event(data)
        elif data['type'] == 'episode_change':
            await self.update_episode(data['episode'], data['translator'])
        elif data['type'] == 'season_change':
            await self.update_season(data['season'])

    async def handle_sync_event(self, data):
        await self.update_room_state(
            current_time=data.get('time'),
            is_playing=data['event'] == 'play'
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_event',
                'data': {
                    'type': 'sync_event',
                    'event': data['event'],
                    'time': data.get('time')
                }
            }
        )

    async def broadcast_event(self, event):
        await self.send(text_data=json.dumps(event['data']))

    async def send_initial_state(self):
        state = await self.get_room_state()
        await self.send(text_data=json.dumps({
            'type': 'initial_state',
            'stream_url': state["stream_url"],
            'current_time': state['current_time'],
            'is_playing': state['is_playing'],
            'current_season': state['current_season'],
            'current_episode': state['current_episode'],
            'current_translator': state['current_translator']
        }))

        # Обновляем счетчик участников для всех
        count = await self.get_participants_count()  # Maybe remove?
        # user = self.scope['user']
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_event',
                'data': {
                    'type': 'users_update',
                    'count': count,
                }
            }
        )

    @database_sync_to_async
    def room_exists(self):
        return Room.objects.filter(id=self.room_id).exists()

    @database_sync_to_async
    def get_room_state(self) -> dict:
        room = Room.objects.get(id=self.room_id)
        return {
            'stream_url': room.stream_url,
            'current_time': room.current_time,
            'is_playing': room.is_playing,
            'current_season': room.current_season,
            'current_episode': room.current_episode,
            'current_translator': room.current_translator
        }

    @database_sync_to_async
    def update_room_state(self, current_time=None, is_playing=None):
        room = Room.objects.get(id=self.room_id)
        if current_time is not None:
            room.current_time = current_time
        if is_playing is not None:
            room.is_playing = is_playing
        room.save()

    @database_sync_to_async
    def update_episode(self, episode: int, translator: int) -> None:
        room = Room.objects.get(id=self.room_id)
        room.current_episode = episode
        room.current_translator = translator
        room.save()

    @database_sync_to_async
    def update_season(self, season: int) -> None:
        room = Room.objects.get(id=self.room_id)
        room.season = season
        room.save()

    @database_sync_to_async
    def increment_participants(self):
        room = Room.objects.get(id=self.room_id)
        room.participants_count += 1
        room.save()

    @database_sync_to_async
    def decrement_participants(self):
        room = Room.objects.get(id=self.room_id)
        room.participants_count = max(0, room.participants_count - 1)
        room.save()

    @database_sync_to_async
    def get_participants_count(self):
        return Room.objects.get(id=self.room_id).participants_count
