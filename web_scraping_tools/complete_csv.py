from bs4 import BeautifulSoup
import requests
import pandas
import time

class UserExit(Exception):
    '''User exited request loop.'''
    pass

class PlayerPage:
    '''Used to retrieve player data.'''
    def __init__(self, path: str, delay: int=2.5, auto: bool=False):
        '''Constructor.
        
        path: csv file path.
        delay: time delay between the requests in seconds. Default = 2.5
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
        soup = BeautifulSoup(page.text, 'html.parser')

        # A lot of the following variables must be changed.
        # Stats seen in "giant stats" section:
        giant_stats = soup.find('div', attrs={'class':'giant-stats'}).find_all('span', attrs={'class':'value'})
        damage_per_round = float(giant_stats[0].text)
        kd_ratio = float(giant_stats[1].text)
        headshot_percent = float(giant_stats[2].text[:-1])/100.0
        win_percent = float(giant_stats[3].text[:-1])/100.0

        # Stats seen in "main stats" section:
        main_stats = soup.find('div', attrs={'class':'main'}).find_all('span', attrs={'class':'value'})
        wins = int(main_stats[0].text.replace(',',''))
        kast = float(main_stats[1].text[:-1])/100
        dd_per_round = float(main_stats[2].text)
        kills = int(main_stats[3].text.replace(',',''))
        deaths = int(main_stats[4].text.replace(',',''))
        assists = int(main_stats[5].text.replace(',',''))
        acs = float(main_stats[6].text)
        kad_ratio = float(main_stats[7].text)
        kills_per_round = float(main_stats[8].text)
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

path = 'sample.csv'
pp = PlayerPage(path, delay=2, auto=True)
pp.start(player_limit=10000)
