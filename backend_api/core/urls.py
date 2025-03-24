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
    path('api/player', views.PlayerList_api.as_view(), name='player-detail'),
    path('api/player/<int:pk>/', views.PlayerDetail_api.as_view(), name='player-detail'),
    path('api/player/update-name/', views.PlayerUpdateName_api.as_view(), name='player-update-name'),
    path('api/player/update-PWD/', views.PlayerUpdatePWD_api.as_view(), name='player-update-pwd'),
    path('api/player/delete/', views.PlayerDelete_api.as_view(), name='player-delete'),

    # Authentification API
    path('api/login/', views.PlayerLogin_api.as_view(), name='login_api'),
    path('api/logout/', views.PlayerLogout_api.as_view(), name='logout_api'),

    # CRUD FRIENDSHIP
    path('api/friend-request/send/', views.SendFriendRequest_api.as_view(), name='send-friend-request'),
    path('api/friend-request/accept/<int:pk>/', views.FriendRequestAccept_api.as_view(), name='friend-request-accept'),
    path('api/friend-request/reject/<int:pk>/', views.FriendRequestReject_api.as_view(), name='friend-request-reject'),
    path('api/friend-request/cancel/<int:pk>/', views.FriendRequestCancel_api.as_view(), name='cancel-friend-request'),
    path('api/friend/remove/<int:id>/', views.FriendRemove_api.as_view(), name='remove-friend'),
    path('api/friend/list/', views.FriendshipList_api.as_view(), name='friendship-list'),

    # CRUD BLOCK
    path('api/block/add', views.BlockPlayer_api.as_view(), name='block-player'),
    path('api/block/list/', views.BlockListView.as_view(), name='block-list'),
    path('api/block/remove/<int:pk>/', views.UnblockPlayerView.as_view(), name='unblock-player'),

    # JWT Token Endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
