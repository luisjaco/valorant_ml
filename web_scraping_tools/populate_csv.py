import bs4
import requests
import csv
import time
# TODO KEEP TRACK OF URLS TO AVOID DUPLICATE PLAYERS!
class LeaderboardPage:
    '''Used to fill a csv with rows of players from a set range of leaderboard pages.'''
    def __init__(self, path: str, delay: int=2.5, auto: bool=False):
        '''Constructor.
        
        path: csv file path.
        delay: delay between page requests. Default = 2.5.
        auto: whether or not the program will automatically retry requests. Default = False.
        '''
        self.path = path
        self.delay = delay
        self.auto = auto
        print("There are a total of 55 pages in the leaderboards of Tracker Networks Valorant stats leaderboard. [1-55]\nThere are about 100 players per page.")

    def start(self) -> None:
        '''Populates a csv file with player data for a set amount of leaderboard pages.'''
        page_start = -1
        page_end = -1
        while page_start < 1 or page_start > 55:
            print("Enter the starting page number: [1-55]")
            page_start = int(input())
        while page_end < page_start or page_end > 55:
            print(f"Enter the ending page number: [{page_start}-55]")
            page_end = int(input())

        player_list = []
        print(f"Starting search with range [{page_start}-{page_end}], auto={self.auto}, and delay={self.delay}s\n~If you would like to stop execution, [ctrl+c] will safely end execution!~")
        self._request_loop(page_start, page_end, player_list)
        
        print("Dictionaries created. Printing first and last player dictionaries:")
        print("~~~~~~~~~~~~~~~~~~~~~")
        for player_dict in [player_list[0], player_list[-1]]:
            for key, value in player_dict.items():
                print(f"{key}: {value}")
            print("~~~~~~~~~~~~~~~~~~~~~")

        self.end(player_list)

    def _request_loop(self, page_start: int, page_end: int, player_list: list) -> None:
        '''Loop of requesting for pages. Handles when page request is blocked.'''
        page_index = page_start
        while page_index <= page_end:
            path = "https://tracker.gg/valorant/leaderboards/ranked/all/default?region=na&page=" + str(page_index) + "&act=ec876e6c-43e8-fa63-ffc1-2e8d4db25525"
            try:
                player_list += self._get_leaderboard_data(path)
                print(f"Page {page_index} read.")
                page_index += 1
                time.sleep(self.delay)
            
            # When the page request is blocked.
            except AttributeError:
                if self.auto:
                    print(f"Attempt for page {page_index} blocked. Sleeping for 30 seconds, then trying again...")
                    time.sleep(30)
                else:
                    print(f"Attempt for page {page_index} blocked. Try again?\n[1] yes\n[0] no")
                    response = input()
                    if response == "1":
                        print("Sleeping for 30 seconds, then trying again.")
                        time.sleep(30)
                    else:
                        print("Ending execution.")
                        break
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt caught. Ending execution")
                break
    
    def _get_leaderboard_data(self, path: str) -> list:
        '''Creates a list of dictionaries including player data based on a single page of leaderboard data.'''
        page = requests.get(path)
        soup = bs4.BeautifulSoup(page.text, 'html.parser')

        # Getting all the rows inside of the leaderboard:
        tbody = soup.find('tbody')
        player_rows = tbody.find_all('tr')

        # Gathering leaderboard data:
        page_players = []
        for player_row in player_rows:
            player_dict = self._get_player_stats(player_row)
            page_players.append(player_dict)

        return page_players

    def _get_player_stats(self, player_row: bs4.element.Tag) -> dict:
        '''Creates a dictionary including all stats available from a single players leaderboard row.'''
        # Many of the following variables must be reformatted.
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

    def end(self, player_list: list) -> None:
        '''Ending sequence. Writes data to a csv. Adds extra columns for full data completion.'''
        print('Add to csv?\n[1] yes\n[0] no')
        add_to_csv = input()
        if add_to_csv == '1':
            with open(self.path, 'w') as csvfile:
                # Filling header with all columns, includes those which will be found using 'complete_csv.py'
                fieldnames = ['id','name','tag','url','rank','tier','ranked_rating', 
                            'damage_per_round', 'kd_ratio', 'headshot_percent', 
                            'win_percent', 'wins', 'kast', 'dd_per_round', 'kills', 
                            'deaths', 'assists', 'acs', 'kad_ratio', 'kills_per_round',
                            'first_bloods', 'flawless_rounds', 'aces']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                id = 0
                for player_dict in player_list:
                    player_dict['id'] = id
                    writer.writerow(player_dict)
                    id += 1

            print('Added to csv!')
        else:
            print('Ending execution.')

path = "sample.csv"
lp = LeaderboardPage(path, delay=2, auto=True)
lp.start()
