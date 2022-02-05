from django.db.models import Q
from django_filters import rest_framework as filters
from ..models import MarketList

class MarketListFilter(filters.FilterSet):
    
    first_name  = filters.CharFilter(field_name='player__first_name', lookup_expr='startswith')
    last_name   = filters.CharFilter(field_name='player__last_name', lookup_expr='startswith')
    name        = filters.CharFilter(method='name_filter')
    country     = filters.CharFilter(field_name='player__country')
    team_name   = filters.CharFilter(field_name='player__team__name', lookup_expr='startswith')
    min_value   = filters.NumberFilter(field_name="player__market_value", lookup_expr='gte')
    max_value   = filters.NumberFilter(field_name="player__market_value", lookup_expr='lte')

    class Meta:
        model = MarketList
        fields = [
            'first_name',
            'last_name',
            'country',
            'team_name',
            'min_value',
            'max_value',
        ]

    def name_filter(self, queyset, name, value):
        q = MarketList.objects.all()
        for term in value.split():
            q = q.filter(
                Q(player__first_name__startswith=term) | 
                Q(player__last_name__startswith=term)
                )
        
        return q

