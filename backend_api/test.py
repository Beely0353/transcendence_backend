from rest_framework import serializers
from .models import Friendship, Player, Block  # Assurez-vous que Block est importé

class SendFriendRequestSerializer(serializers.ModelSerializer):
    player_2 = serializers.IntegerField(write_only=True)  # On attend l'ID du joueur cible

    class Meta:
        model = Friendship
        fields = ['player_2']  # player_1 est implicite via l'utilisateur connecté

    def validate(self, data):
        player_1 = self.context['request'].user  # L'utilisateur connecté est player_1
        player_2_id = data.get('player_2')

        try:
            player_2 = Player.objects.get(id=player_2_id)  # Convertit l'ID en instance Player
        except Player.DoesNotExist:
            raise serializers.ValidationError({"code": 1014, "message": "Le joueur cible n'existe pas."})

        # Vérification : pas d'auto-demande
        if player_1 == player_2.user:  # Compare avec l'utilisateur lié au Player
            raise serializers.ValidationError({"code": 1015, "message": "Vous ne pouvez pas envoyer une demande d'ami à vous-même."})

        # Vérification : demande en attente de player_1 à player_2
        if Friendship.objects.filter(player_1=player_1.player_profile, player_2=player_2, status='pending').exists():
            raise serializers.ValidationError({"code": 1016, "message": "Une demande d'ami a déjà été envoyée à ce joueur."})

        # Vérification : demande en attente de player_2 à player_1
        if Friendship.objects.filter(player_1=player_2, player_2=player_1.player_profile, status='pending').exists():
            raise serializers.ValidationError({"code": 1017, "message": "Vous avez déjà reçu une demande d'ami de ce joueur."})

        # Vérification : déjà amis (dans les deux sens)
        if Friendship.objects.filter(
            status='accepted',
            player_1__in=[player_1.player_profile, player_2],
            player_2__in=[player_1.player_profile, player_2]
        ).exists():
            raise serializers.ValidationError({"code": 1002, "message": "Vous êtes déjà amis avec ce joueur."})

        # Vérification : blocage par player_1
        if Block.objects.filter(blocker=player_1.player_profile, blocked=player_2).exists():
            raise serializers.ValidationError({"code": 1018, "message": "Vous avez bloqué ce joueur."})

        # Vérification : blocage par player_2
        if Block.objects.filter(blocker=player_2, blocked=player_1.player_profile).exists():
            raise serializers.ValidationError({"code": 1019, "message": "Ce joueur vous a bloqué."})

        return data

    def create(self, validated_data):
        player_1 = self.context['request'].user.player_profile  # Récupère l'instance Player de l'utilisateur connecté
        player_2_id = validated_data.pop('player_2')
        player_2 = Player.objects.get(id=player_2_id)  # Convertit l'ID en instance Player
        friendship = Friendship.objects.create(player_1=player_1, player_2=player_2, status='pending')
        return friendship

    def to_representation(self, instance):
        return {"code": 1000}  # Succès de la création
