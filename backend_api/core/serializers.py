import uuid
from rest_framework import serializers
from django.db import models
from django.utils import timezone
from .models import Player, Game, Match, Tournament, Friendship, Block
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.hashers import check_password
from core.validators import validate_strong_password
from django.contrib.auth import authenticate
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'created_at', 'name', 'victory', 'defeat', 'avatar', 'online', 'last_seen', 'description']

    def to_representation(self, instance):
        fields = super().to_representation(instance)
        request = self.context.get('request')
        user = request.user if request and hasattr(request, 'user') else None


        if not user or not user.is_authenticated:
            del fields['online']
            del fields['last_seen']
            del fields['description']
            return fields

        try:
            current_player = user.player_profile
        except AttributeError:
            del fields['online']
            del fields['last_seen']
            del fields['description']
            return fields

        # Vérifier si c’est le joueur lui-même ou un ami
        is_self = current_player.id == instance.id
        friendship = Friendship.objects.filter(
            models.Q(player_1=current_player, player_2=instance, status='accepted') |
            models.Q(player_1=instance, player_2=current_player, status='accepted')
        ).first()
        is_friend = is_self or (friendship is not None)

        if not is_friend:
            del fields['online']
            del fields['last_seen']
            del fields['description']

        return fields

class GameSerializer(serializers.ModelSerializer):
    player_1 = PlayerSerializer(read_only=True)
    player_2 = PlayerSerializer(read_only=True)

    class Meta:
        model = Game
        fields = '__all__'

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'


class TournamentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__'

class FriendshipSerializer(serializers.ModelSerializer):
    player_1_name = serializers.CharField(source='player_1.name')
    player_2_name = serializers.CharField(source='player_2.name')
    status = serializers.CharField()

    class Meta:
        model = Friendship
        fields = ['player_1_name', 'player_2_name', 'status', 'created_at']


class BlockSerializer(serializers.ModelSerializer):
    blocker_name = serializers.CharField(source='blocker.name')
    blocked_name = serializers.CharField(source='blocked.name')

    class Meta:
        model = Block
        fields = ['blocker_name', 'blocked_name', 'created_at']

#===CRUD PLAYER====

class PlayerRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, allow_blank=True, allow_null=True)
    password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if not data.get('username'):
            raise serializers.ValidationError({"code": 1009}) # Nom d'utilisateur requis.
        if not data.get('password') or not data.get('password2'):
            raise serializers.ValidationError({"code": 1010}) # Mot de passe requis.
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"code": 1001})  # Les mots de passe ne correspondent pas.
        if Player.objects.filter(name=data['username']).exists():
            raise serializers.ValidationError({"code": 1002})  # Ce nom d'utilisateur est déjà pris.
        validate_strong_password(data['password'])
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=f"temp_{uuid.uuid4().hex[:8]}",
            password=validated_data['password']
        )
        player = Player.objects.create(user=user, name=validated_data['username'])
        user.username = f"player_{player.id}"
        user.save()
        return user

    def to_representation(self, instance):
            return {"code": 1000}

class PlayerUpdateInfoSerializer(serializers.ModelSerializer):
    description = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    online = serializers.BooleanField(write_only=True, required=False, allow_null=True)
    avatar = serializers.ImageField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Player
        fields = ['online', 'description', 'avatar']

    def validate(self, data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError({"code": 1030})

        instance = self.instance
        if instance != request.user.player_profile:
            raise serializers.ValidationError({"code": 1031})

        avatar = data.get('avatar')
        if avatar:
            allowed_extensions = ['jpg', 'jpeg', 'png']
            if not avatar.name.lower().endswith(tuple(allowed_extensions)):
                raise serializers.ValidationError({"code": 1032})

            max_weight = 2 * 1024 * 1024  # 2 Mo en octets
            if avatar.size > max_weight:
                raise serializers.ValidationError({"code": 1033})

            try:
                img = Image.open(avatar)
                max_dimensions = (500, 500)
                if img.width > max_dimensions[0] or img.height > max_dimensions[1]:
                    raise serializers.ValidationError({"code": 1034})
            except Exception:
                raise serializers.ValidationError({"code": 1035})

        return data

    def update(self, instance, validated_data):
        description = validated_data.get('description')
        online = validated_data.get('online')
        avatar = validated_data.get('avatar')
        if avatar is not None:
            instance.avatar = avatar
        if description is not None:
            instance.description = description
        if online is not None:
            if online:
                instance.online = True
                instance.last_seen = None
            elif online is False:
                instance.online = False
                instance.last_seen = timezone.now()    
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {"code": 1000}

class PlayerUpdateNameSerializer(serializers.ModelSerializer):
    name             = serializers.CharField(write_only=True)
    current_password = serializers.CharField(write_only=True)

    class Meta:
        model = Player
        fields = ['name', 'current_password']

    def validate(self, data):
        user = self.context['request'].user
        if not check_password(data['current_password'], user.password):
            raise serializers.ValidationError({"code": 1008})  # Mot de passe incorrect.
        if Player.objects.filter(name=data['name']).exists():
            raise serializers.ValidationError({"code": 1002}) #Ce nom d'utilisateur est déjà pris.
        return data

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {"code": 1000}
    
class PlayerUpdatePWDSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_pwd1 = serializers.CharField(write_only=True)
    new_pwd2 = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['current_password']):
            raise serializers.ValidationError({"code": 1008})  # Mot de passe incorrect.
        if data['new_pwd1'] != data['new_pwd2']:
            raise serializers.ValidationError({"code": 1001})  # Les mots de passe ne correspondent pas.
        validate_strong_password(data['new_pwd1'])   # À voir dans validators.py
        return data

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_pwd1'])
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {"code": 1000}

class PlayerDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['password']):
            raise serializers.ValidationError({"code": 1008})  # Mot de passe incorrect.
        return data
    
    def to_representation(self, instance):
        return {"code": 1000}

class PlayerLoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, allow_blank=True, allow_null=True)

    def validate(self, data):
        player_name = data.get('username')
        password = data.get('password')

        if not player_name:
            raise serializers.ValidationError({"code": 1009}) # Nom requis
        if not password:
            raise serializers.ValidationError({"code": 1010}) # Mot de passe requis


        try:
            player = Player.objects.get(name=player_name)
        except Player.DoesNotExist:
            raise serializers.ValidationError({"code": 1013}) # Nom ou mot de passe incorrect
    
        username = player.user.username
        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError({"code": 1013}) # Nom ou mot de passe incorrect

        player.online = True
        player.last_seen = None
        player.save()

        data['user'] = user
        data['player'] = player
        return data

    def create(self, validated_data):
        player = validated_data['player']
        return player

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance.user)
        return {
            "code": 1000,
            "player": instance.id,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }

class PlayerLogoutSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, allow_blank=True, allow_null=True)

    def validate(self, data):
        token = data.get('token')

        if not token:
            raise serializers.ValidationError({"code": 1011})

        try:
            refresh_token = RefreshToken(token)
            refresh_token.blacklist()
        except TokenError:
            raise serializers.ValidationError({"code": 1012})

        return data

    def create(self, validated_data):
        return {"success": True}

    def to_representation(self, instance):
        return {"code": 1000}

#===CRUD FriendShip====

class SendFriendRequestSerializer(serializers.ModelSerializer):
    player_2 = serializers.IntegerField(write_only=True)

    class Meta:
        model = Friendship
        fields = ['player_2']

    def validate(self, data):
        player_1 = self.context['request'].user
        player_2_id = data.get('player_2')

        try:
            player_2 = Player.objects.get(id=player_2_id)
        except Player.DoesNotExist:
            raise serializers.ValidationError({"code": 1014})  # Le joueur cible n'existe pas.
        if player_1 == player_2.user:
            raise serializers.ValidationError({"code": 1015})  # Vous ne pouvez pas envoyer une demande d'ami à vous-même.
        if Friendship.objects.filter(player_1=player_1.player_profile, player_2=player_2, status='pending').exists():
            raise serializers.ValidationError({"code": 1016})  # Une demande d'ami a déjà été envoyée à ce joueur.
        if Friendship.objects.filter(player_1=player_2, player_2=player_1.player_profile, status='pending').exists():
            raise serializers.ValidationError({"code": 1017})  # Vous avez déjà reçu une demande d'ami de ce joueur.
        if Friendship.objects.filter(
            status='accepted',
            player_1__in=[player_1.player_profile, player_2],
            player_2__in=[player_1.player_profile, player_2]
        ).exists():
            raise serializers.ValidationError({"code": 1002})  # Vous êtes déjà amis avec ce joueur.
        if Block.objects.filter(blocker=player_1.player_profile, blocked=player_2).exists():
            raise serializers.ValidationError({"code": 1018})  # Vous avez bloqué ce joueur.
        if Block.objects.filter(blocker=player_2, blocked=player_1.player_profile).exists():
            raise serializers.ValidationError({"code": 1019})  # Ce joueur vous a bloqué.

        return data

    def create(self, validated_data):
        player_1 = self.context['request'].user.player_profile
        player_2_id = validated_data.pop('player_2')
        player_2 = Player.objects.get(id=player_2_id)
        friendship = Friendship.objects.create(player_1=player_1, player_2=player_2, status='pending')
        return friendship

    def to_representation(self, instance):
        return {"code": 1000} 


class FriendRequestAcceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = []

    def validate(self, data):
        friendship = self.instance
        request_user = self.context['request'].user

        if friendship.player_2.user != request_user:
            raise serializers.ValidationError({"code": 1020})  # "Seul le destinataire peut accepter cette demande."
        if friendship.status != 'pending':
            raise serializers.ValidationError({"code": 1021})  # "Cette demande a déjà été traitée."

        return data

    def update(self, instance, validated_data):
        instance.status = 'accepted'
        instance.save()
        Friendship.objects.get_or_create(
            player_1=instance.player_2,
            player_2=instance.player_1,
            defaults={'status': 'accepted'}
        )
        return instance

    def to_representation(self, instance):
        return {"code": 1000} 

class FriendRequestRejectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = []

    def to_representation(self, instance):
        return {"code": 1000}

class FriendRequestCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = []

    def to_representation(self, instance):
        return {"code": 1000}


class FriendshipRemoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = []

    def validate(self, data):
        return data

    def to_representation(self, instance):
        return {"code": 1000} 

class FriendshipListSerializer(serializers.ModelSerializer):
    player_1 = serializers.CharField(source='player_1.name', read_only=True)
    player_2 = serializers.CharField(source='player_2.name', read_only=True)

    class Meta:
        model = Friendship
        fields = ['id', 'player_1', 'player_2', 'status', 'created_at']


#===CRUD Block====

class BlockPlayerSerializer(serializers.ModelSerializer):
    blocked_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Block
        fields = ['blocked_id']

    def validate(self, data):
        blocker = self.context['request'].user.player_profile
        blocked_id = data.get('blocked_id')

        try:
            blocked = Player.objects.get(id=blocked_id)
        except Player.DoesNotExist:
            raise serializers.ValidationError({"code": 1014})  # "Le joueur cible n'existe pas."
        if blocker == blocked:
            raise serializers.ValidationError({"code": 1026})  # "Vous ne pouvez pas vous bloquer vous-même."
        if Block.objects.filter(blocker=blocker, blocked=blocked).exists():
            raise serializers.ValidationError({"code": 1027})  # "Ce joueur est déjà bloqué."


        Friendship.objects.filter(
            status='accepted',
            player_1__in=[blocker, blocked],
            player_2__in=[blocker, blocked]
        ).delete()
        Friendship.objects.filter(
            status='pending',
            player_1__in=[blocker, blocked],
            player_2__in=[blocker, blocked]
        ).delete()
        return data

    def create(self, validated_data):
        blocker = self.context['request'].user.player_profile
        blocked_id = validated_data.pop('blocked_id')
        blocked = Player.objects.get(id=blocked_id)
        block = Block.objects.create(blocker=blocker, blocked=blocked)
        return block

    def to_representation(self, instance):
        return {"code": 1000}


class BlockListSerializer(serializers.ModelSerializer):
    blocked = serializers.CharField(source='blocked.name', read_only=True)

    class Meta:
        model = Block
        fields = ['id', 'blocked', 'created_at']


class UnblockPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = []

    def to_representation(self, instance):
        return {"code": 1000}
