from .serializers import (
    PlayerAdminUserSerializer, 
    PlayerNormalUserSerializer, 
    PlayerMarketListUserSerializer,
    TeamAdminUserSerializer,
    TeamNormalUserSerializer,
    MarketListPutPlayerSerializer,
    MarketListDetailSerializer,    
)

from rest_framework.generics import (
    GenericAPIView,     
    RetrieveUpdateDestroyAPIView, 
    ListCreateAPIView,
    RetrieveUpdateAPIView
)

from soccer_manager.models import Player, Team, MarketList
from accounts.models import Account
from rest_framework.permissions import IsAuthenticated, IsAdminUser
        
from .permissions import IsPlayerOwner, IsTeamOwner
from rest_framework.exceptions import PermissionDenied
from.filters import MarketListFilter
from django_filters import rest_framework as filters

class PlayerListCreateAPIView(ListCreateAPIView):
    serializer_class = PlayerAdminUserSerializer
    queryset = Player.objects.all()
    permission_classes = [IsAuthenticated,]

    def perform_create(self, serializer):
         
        if not self.request.user.is_admin:
            raise PermissionDenied("You don't have permission to create players!")

        return serializer.save()
    
    def get_queryset(self):

        # all players
        if self.request.user.is_admin:
            return self.queryset
        # only players owned by the user
        else:    
            return self.queryset.filter(team__owner_id = self.request.user.id)

class PlayerRUDAPIView(RetrieveUpdateDestroyAPIView):    
    queryset = Player.objects.all()
    permission_classes = [IsAuthenticated, IsPlayerOwner]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        if self.request.user.is_admin:
            return PlayerAdminUserSerializer
        else:
            return PlayerNormalUserSerializer

    def perform_destroy(self, serializer):
        if not self.request.user.is_admin:
            raise PermissionDenied("You don't have permission to delete players!")
        else:
            serializer.delete()

class TeamListCreateAPIView(ListCreateAPIView):
    serializer_class = TeamAdminUserSerializer
    queryset = Team.objects.all()
    permission_classes = [IsAuthenticated,]
    
    def perform_create(self, serializer):
         
        if not self.request.user.is_admin:
            raise PermissionDenied("You don't have permission to create teams!")

        return serializer.save()

class TeamRUDAPIView(RetrieveUpdateDestroyAPIView):    
    queryset = Team.objects.all()
    permission_classes = [IsAuthenticated, IsTeamOwner]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        if self.request.user.is_admin:
            return TeamAdminUserSerializer
        else:
            return TeamNormalUserSerializer

    def perform_destroy(self, serializer):
        if not self.request.user.is_admin:
            raise PermissionDenied("You don't have permission to delete teams!")
        else:
            serializer.delete()

class MarketListListCreateAPIView(ListCreateAPIView):
    
    queryset = MarketList.objects.all()
    permission_classes = [IsAuthenticated]

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = MarketListFilter

    def perform_create(self, serializer):

        serializer.is_valid(raise_exception = True)
        
        player_id = serializer.validated_data['player_id']
        player = Player.objects.get(id = player_id)
        request_user_team = Team.objects.get(owner=self.request.user)
        
        # player not from user team and not admin
        if player.team != request_user_team and not self.request.user.is_admin:
            raise PermissionDenied("You can't put players you don't own on the marketlist!")
        
        player.asked_price = serializer.validated_data['asked_price']
        player.save()
        
        MarketList.objects.get_or_create(player=player)

    def get_serializer_class(self):

        if self.request.method == 'POST':
            return MarketListPutPlayerSerializer
        else:
            return MarketListDetailSerializer

class MarketlistRUAPIView(RetrieveUpdateAPIView):        
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'    

    def get_queryset(self):        
        
        player_id = self.kwargs['id']
        if not MarketList.objects.filter(player__id = player_id):
            raise Exception(f'Player id: {player_id} not on market list!')

        return Player.objects.all()    
    
    def get_serializer_class(self):
        return PlayerMarketListUserSerializer
        
    def perform_update(self, serializer):

        serializer.is_valid(raise_exception=True)

        # check if the request user has a team
        try:
            user_team = Team.objects.get(owner = self.request.user)
        except:
            raise Exception(f"User id {self.request.user.id} doesn't have a team.")
        
        buyer_team = serializer.validated_data['team']

        # user can't buy a player to a team he doens't own, unless he's admin
        if user_team != buyer_team and self.request.user.is_admin == False:
            raise Exception(f"You can't buy a player to a team you don't own.")

        # check if user is trying to buy his own player
        player_id = self.kwargs['id']
        player = Player.objects.get(id = player_id)
        if player.team == buyer_team:
            raise Exception(f"You can't buy your own player!")               

        buyer_team.Buy(player.team, player)

        return PlayerMarketListUserSerializer(player)