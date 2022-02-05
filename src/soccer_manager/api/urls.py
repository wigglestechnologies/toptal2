from django.urls import path
from . import views

app_name = 'soccer-manager'

urlpatterns = [
    
    # players
    path('players/', views.PlayerListCreateAPIView.as_view(), name='player-list-create'),
    path('players/<int:id>/', views.PlayerRUDAPIView.as_view(), name='player-rud'),

    # teams
    path('teams/', views.TeamListCreateAPIView.as_view(), name='team-list-create'),
    path('teams/<int:id>/', views.TeamRUDAPIView.as_view(), name='team-rud'),

    # market list
    path('marketlist/', views.MarketListListCreateAPIView.as_view(), name='marketlist-list-create'),
    path('marketlist/<int:id>/', views.MarketlistRUAPIView.as_view(), name='marketlist-ru'),
]