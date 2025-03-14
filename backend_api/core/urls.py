from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# ===========================
# CONFIGURATION DU ROUTEUR DRF
# ===========================

router = DefaultRouter()
router.register(r'players', views.PlayerViewSet)
router.register(r'games', views.GameViewSet)
router.register(r'matches', views.MatchViewSet, basename='match')
router.register(r'tournaments', views.TournamentViewSet)

# ===========================
# DEFINITION DES URLS
# ===========================

urlpatterns = [
    # Routes DRF avec router
    path('api/', include(router.urls)),

    # CRUD PLAYER
    path('api/register/', views.PlayerRegister_api.as_view(), name='register_api'),
    path('api/player/<int:pk>/', views.PlayerDetail_api.as_view(), name='player-detail'),
    path('api/player/update-name/', views.PlayerUpdateName_api.as_view(), name='player-update'),
    path('api/player/update-PWD/', views.PlayerUpdatePWD_api.as_view(), name='player-update'),
    path('api/player/delete/', views.PlayerDelete_api.as_view(), name='player-delete'),

    # Authentification API (Inscription & Connexion)
    path('api/login/', views.login_api, name='login_api'),
    path('api/logout/', views.logout_api, name='logout_api'),

    # JWT Token Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/send_friend_request/', views.SendFriendRequest.as_view(), name='send_friend_request'),
    path('api/accept_friend_request/', views.AcceptFriendRequest.as_view(), name='accept_friend_request'),
    path('api/reject_friend_request/', views.RejectFriendRequest.as_view(), name='reject_friend_request'),
    path('api/block_player/', views.BlockPlayer.as_view(), name='block_player'),
    path('api/unblock_player/', views.UnblockPlayer.as_view(), name='unblock_player'),
]
