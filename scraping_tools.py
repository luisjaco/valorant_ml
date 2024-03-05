import bs4
import csv
import requests
import pandas
import time

class UserExit(Exception):
    '''User exited request loop.'''
    pass

class LeaderboardScraper:
    '''Used to populate a csv file with rows of players from a set range of leaderboard pages.'''
    def __init__(self, path: str, delay: int=2, auto: bool=False):
        '''Constructor.
        
        path: csv file path.
        delay: delay between page requests. Default = 2.
        auto: whether or not the program will automatically retry requests. Default = False.
        '''
        self.path = path
        self.delay = delay
        self.auto = auto
        self.seen_urls = set()
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
            if player_dict is not None:
                page_players.append(player_dict)
                self.seen_urls.add(player_dict['url'])

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

        # Ensuring there are no duplicate players. Often times the leaderboards will change during execution, and players will be repeated.
        if url in self.seen_urls:
            print("Duplicate player occurance found. Skipping player " + str(name.encode())[2:-1] + ".")
            return None
        
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
        self.seen_urls.clear()

        print("Dictionaries created. Printing first and last player dictionaries:")
        print("~~~~~~~~~~~~~~~~~~~~~")
        for player_dict in [player_list[0], player_list[-1]]:
            for key, value in player_dict.items():
                print(f"{key}: {value}")
            print("~~~~~~~~~~~~~~~~~~~~~")

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

class PlayerProfileScraper:
    '''Used to retrieve player profile data.'''
    def __init__(self, path: str, delay: int=2, auto: bool=False):
        '''Constructor.
        
        path: csv file path.
        delay: time delay between the requests in seconds. Default = 2.
        auto: whether or not the program will automatically retry requests. Default = False.
        '''
        self.path = path
        self.auto = auto
        self.delay = delay
        self.df = pandas.read_csv(path)
        print(f"{len(self.df)} rows loaded!")
        self.skipped_indices = []

    def start(self, player_limit: int=-1) -> None:
        '''Begins player retrieval process.
        
        player_limit: limit of players to find data for.'''
        while player_limit < 1:
            print("How many players would you like to find the data for?: ")
            player_limit = int(input())
        
        print(f"Starting search with {self.delay}s delay and auto={self.auto}.\n~If you would like to stop execution, [ctrl+c] will safely end execution!~")
        self._iterate_data(player_limit)
        self.end()

    def _iterate_data(self, player_limit: int) -> None:
        '''Iterates through rows of a dataframe, completes desired number of unfinished rows.
        
        player_limit: limit of players to find data for.'''
        iterations = 0
        for index, row in self.df.iterrows():
                if iterations >= player_limit:
                    print("Limit reached. Ending execution.")
                    break
                try:
                    # If row has missing data, we will attempt to create a request for data.
                    if pandas.isna(row['damage_per_round']):
                        self.df.loc[index] = self._request_loop(row)
                        iterations += 1
                        time.sleep(self.delay)
                except KeyboardInterrupt:
                        print('\nKeyboardInterrupt caught. Ending execution.')
                        break
                except UserExit:
                        print('Ending execution.')
                        break
                if row['id'] == self.df.iloc[-1]['id']:
                    print("End of file. Ending Execution.")
                    break
    
    def _request_loop(self, row: pandas.Series) -> pandas.Series:
        '''Loop which controls the process of requesting and completing a row of player data.
        
        row: dataframe row of the player.'''
        encoded_name = self._encode_string(row['name'])
        encoded_tag = self._encode_string(row['tag'])
        attempts = 0
        while True:
                # If a request is blocked, we will prompt the user if they would like to try again.
                try:
                    attempts += 1
                    self._complete_row(row)
                    print(f"[+] Successfully added data for {encoded_name}{encoded_tag} [id #{row['id']}].")
                    return row
                except AttributeError:
                    if self.auto:
                        # If auto is on, a row will be skipped after 3 attempts of trying to find a player.
                        if attempts >= 3:
                            print("[x] Attempt limit [3] reached. Skipping row.")
                            self.skipped_indices.append(row['id'])
                            return row
                        else:
                            print(f"[-] Attempt for {encoded_name}{encoded_tag} [id #{row['id']}] blocked. Sleeping for 30 seconds, then trying again...")
                            time.sleep(30)
                    else:
                        print(f"[x] Attempt for {encoded_name}{encoded_tag} [id #{row['id']}] blocked.\n[2] skip row\n[1] try again\n[0] stop running")
                        response = input()
                        if response == "2":
                            print("Skipping row.")
                            self.skipped_indices.append(row['id'])
                            return row
                        elif response == "1":
                            print("Sleeping for 30 seconds, then trying again.")
                            time.sleep(30)
                        else:
                            raise UserExit
    
    def _encode_string(self, string: str) -> str:
        '''Creates a string encoded in utf-8 from a previously unicode encoded string.
        
        string: unicode string.'''
        return str(string.encode())[2:-1]
    
    def _complete_row(self, row: pandas.Series) -> None:
        '''Completes a dataframe row by checking the players stat page, then setting the missing columns to the corresponding values.
        
        row: dataframe row of player.'''
        page = requests.get(row['url'])
        soup = bs4.BeautifulSoup(page.text, 'html.parser')

        # A lot of the following variables must be changed.
        # Stats seen in "giant stats" section:
        giant_stats = soup.find('div', attrs={'class':'giant-stats'}).find_all('span', attrs={'class':'value'})
        damage_per_round = float(giant_stats[0].text.replace(',',''))
        kd_ratio = float(giant_stats[1].text)
        headshot_percent = float(giant_stats[2].text[:-1])/100.0
        win_percent = float(giant_stats[3].text[:-1])/100.0

        # Stats seen in "main stats" section:
        main_stats = soup.find('div', attrs={'class':'main'}).find_all('span', attrs={'class':'value'})
        wins = int(main_stats[0].text.replace(',',''))
        kast = float(main_stats[1].text[:-1])/100
        dd_per_round = float(main_stats[2].text.replace(',',''))
        kills = int(main_stats[3].text.replace(',',''))
        deaths = int(main_stats[4].text.replace(',',''))
        assists = int(main_stats[5].text.replace(',',''))
        acs = float(main_stats[6].text.replace(',',''))
        kad_ratio = float(main_stats[7].text.replace(',',''))
        kills_per_round = float(main_stats[8].text.replace(',',''))
        first_bloods = int(main_stats[9].text.replace(',',''))
        flawless_rounds = int(main_stats[10].text.replace(',',''))
        aces = int(main_stats[11].text.replace(',',''))

        # Adding data to row.
        row['damage_per_round'] = damage_per_round
        row['kd_ratio'] = kd_ratio
        row['headshot_percent'] = headshot_percent
        row['win_percent'] = win_percent
        row['wins'] = wins
        row['kast'] = kast
        row['dd_per_round'] = dd_per_round
        row['kills'] = kills
        row['deaths'] = deaths
        row['assists'] = assists
        row['acs'] = acs
        row['kad_ratio'] = kad_ratio
        row['kills_per_round'] = kills_per_round
        row['first_bloods'] = first_bloods
        row['flawless_rounds'] = flawless_rounds
        row['aces'] = aces

    def end(self) -> None:
        '''Ending sequence. Prompts user whether or not they would like to update data.'''
        if len(self.skipped_indices) > 0:
            print("Printing skipped row id #'s...")
            print(self.skipped_indices)
        
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        print('Add to csv?\n[1] yes\n[0] no')
        response = input()
        if response == '1':
            self.df.to_csv(self.path, index=False)
            print('Added to csv!')
        else:
            print('Exiting.')
