from django.contrib import admin
from .models import Player, Tournament, Match, Game, Friendship, Block


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'online')

class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['id', 'player_1', 'player_2', 'status', 'created_at']

class BlockAdmin(admin.ModelAdmin):
    list_display = ['id']

admin.site.register(Player, PlayerAdmin)
admin.site.register(Tournament)
admin.site.register(Match)
admin.site.register(Game)
admin.site.register(Friendship)
admin.site.register(Block)
