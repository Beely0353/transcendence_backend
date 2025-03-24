# Django imports
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import models
import uuid

# DRF imports
from rest_framework import status, viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken

# Local imports
from .models import Player, Game, Match, Tournament, Friendship, Block
from . import serializers

# ==============================
# API DJANGO REST FRAMEWORK
# ==============================

class AdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]

class PlayerViewSet(AdminViewSet):
    queryset = Player.objects.all()
    serializer_class = serializers.PlayerSerializer

class GameViewSet(AdminViewSet):
    queryset = Game.objects.all()
    serializer_class = serializers.GameSerializer

class MatchViewSet(AdminViewSet):
    queryset = Match.objects.all()
    serializer_class = serializers.MatchSerializer

class TournamentViewSet(AdminViewSet):
    queryset = Tournament.objects.all()
    serializer_class = serializers.TournamentSerializer

# ==============================
# AUTHENTIFICATION API
# ==============================


#===CRUD PLAYER====

class PlayerRegister_api(generics.CreateAPIView):
    serializer_class = serializers.PlayerRegisterSerializer
    permission_classes = [AllowAny]

class PlayerList_api(generics.ListAPIView):
    queryset = Player.objects.all()
    serializer_class = serializers.PlayerSerializer
    permission_classes = [AllowAny]

class PlayerDetail_api(generics.RetrieveAPIView):
    queryset = Player.objects.all()
    serializer_class = serializers.PlayerSerializer
    permission_classes = [AllowAny]

class PlayerUpdateName_api(generics.UpdateAPIView):
    serializer_class = serializers.PlayerUpdateNameSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.player_profile
    
class PlayerUpdatePWD_api(generics.UpdateAPIView):
    serializer_class = serializers.PlayerUpdatePWDSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class PlayerDelete_api(generics.DestroyAPIView):
    serializer_class = serializers.PlayerDeleteSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        instance.delete()

class PlayerLogin_api(generics.CreateAPIView):
    serializer_class = serializers.PlayerLoginSerializer
    permission_classes = [AllowAny]

class PlayerLogout_api(generics.CreateAPIView):
    serializer_class = serializers.PlayerLogoutSerializer
    permission_classes = [IsAuthenticated]

# ============CRUD FriendShip================

class SendFriendRequest_api(generics.CreateAPIView):
    serializer_class = serializers.SendFriendRequestSerializer
    permission_classes = [IsAuthenticated]

class FriendRequestAccept_api(generics.UpdateAPIView):
    serializer_class = serializers.FriendRequestAcceptSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    queryset = Friendship.objects.all()

    def get_object(self):
        return Friendship.objects.get(id=self.kwargs['pk'])

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"code": 1000}, status=status.HTTP_200_OK)
    
class FriendRequestReject_api(generics.DestroyAPIView):
    serializer_class = serializers.FriendRequestRejectSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    queryset = Friendship.objects.all()

    def get_object(self):
        return Friendship.objects.get(id=self.kwargs['pk'])

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        serializer.is_valid(raise_exception=True)  
        self.perform_destroy(instance)
        return Response({"code": 1000}, status=status.HTTP_200_OK)

class FriendRequestCancel_api(generics.DestroyAPIView):
    serializer_class = serializers.FriendRequestCancelSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    queryset = Friendship.objects.all()

    def get_object(self):
        request_user = self.request.user
        obj = super().get_object()

        # Validation personnalisée
        if obj.player_1.user != request_user:
            raise serializers.ValidationError({"code": 1023})  # "Seul l'expéditeur peut annuler cette demande."
        if obj.status != 'pending':
            raise serializers.ValidationError({"code": 1021})  # "Cette demande a déjà été traitée."

        return obj

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"code": 1000}, status=status.HTTP_200_OK)
    
class FriendRemove_api(generics.DestroyAPIView):
    serializer_class = serializers.FriendshipRemoveSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id' 
    queryset = Friendship.objects.all()

    def get_object(self):
        player = self.request.user.player_profile
        obj = super().get_object()

        # Validation personnalisée
        if obj.status != 'accepted':
            raise serializers.ValidationError({"code": 1030})  # "Cette relation n'est pas une amitié acceptée."
        if obj.player_1 != player and obj.player_2 != player:
            raise serializers.ValidationError({"code": 1025})  # "Vous n'êtes pas amis avec ce joueur."

        return obj

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        Friendship.objects.filter(
            status='accepted',
            player_1=instance.player_1,
            player_2=instance.player_2
        ).delete()
        Friendship.objects.filter(
            status='accepted',
            player_1=instance.player_2,
            player_2=instance.player_1
        ).delete()
        return Response({"code": 1000}, status=status.HTTP_200_OK)


class FriendshipList_api(generics.ListAPIView):
    serializer_class = serializers.FriendshipListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.player_profile
        return Friendship.objects.filter(
            models.Q(player_1=user) | models.Q(player_2=user)
        )

# ============CRUD Block================

class BlockPlayer_api(generics.CreateAPIView):
    serializer_class = serializers.BlockPlayerSerializer
    permission_classes = [IsAuthenticated]


class BlockListView(generics.ListAPIView):
    serializer_class = serializers.BlockListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.player_profile
        return Block.objects.filter(blocker=user)

class UnblockPlayerView(generics.DestroyAPIView):
    serializer_class = serializers.UnblockPlayerSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    queryset = Block.objects.all()

    def get_object(self):
        blocker = self.request.user.player_profile
        obj = super().get_object()

        # Validation personnalisée
        if obj.blocker != blocker:
            raise serializers.ValidationError({"code": 1028})  # "Vous n'avez pas bloqué ce joueur."
        
        return obj

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"code": 1000}, status=status.HTTP_200_OK)
