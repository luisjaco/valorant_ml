from bs4 import BeautifulSoup
import requests
import csv
import time

# For reference: there are a total of 55 pages in the leaderboards.

def find_leaderboard_data(path):
    '''Creates a list of dictionaries including player data which can be found on the Valorant leaderboards.'''
    page = requests.get(path)
    soup = BeautifulSoup(page.text, 'html.parser')

    # Getting all the rows inside of the leaderboard:
    tbody = soup.find('tbody')
    player_rows = tbody.find_all('tr')

    # Gathering leaderboard data:
    players = []
    for player_row in player_rows:
        player_dict = player_leaderboard_stats(player_row)
        players.append(player_dict)

    return players

def player_leaderboard_stats(player_row):
    '''Creates a dictionary including all stats available from a players data row, found on the Valorant leaderboard.'''
    # Many of the following variables must be reformatted, therefore we perform many functions to make them align.
    name = player_row.find('span', attrs={'class':'trn-ign__username'}).text
    tag = player_row.find('span', attrs={'class':'trn-ign__discriminator'}).text[1:]
    url = "https://tracker.gg" + player_row.find('a')['href'] + "/overview"
    rank = int(player_row.find('td', attrs={'class':'rank'}).text)
    tier = player_row.find('td', attrs={'class':'stat collapse'}).text
    ranked_rating = int(player_row.find('div', attrs={'class':'flex justify-end'}).text[1:].replace(',',''))

    player_dict = {
        'name' : name,
        'tag' : tag,
        'url' : url,
        'rank' : rank,
        'tier' : tier,
        'ranked_rating' : ranked_rating
    }

    return player_dict

def populate_csv_file(auto=False):
    '''Populates \"valorant_data.csv\" with player data for a set amount of leaderboard pages.'''
    page_index = 1

    print("How many pages of leaderboards would you like to find [about 100 players per page]?: ", end='')
    page_max = int(input())
    
    players = []
    while page_index <= page_max:
        path = "https://tracker.gg/valorant/leaderboards/ranked/all/default?region=na&page=" + str(page_index) + "&act=ec876e6c-43e8-fa63-ffc1-2e8d4db25525"
        try:
            players += find_leaderboard_data(path)
            print(f"Page {page_index} read.")
            page_index += 1
        except AttributeError:
            if auto:
                print(f"Attempt for page {page_index} blocked. Sleeping for 30 seconds, then trying again...")
                time.sleep(30)
            else:
                print(f"Attempt for page {page_index} blocked. Try again? [1] yes [0] no: ", end='')
                try_again = input()
                if try_again == "1":
                    print("Sleeping for 30 seconds, then trying again.")
                    time.sleep(30)
                else:
                    print("Exiting.")
                    break

    print("Dictionaries created. Printing first and last player dictionaries:")
    print("~~~~~~~~~~~~~~~~~~~~~")
    for player_dict in [players[0], players[-1]]:
        for key, value in player_dict.items():
            print(f"{key}: {value}")
        print("~~~~~~~~~~~~~~~~~~~~~")

    print('Add to csv? [1] yes [0] no: ', end='')
    add_to_csv = input()
    if add_to_csv == '1':
        with open('valorant_data.csv', 'w') as csvfile:
            fieldnames = ['name','tag','url','rank','tier','ranked_rating', 
                          'damage_per_round', 'kd_ratio', 'headshot_percent', 
                          'win_percent', 'wins', 'kast', 'dd_per_round', 'kills', 
                          'deaths', 'assists', 'acs', 'kad_ratio', 'kills_per_round',
                          'first_bloods', 'flawless_rounds', 'aces']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for player_dict in players:
                writer.writerow(player_dict)
        print('Added to csv!')
    else:
        print('Exiting.')
        exit()

populate_csv_file(auto=True)