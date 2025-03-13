from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import Player

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    try:
        player = user.player_profile
        player.online = True
        player.save()
    except Player.DoesNotExist:
        pass

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    try:
        player = user.player_profile
        player.online = False
        player.save()
    except Player.DoesNotExist:
        pass
