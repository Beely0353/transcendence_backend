from django.contrib import admin
from .models import Player, Tournament, Match, Game, Friendship


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'online')

admin.site.register(Player, PlayerAdmin)
admin.site.register(Tournament)
admin.site.register(Match)
admin.site.register(Game)
admin.site.register(Friendship)
