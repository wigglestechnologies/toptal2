from django.db import models
from django_countries.fields import CountryField
from accounts.models import Account

from django.dispatch import receiver
from accounts.signals import user_logged_in

import names
import random

from django_countries.data import COUNTRIES

from django.core.validators import MinValueValidator

class Team(models.Model):
    
    class Meta:
        ordering = ['id']

    name        = models.CharField(max_length=100, default="Unnamed")
    country     = CountryField(blank_label = '(select country)')
    value       = models.FloatField(default=0, validators=[MinValueValidator(0)])
    budget      = models.FloatField(default=5000000.0, validators=[MinValueValidator(0)])    
    owner       = models.OneToOneField(Account, on_delete=models.CASCADE)        
    created     = models.DateTimeField(auto_now_add=True)

    def Buy(self, owner_team, player):

        if player.asked_price > self.budget:
            raise Exception(f"Team doesn't have budget to buy player id {player.id}!")

        random.seed()
        
        # remove player from market list        
        market_list_entry = MarketList.objects.get(player = player)        
        market_list_entry.delete()        

        # transfer money
        owner_team.budget     += player.asked_price
        self.budget           -= player.asked_price        
        
        # update player value and reset asked price on market
        player.market_value   = player.asked_price * (1 + (random.randrange(10, 100) / 100))
        player.asked_price    = 0
        
        # update team
        player.team           = self
        
        # update database
        player.save()
        owner_team.save()
        self.save()                
        self.UpdateTeamValue()
        owner_team.UpdateTeamValue()

    def UpdateTeamValue(self):

        self.value = 0        
        for player in Team.objects.get(id = self.id).player_set.all():
            self.value += player.market_value
        
        self.save()

        
GOALKEEPER   = "GOALKEEPER"
DEFENDER     = "DEFENDER"
MIDFIELDER   = "MIDFIELDER"
ATTACKER     = "ATTACKER"

TEAM_COMPOSITION = {
    GOALKEEPER: 3,
    DEFENDER: 6,
    MIDFIELDER: 6,
    ATTACKER: 5
}

class Player(models.Model):

    class Meta:
        ordering = ['id']

    PLAYER_POSITION = [(GOALKEEPER, GOALKEEPER), (DEFENDER, DEFENDER), (MIDFIELDER, MIDFIELDER), (ATTACKER, ATTACKER)]
    
    first_name      = models.CharField(max_length=100, default="")
    last_name       = models.CharField(max_length=100, default="")
    country         = CountryField(blank_label = '(select country)')
    age             = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    market_value    = models.FloatField(default=1000000.0, validators=[MinValueValidator(0)])
    asked_price     = models.FloatField(default=0, validators=[MinValueValidator(0)])
    position        = models.CharField(max_length=16, choices=PLAYER_POSITION)
    team            = models.ForeignKey(Team, on_delete=models.CASCADE)
    created         = models.DateTimeField(auto_now_add=True)

    @property
    def fullname(self):
        return f'{self.first_name} {self.last_name}'   
        

class MarketList(models.Model):

    player = models.ForeignKey(Player, on_delete=models.CASCADE)

    class Meta:
        ordering = ['id']


@receiver(user_logged_in)
def create_team(sender, user_id, **kwargs):
    
    team = Team.objects.filter(owner__id = user_id)
    if not team:

        random.seed()

        country_list = list(COUNTRIES)
        country_list_size = len(country_list)

        user = Account.objects.get(pk=user_id)    

        # create team
        team = Team(
            name = f"{user.first_name}'s Team",
            country = country_list[random.randrange(0, country_list_size)],
            owner = user
            )
        team.save()

        # create players
        for player_position, num_players in TEAM_COMPOSITION.items():            
            for i in range(num_players):

                player = Player(
                    first_name=names.get_first_name(gender='male'),
                    last_name=names.get_last_name(),
                    age=random.randint(18, 40),
                    country=country_list[random.randrange(0, country_list_size)],
                    position=player_position,
                    team=team
                    )
                player.save()
                #print(player_position + str(i))        
        
        team.UpdateTeamValue()

    #print("user logged in " + str(user_id))