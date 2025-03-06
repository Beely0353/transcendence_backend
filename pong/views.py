# Django imports
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
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
from .serializers import PlayerSerializer, GameSerializer, MatchSerializer, TournamentSerializer, FriendshipSerializer, RegisterSerializer

# ==============================
# VUES CLASSIQUES DJANGO
# ==============================

def home(request):
    """Vue de la page d'accueil."""
    return render(request, 'home.html')

def lobby_chat(request):
    return render(request, 'chat/lobby.html')

def lobby_pong(request):
    return render(request, 'pong/lobby.html')


# ==============================
# API DJANGO REST FRAMEWORK
# ==============================

class AdminViewSet(viewsets.ModelViewSet):
    """Gère les CRUD pour les modèles accessibles uniquement aux admins."""
    permission_classes = [IsAdminUser]

class PlayerViewSet(AdminViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

class GameViewSet(AdminViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer

class MatchViewSet(AdminViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

class TournamentViewSet(AdminViewSet):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer

# ==============================
# AUTHENTIFICATION API
# ==============================

class register_api(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return Response({"error": "Nom d'utilisateur et mot de passe requis."}, status=status.HTTP_400_BAD_REQUEST)


    user = authenticate(username=username, password=password)

    if user is None:
        return Response({"error": "Nom d'utilisateur ou mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)
    
    player, _ = Player.objects.get_or_create(user=user, name=user.username)
    refresh = RefreshToken.for_user(user)
    player_serializer = PlayerSerializer(player)

    return Response({
        "message": "Connexion réussie.",
        "player": player_serializer.data,
        "tokens": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
def logout_api(request):
    print("test")
    try:
        data = request.data
        token = data.get('token')
        
        if token is None:
            return Response({'error': 'Token manquant'}, status=status.HTTP_400_BAD_REQUEST)

        print("Token reçu:", token)
        refresh_token = RefreshToken(token)
        refresh_token.blacklist()

        return Response({'message': 'Déconnexion réussie'}, status=status.HTTP_200_OK)

    except InvalidToken:
        return Response({'error': 'Token invalide'}, status=status.HTTP_400_BAD_REQUEST)

# ==============================

class SendFriendRequest(APIView):
    def post(self, request, *args, **kwargs):
        sender = request.user.player_profile
        receiver_id = request.data.get('receiver_id')
        
        try:
            receiver = Player.objects.get(id=receiver_id)
        except Player.DoesNotExist:
            return Response({'error': 'Player not found'}, status=status.HTTP_400_BAD_REQUEST)

        # Vérification du blocage avant d'envoyer la demande d'ami
        if Block.objects.filter(blocker=receiver, blocked=sender).exists():
            return Response({'error': 'You have been blocked by this player, you cannot send a friend request.'}, 
                            status=status.HTTP_403_FORBIDDEN)

        # Code pour envoyer la demande d'ami ici

        return Response({'message': 'Friend request sent'}, status=status.HTTP_200_OK)
















# ==============================
# PAS FONCTIONNEL
# ==============================

class AcceptFriendRequest(APIView):
    def post(self, request, *args, **kwargs):
        player_1 = request.user.player_profile
        player_2_id = request.data.get('player_2_id')
        try:
            friendship = Friendship.objects.get(player_1=player_1, player_2__id=player_2_id, status='pending')
        except Friendship.DoesNotExist:
            return Response({'error': 'Friend request not found or already accepted/rejected'}, status=status.HTTP_400_BAD_REQUEST)

        # Accepter la demande d'ami
        friendship.status = 'accepted'
        friendship.save()

        return Response({'message': 'Friend request accepted'}, status=status.HTTP_200_OK)

class RejectFriendRequest(APIView):
    def post(self, request, *args, **kwargs):
        player_1 = request.user.player_profile
        player_2_id = request.data.get('player_2_id')
        try:
            friendship = Friendship.objects.get(player_1=player_1, player_2__id=player_2_id, status='pending')
        except Friendship.DoesNotExist:
            return Response({'error': 'Friend request not found or already accepted/rejected'}, status=status.HTTP_400_BAD_REQUEST)

        friendship.status = 'rejected'
        friendship.save()

        return Response({'message': 'Friend request rejected'}, status=status.HTTP_200_OK)


class BlockPlayer(APIView):
    def post(self, request, *args, **kwargs):
        blocker = request.user.player_profile
        blocked_id = request.data.get('blocked_id')
        try:
            blocked = Player.objects.get(id=blocked_id)
        except Player.DoesNotExist:
            return Response({'error': 'Player not found'}, status=status.HTTP_400_BAD_REQUEST)

        block, created = Block.objects.get_or_create(blocker=blocker, blocked=blocked)
        if not created:
            return Response({'error': 'Player is already blocked'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Player blocked'}, status=status.HTTP_201_CREATED)

class UnblockPlayer(APIView):
    def post(self, request, *args, **kwargs):
        blocker = request.user.player_profile
        blocked_id = request.data.get('blocked_id')
        try:
            block = Block.objects.get(blocker=blocker, blocked__id=blocked_id)
        except Block.DoesNotExist:
            return Response({'error': 'Player not found or not blocked'}, status=status.HTTP_400_BAD_REQUEST)
        
        block.delete()

        return Response({'message': 'Player unblocked'}, status=status.HTTP_200_OK)

# ==============================

class FriendListView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]  # Cela s'assure que l'utilisateur est authentifié avec JWT

    def get(self, request, *args, **kwargs):
        # On récupère le joueur actuellement connecté via son profil Player associé au User
        player = request.user.player_profile

        # Récupérer la liste des amis du joueur (en supposant que "friends" soit une ManyToManyField sur Player)
        friends = player.friends.all()

        # Sérialiser les amis récupérés
        serializer = PlayerSerializer(friends, many=True)

        # Retourner la réponse avec la liste des amis
        return Response(serializer.data)


# ==============================

class MatchViewSet(viewsets.ModelViewSet):
    """ API CRUD pour gérer les matchs """
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

    def create(self, request, *args, **kwargs):
        """ Personnalise la création d'un match en générant les rounds (Game) """
        data = request.data
        try:
            # 📌 1️⃣ Vérifier que les joueurs existent
            player_1 = Player.objects.get(id=data['player_1'])
            player_2 = Player.objects.get(id=data['player_2'])

            # 📌 2️⃣ Créer le match
            match = Match.objects.create(
                player_1=player_1,
                player_2=player_2,
                type=data.get('type', 'PRIVEE'),
                private_code=uuid.uuid4() if data.get('type') == 'PRIVEE' else None
            )

            # 📌 3️⃣ Créer les rounds (Game) associés
            number_of_games = data.get('rounds', 3)  # 3 rounds par défaut
            for _ in range(number_of_games):
                Game.objects.create(
                    match=match,
                    player_1=player_1,
                    player_2=player_2,
                    ball_position={'x': 400, 'y': 200},
                    paddle_position={'paddle_l': 150, 'paddle_r': 150}
                )

            return Response({
                'match_id': match.id,
                'ws_url': f"ws://127.0.0.1:8000/ws/pong/{match.id}/",
                'message': 'Match créé avec succès !'
            }, status=201)

        except Player.DoesNotExist:
            return Response({'error': 'Joueur introuvable'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
