from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/pong/game/(?P<match_id>\d+)/(?P<game_id>\d+)/$', consumers.PongConsumer.as_asgi()),
]
