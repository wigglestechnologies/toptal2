import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse as api_reverse
from rest_framework.test import APITestCase

from .models import create_team, Team, Player, MarketList
from accounts.models import Account

User = get_user_model()

class PlayerTestAPI(APITestCase):

    def setUp(self):

        self.admin_user         = User.objects.create_superuser('John', 'Admin', 'admin@soccer.com', 'abc1234')
        self.user               = User.objects.create_user('John', 'Verified', 'user@soccer.com', 'abc1234')
        self.user.is_verified = True
        self.user.save()

        self._LoginUser(self.admin_user.email, 'abc1234')
        self._LoginUser(self.user.email, 'abc1234')

    def _LoginUser(self, email, password):        

        data = {
            'email': email,
            'password': password
        }
        
        url = api_reverse('accounts-api:login')
        response = self.client.post(url, data=data)        

        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_player_create(self):

        team = Team.objects.get(owner = self.admin_user)
        data = {
            'first_name': 'Neymar',
            'last_name': 'Junior', 
            'country': 'BR',
            'team': team.id,
            'age': 28,
            'position': 'ATTACKER'
            }        
        
        # create player by admin
        response = self.client.post(
            api_reverse('soccer-manager:player-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],
            data=data
        )        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  

    def test_player_create_bad_data(self):

        team = Team.objects.get(owner = self.admin_user)
        data = {
            'first_name': 'Neymar',
            'last_name': 'Junior', 
            'country': 'Z',
            'team': team.id,
            'age': 28,
            'position': 'ATTACKER'
            }        
        
        # create player by admin
        response = self.client.post(
            api_reverse('soccer-manager:player-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],
            data=data
        )        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)  

    def test_player_create_regular_user(self):

        team = Team.objects.get(owner = self.user)
        data = {
            'first_name': 'Neymar',
            'last_name': 'Junior', 
            'country': 'BR',
            'team': team.id,
            'age': 28,
            'position': 'ATTACKER'
            }        
        
        # create player by user
        response = self.client.post(
            api_reverse('soccer-manager:player-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],
            data=data
        )        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  

    def test_player_list_admin(self):
         
        response = self.client.get(
            api_reverse('soccer-manager:player-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  
        self.assertEqual(response.data['count'], 40)  # all players

    def test_player_list_user(self):
         
        response = self.client.get(
            api_reverse('soccer-manager:player-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],        
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  
        self.assertEqual(response.data['count'], 20)  # only user players

    def test_player_retrieve_admin(self):
         
        team = Team.objects.get(owner = self.user.pk)
        players = team.player_set.all()
        response = self.client.get(
            api_reverse('soccer-manager:player-rud', kwargs={'id': str(players[0].id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)       

    def test_player_retrieve_user_player(self):
         
        team = Team.objects.get(owner = self.user.pk)
        players = team.player_set.all()
        response = self.client.get(
            api_reverse('soccer-manager:player-rud', kwargs={'id': str(players[0].id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)      

    def test_player_retrieve_other_user_player(self):
         
        team = Team.objects.get(owner = self.admin_user.pk)
        players = team.player_set.all()
        response = self.client.get(
            api_reverse('soccer-manager:player-rud', kwargs={'id': str(players[0].id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)      

    def test_player_update_admin(self):
         
        team = Team.objects.get(owner = self.user.pk)
        players = team.player_set.all()

        new_last_name = 'Muller'
        data = {
            'last_name': new_last_name
        }

        response = self.client.patch(
            api_reverse('soccer-manager:player-rud', kwargs={'id': str(players[0].id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],           
            data=data 
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)       
        self.assertEqual(response.data['last_name'], new_last_name)

    def test_player_update_user_player_allowed_field(self):
         
        team = Team.objects.get(owner = self.user.pk)
        players = team.player_set.all()

        new_last_name = 'Muller'
        data = {
            'last_name': new_last_name
        }

        response = self.client.patch(
            api_reverse('soccer-manager:player-rud', kwargs={'id': str(players[0].id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
            data=data,
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK) 
        self.assertEqual(response.data['last_name'], new_last_name)     

    def test_player_update_user_player_unallowed_field(self):
         
        team = Team.objects.get(owner = self.user.pk)
        players = team.player_set.all()

        old_age = players[0].age
        data = {
            'age': old_age+10
        }

        response = self.client.patch(
            api_reverse('soccer-manager:player-rud', kwargs={'id': str(players[0].id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
            data=data,
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['age'], old_age)


    def test_player_update_other_user_player(self):
         
        team = Team.objects.get(owner = self.admin_user.pk)
        players = team.player_set.all()

        data = {
            'last_name': 'Muller'
        }

        response = self.client.patch(
            api_reverse('soccer-manager:player-rud', kwargs={'id': str(players[0].id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
            data=data,
        )        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)      


    def test_player_delete_admin(self):
         
        team = Team.objects.get(owner = self.user.pk)
        players = team.player_set.all()
        response = self.client.delete(
            api_reverse('soccer-manager:player-rud', kwargs={'id': str(players[0].id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)       
    
    def test_player_delete_user(self):
         
        team = Team.objects.get(owner = self.user.pk)
        players = team.player_set.all()
        response = self.client.delete(
            api_reverse('soccer-manager:player-rud', kwargs={'id': str(players[0].id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class TeamTestAPI(APITestCase):

    def setUp(self):

        self.admin_user         = User.objects.create_superuser('John', 'Admin', 'admin@soccer.com', 'abc1234')
        self.user               = User.objects.create_user('John', 'Verified', 'user@soccer.com', 'abc1234')
        self.user.is_verified = True
        self.user.save()

        self.user2               = User.objects.create_user('John', 'Verified2', 'user2@soccer.com', 'abc1234')
        self.user2.is_verified = True
        self.user2.save()

        self._LoginUser(self.admin_user.email, 'abc1234')
        self._LoginUser(self.user.email, 'abc1234')

    def _LoginUser(self, email, password):        

        data = {
            'email': email,
            'password': password
        }
        
        url = api_reverse('accounts-api:login')
        response = self.client.post(url, data=data)        

        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_team_create_admin(self):

        user = Account.objects.get(email='user2@soccer.com')

        data = {
            'name': 'Test Team',
            'country': 'BR',             
            'owner': user.id,
            'value': 0,
            'budget': 0
            }        
                
        response = self.client.post(
            api_reverse('soccer-manager:team-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],
            data=data
        )        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  

    def test_team_create_user(self):

        user = Account.objects.get(email='user2@soccer.com')

        data = {
            'name': 'Test Team',
            'country': 'BR',             
            'owner': user.id,
            'value': 0,
            'budget': 0
            }        
               
        response = self.client.post(
            api_reverse('soccer-manager:team-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],
            data=data
        )        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  

    def test_team_list_admin(self):
                
        response = self.client.get(
            api_reverse('soccer-manager:team-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  
        self.assertEqual(response.data['count'], 2)  

    def test_team_list_user(self):
                
        response = self.client.get(
            api_reverse('soccer-manager:team-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)  
        self.assertEqual(response.data['count'], 2)  

    def test_team_retrieve_admin(self):
        
        team = Team.objects.get(owner=self.user)        
        response = self.client.get(
            api_reverse('soccer-manager:team-rud', kwargs={'id': str(team.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)       

    def test_team_retrieve_user(self):
        
        team = Team.objects.get(owner=self.user)        
        response = self.client.get(
            api_reverse('soccer-manager:team-rud', kwargs={'id': str(team.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)       

    def test_team_retrieve_other_user(self):
        
        team = Team.objects.get(owner=self.admin_user)        
        response = self.client.get(
            api_reverse('soccer-manager:team-rud', kwargs={'id': str(team.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)       

    def test_team_update_admin(self):
         
        team = Team.objects.get(owner = self.user.pk)
        new_name = 'Muller Team'
        data = {
            'name': new_name
        }

        response = self.client.patch(
            api_reverse('soccer-manager:team-rud', kwargs={'id': str(team.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],           
            data=data 
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)       
        self.assertEqual(response.data['name'], new_name)       

    def test_team_update_user_team_allowed_field(self):
         
        team = Team.objects.get(owner = self.user.pk)        

        new_name = 'Muller Team'
        data = {
            'name': new_name
        }

        response = self.client.patch(
            api_reverse('soccer-manager:team-rud', kwargs={'id': str(team.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
            data=data,
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)      
        self.assertEqual(response.data['name'], new_name)       

    def test_team_update_user_team_unallowed_field(self):
         
        team = Team.objects.get(owner = self.user.pk)        

        old_value = team.value
        data = {
            'value:': old_value+10
        }

        response = self.client.patch(
            api_reverse('soccer-manager:team-rud', kwargs={'id': str(team.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],           
            data=data,
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['value'], old_value)


    def test_team_update_other_user_team(self):
         
        team = Team.objects.get(owner = self.admin_user.pk)
        data = {
            'name:': 'Muller Team'
        }

        response = self.client.patch(
            api_reverse('soccer-manager:team-rud', kwargs={'id': str(team.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
            data=data,
        )        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)      

    def test_team_delete_admin(self):
         
        team = Team.objects.get(owner = self.user.pk) 
        response = self.client.delete(
            api_reverse('soccer-manager:team-rud', kwargs={'id': str(team.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)       
    
    def test_team_delete_user(self):
         
        team = Team.objects.get(owner = self.user.pk)
        response = self.client.delete(
            api_reverse('soccer-manager:team-rud', kwargs={'id': str(team.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MarketListTestAPI(APITestCase):

    def setUp(self):

        self.admin_user         = User.objects.create_superuser('John', 'Admin', 'admin@soccer.com', 'abc1234')
        self.user               = User.objects.create_user('John', 'Verified', 'user@soccer.com', 'abc1234')
        self.user.is_verified = True
        self.user.save()

        self.user2               = User.objects.create_user('John', 'Verified2', 'user2@soccer.com', 'abc1234')
        self.user2.is_verified = True
        self.user2.save()

        self._LoginUser(self.admin_user.email, 'abc1234')
        self._LoginUser(self.user.email, 'abc1234')
        self._LoginUser(self.user2.email, 'abc1234')

    def _LoginUser(self, email, password):        

        data = {
            'email': email,
            'password': password
        }
        
        url = api_reverse('accounts-api:login')
        response = self.client.post(url, data=data)        

        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def _PutPlayersOnMarketlist(self):
                
        self.teams_count = Team.objects.count()
        self.players_count = 0
        self.players_on_market = {}
        self.players_per_team = 3

        for team in Team.objects.all():                        
            
            players = team.player_set.all()
            self.players_on_market[team.id] = list()
        
            for j in range(self.players_per_team):

                self.players_on_market[team.id].append(players[j])

                player_id = players[j].id
                asked_price = players[j].market_value + 10000        
                data = {
                    'player_id': player_id,
                    'asked_price': asked_price,             
                    }        
                        
                response = self.client.post(
                    api_reverse('soccer-manager:marketlist-list-create'), 
                    HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],
                    data=data
                )        
                
                self.players_count += 1        

    def test_marketlist_put_player(self):

        team = Team.objects.get(owner=self.user)
        players = team.player_set.all()
        player_id = players[0].id
        asked_price = players[0].market_value + 10000
        
        data = {
            'player_id': player_id,
            'asked_price': asked_price,             
            }        
                
        response = self.client.post(
            api_reverse('soccer-manager:marketlist-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],
            data=data
        )        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['asked_price'], asked_price)
        self.assertEqual(MarketList.objects.count(), 1)

    def test_marketlist_put_player_admin(self):

        team = Team.objects.get(owner=self.user2)
        players = team.player_set.all()
        player_id = players[0].id
        asked_price = players[0].market_value + 10000
        
        data = {
            'player_id': player_id,
            'asked_price': asked_price,             
            }        
                
        response = self.client.post(
            api_reverse('soccer-manager:marketlist-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.admin_user.tokens()['access'],
            data=data
        )        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['asked_price'], asked_price)
        self.assertEqual(MarketList.objects.count(), 1)

    def test_marketlist_put_other_user_player(self):

        team = Team.objects.get(owner=self.user2)
        players = team.player_set.all()
        player_id = players[0].id
        asked_price = players[0].market_value + 10000
        
        data = {
            'player_id': player_id,
            'asked_price': asked_price,             
            }        
                
        response = self.client.post(
            api_reverse('soccer-manager:marketlist-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],
            data=data
        )        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_marketlist_list_players(self):
        
        self._PutPlayersOnMarketlist()
        
        response = self.client.get(
            api_reverse('soccer-manager:marketlist-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
        )        
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], self.players_count)

        response = self.client.get(
            api_reverse('soccer-manager:marketlist-list-create'), 
            HTTP_AUTHORIZATION='Bearer ' + self.user2.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], self.players_count)

    def test_marketlist_retrieve_player_user(self):

        self._PutPlayersOnMarketlist()        

        team = Team.objects.get(owner = self.user)
        player_id = self.players_on_market[team.id][0].id
        
        response = self.client.get(
            api_reverse('soccer-manager:marketlist-ru', kwargs={'id': str(player_id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],            
        )        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def buy_player(self, buyer_user):
        self._PutPlayersOnMarketlist()                

        team        = Team.objects.get(owner=self.user)
        new_team    = Team.objects.get(owner=self.user2)

        player      = self.players_on_market[team.id][0]
        
        data = {
            'team': new_team.id,
        }

        asked_price             = player.asked_price
        seller_team_old_budget  = team.budget
        buyer_team_old_budget   = new_team.budget                
        
        response = self.client.put(
            api_reverse('soccer-manager:marketlist-ru', kwargs={'id': str(player.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + buyer_user.tokens()['access'],    
            data=data,        
        )                                
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(team.budget, seller_team_old_budget+asked_price)
        self.assertEqual(new_team.budget, buyer_team_old_budget-asked_price)
        self.assertGreater(Player.objects.get(id=player.id).market_value, asked_price)

    def test_marketlist_buy_player(self):        
        self.buy_player(self.user2)

    def test_marketlist_buy_admin(self):        
        self.buy_player(self.admin_user)

    def test_marketlist_buy_own_player(self):
        
        self._PutPlayersOnMarketlist()                

        team        = Team.objects.get(owner=self.user)
        new_team    = Team.objects.get(owner=self.user)

        player      = self.players_on_market[team.id][0]
        
        data = {
            'team': new_team.id,
        }

        asked_price             = player.asked_price
        seller_team_old_budget  = team.budget
        buyer_team_old_budget   = new_team.budget        
        
        response = self.client.put(
            api_reverse('soccer-manager:marketlist-ru', kwargs={'id': str(player.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],    
            data=data,        
        )                                
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_marketlist_buy_player_to_other_team(self):
        
        self._PutPlayersOnMarketlist()                

        team        = Team.objects.get(owner=self.user)
        new_team    = Team.objects.get(owner=self.user2)

        player      = self.players_on_market[team.id][0]
        
        data = {
            'team': new_team.id,
        }

        asked_price             = player.asked_price
        seller_team_old_budget  = team.budget
        buyer_team_old_budget   = new_team.budget        
        
        response = self.client.put(
            api_reverse('soccer-manager:marketlist-ru', kwargs={'id': str(player.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user.tokens()['access'],    
            data=data,        
        )                                
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_marketlist_delete_player(self):
        
        self._PutPlayersOnMarketlist()                
        team        = Team.objects.get(owner=self.user)     
        player      = self.players_on_market[team.id][0]
        
        response = self.client.delete(
            api_reverse('soccer-manager:marketlist-ru', kwargs={'id': str(player.id)}), 
            HTTP_AUTHORIZATION='Bearer ' + self.user2.tokens()['access'],                       
        )                        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        