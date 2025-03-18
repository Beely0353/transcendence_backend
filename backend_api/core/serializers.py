from rest_framework import serializers
from .models import Player, Game, Match, Tournament, Friendship, Block
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from core.validators import validate_strong_password

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__'

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

class PlayerRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'token']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"code": 1001})  # Les mots de passe ne correspondent pas.
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"code": 1002}) #Ce nom d'utilisateur est déjà pris.
        validate_strong_password(data['password']) # À voir dans validators.py
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        Player.objects.create(user=user, name=validated_data['username'])
        return user

    def get_token(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class PlayerUpdateNameSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True)

    class Meta:
        model = Player
        fields = ['name', 'current_password']

    def validate(self, data):
        user = self.context['request'].user
        if not check_password(data['current_password'], user.password):
            raise serializers.ValidationError({"code": 1008})  # Mot de passe incorrect.
        if User.objects.filter(username=data['name']).exists():
            raise serializers.ValidationError({"code": 1002}) #Ce nom d'utilisateur est déjà pris.
        return data

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
    
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

class PlayerDeleteSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user
        if not user.check_password(data['password']):
            raise serializers.ValidationError({"code": 1008})  # Mot de passe incorrect.
        return data

#===CRUD FriendShip====

class SendFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friendship
        fields = ['player_1','player_2','status']

    def validate(self, data):
        user = self.context['request'].user
        player_2 = data.get('player_2')

        if user == player_2:
            raise serializers.ValidationError("Vous ne pouvez pas envoyer une demande d'ami à vous-même.")
        
        if Friendship.objects.filter(player_1=user, player_2=player_2, status='pending').exists():
            raise serializers.ValidationError("Une demande d'ami a déjà été envoyée à ce joueur.")
        
        if Friendship.objects.filter(player_1=player_2, player_2=user, status='pending').exists():
            raise serializers.ValidationError("Vous avez déjà reçu une demande d'ami de ce joueur.")

        if Friendship.objects.filter(
            status='accepted',
            player_1__in=[user, player_2],
            player_2__in=[user, player_2]
        ).exists():
            raise serializers.ValidationError("Vous êtes déjà amis avec ce joueur.")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        player_2 = validated_data.pop('player_2')
        friendship = Friendship.objects.create(player_1=user, player_2=player_2, status='pending')
        return friendship


class RespondFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model   = Friendship
        fields  = ['status']

    def validate(self, data):
        user = self.context['request'].user
        friendship = self.instance

        if user != friendship.player_1 and user != friendship.player_2:
            raise serializers.ValidationError("Vous n'êtes pas autorisé à répondre à cette demande.")
        if friendship.status != 'pending':
            raise serializers.ValidationError("Cette demande d'ami n'est plus en attente.")

        return data
    
    def update(self, instance, validated_data):
        instance.status = validated_data['status']
        instance.save()
        return instance
         
