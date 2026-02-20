from django.urls import path

from anime import views, consumers

urlpatterns = [
    path('', views.index, name='index'),
    path('anime/<int:anime_id>/', views.info, name="info"),
    path('anime/getPlayerInfo/', views.player_info, name='player_info'),
    path('anime/getStream/', views.get_stream, name='get_stream'),
    path('video_room/create/', views.create_video_room, name='create_video_room'),
    path('video_room/<str:room_id>/info/', views.get_room_info, name='get_room_info'),
    path('search/', views.search_view, name='search'),
]

websocket_urlpatterns = [
    path('ws/video_room/<uuid:room_id>/', consumers.VideoRoomConsumer.as_asgi()),
]
