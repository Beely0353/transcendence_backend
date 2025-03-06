import json
import asyncio
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .pong import pong_game


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = 'test'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

        self.send(text_data=json.dumps({
            'type':'connection_established',
            'message':'You are now connected!'
        }))

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':'chat_message',
                'message':message
            }
        )

    def chat_message(self, event):
        message = event['message']

        self.send(text_data=json.dumps({
            'type':'chat',
            'message':message
        }))



class PongConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f"pong_room_{self.match_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        self.game = await self.get_active_game(self.match_id)
        if not self.game:
            await self.send(text_data=json.dumps({"error": "Aucun round en cours"}))
            await self.close()
            return
        
        self.running = True
        self.periodic_task = asyncio.create_task(self.send_periodic_data())

    async def send_periodic_data(self):
        """ Envoie les mises à jour du jeu en temps réel """
        while self.running:
            ball_x, ball_y = await pong_game(self.game.id)
            self.game = await self.get_game(self.game.id)
            await self.send(text_data=json.dumps({
                'type': 'data_pong',
                'x': self.game.ball_position.get('x', 0),
                'y': self.game.ball_position.get('y', 0),
                'paddleL': self.game.paddle_position.get('paddle_l', 0),
                'paddleR': self.game.paddle_position.get('paddle_r', 0)
            }))

            await asyncio.sleep(1 / 60)

    async def receive(self, text_data):
        """ Gère les mouvements des joueurs """
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')
        move = text_data_json.get('type')

        if action == 'move_up':
            if move == 'paddle_l':
                self.game.paddle_position['paddle_l'] -= 5
            if move == 'paddle_r':
                self.game.paddle_position['paddle_r'] -= 5
        elif action == 'move_down':
            if move == 'paddle_l':
                self.game.paddle_position['paddle_l'] += 5
            if move == 'paddle_r':
                self.game.paddle_position['paddle_r'] += 5

        await self.save_game_state()

    async def disconnect(self, close_code):
        """ Gère la déconnexion du joueur """
        self.running = False
        if hasattr(self, 'periodic_task'):
            self.periodic_task.cancel()

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # ---------------------
    # Méthodes Utilitaires
    # ---------------------
    
    @sync_to_async
    def get_active_game(self, match_id):
        from pong.models import Game
        return Game.objects.filter(match__id=match_id, status="En cours").first()

    @sync_to_async
    def save_game_state(self):
        self.game.save()
