from django.db import models
from django.contrib.auth.models import User
import uuid
import random


class StatusChoices(models.TextChoices):
    EN_COURS = 'En cours'
    PAUSE = 'Pause'
    TERMINEE = 'Terminée'

class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=255)
    victory = models.PositiveIntegerField(default=0)
    defeat = models.PositiveIntegerField(default=0)
    online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    description = models.TextField(max_length=500, blank=True, default="")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, default='avatars/default.jpg')

    friends = models.ManyToManyField('self', symmetrical=False, through='Friendship', related_name='friends_of')

    def __str__(self):
        return self.name

class Friendship(models.Model):
    player_1 = models.ForeignKey(Player, related_name='friendship_requests', on_delete=models.CASCADE, null=True, blank=True)
    player_2 = models.ForeignKey(Player, related_name='friendships', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending',
        max_length=10
    )

    class Meta:
        unique_together = ('player_1', 'player_2')

    def __str__(self):
        return f'{self.player_1.name} - {self.player_2.name} ({self.status})'

class Block(models.Model):
    blocker = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocked_by')  # Celui qui bloque
    blocked = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='blocked_players')  # Celui qui est bloqué
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['blocker', 'blocked']  # Un joueur ne peut bloquer un autre joueur qu'une seule fois

    def __str__(self):
        return f'{self.blocker.name} blocked {self.blocked.name}'



class Tournament(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    date_played = models.DateTimeField(auto_now_add=True)
    players = models.ManyToManyField(Player, related_name='tournaments')
    winner = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='tournaments_won')
    status = models.CharField(choices=StatusChoices.choices, max_length=10, default=StatusChoices.EN_COURS)
    
class Match(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches', null=True, blank=True)
    round_number = models.PositiveIntegerField()
    player_1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='matches_as_player_1')
    player_2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='matches_as_player_2', null=True, blank=True)
    winner = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='matches_won')
    status = models.CharField(choices=StatusChoices.choices, max_length=10, default=StatusChoices.EN_COURS)

    class TypeChoices(models.TextChoices):
        IA = 'IA'
        PRIVEE = 'Privée'
        PUBLIC = 'Public'
        TOURNAMENT = 'Tournois'

    type = models.CharField(choices=TypeChoices.choices, max_length=10, default=TypeChoices.PRIVEE)
    private_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, null=True, blank=True)



class Game(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    match = models.ForeignKey(Match, on_delete=models.SET_NULL, related_name='games', null=True, blank=True)
    player_1 = models.ForeignKey(Player, on_delete=models.SET_NULL, related_name='games_as_player_1', null=True, blank=True)
    player_2 = models.ForeignKey(Player, on_delete=models.SET_NULL, related_name='games_as_player_2', null=True, blank=True)
    score_player_1 = models.PositiveIntegerField(default=0)
    score_player_2 = models.PositiveIntegerField(default=0)
    date_played = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=StatusChoices.choices, max_length=10, default=StatusChoices.EN_COURS)
    ball_position = models.JSONField(default=dict)
    paddle_position = models.JSONField(default=dict)
    ball_dx = models.IntegerField(default=1)
    ball_dy = models.IntegerField(default=0) 

    def initialize_ball_direction(self):
        self.ball_dx = random.choice([1, -1])
        self.ball_dy = random.choice([1, -1, 0]) 
        self.save()
