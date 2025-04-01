from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from .models import Player

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    try:
        player = user.player_profile
        player.online = True
        player.last_seen = None
        player.save()
    except Player.DoesNotExist:
        pass

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    try:
        player = user.player_profile
        player.online = False
        player.last_seen = timezone.now()
        player.save()
    except Player.DoesNotExist:
        pass
