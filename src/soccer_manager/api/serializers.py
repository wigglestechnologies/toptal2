from soccer_manager.models import Player, Team, MarketList
from rest_framework import serializers

class PlayerAdminUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Player
        fields = '__all__'
        read_only_fields = ['created']

class PlayerNormalUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Player
        fields = '__all__'
        read_only_fields = [
            'age',
            'market_value',
            'asked_price',
            'position',
            'team',
            'created'
            ]

class PlayerMarketListUserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Player        
        exclude = ['market_value'] # user doesn't need to see this on market
        read_only_fields = [
            'first_name',
            'last_name',
            'country',
            'age',
            'asked_price',
            'position',            
            'created'
            ]
         

class TeamAdminUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = '__all__'
        read_only_fields = ['created']

class TeamNormalUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = '__all__'
        read_only_fields = [
            'value',
            'budget',
            'owner'
        ]


class MarketListPutPlayerSerializer(serializers.Serializer):

    player_id   = serializers.IntegerField()
    asked_price = serializers.FloatField()

    class Meta:        
        fields = [
            'player_id',
            'asked_price'
        ]    

class MarketListDetailSerializer(serializers.ModelSerializer):
    
    player = PlayerMarketListUserSerializer()
    
    class Meta:        
        model = MarketList
        fields = ['player']        
        depth = 1