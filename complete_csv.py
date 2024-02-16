from bs4 import BeautifulSoup
import requests
import pandas
import time

class UserExit(Exception):
    '''User exited request loop.'''
    pass

class PlayerPage:
    '''Used to retrieve player data.'''
    def __init__(self, path:str, auto:bool=False):
        '''Constructor.
        
        path: csv file path.
        auto: whether or not the program will automatically retry requests. Default=False.
        '''
        self.path = path
        self.auto = auto
        self.df = pandas.read_csv(path)
        print(f"{len(self.df)} rows loaded!")

    def start(self):
        '''Begins player retrieval process.'''
        print("How many players would you like to find the data for? [-1 for a continuous search]: ", end='')
        player_limit = int(input())
        print("Starting search, if you would like to stop execution, [ctrl+c] will safely end execution!")
        self._iterate_rows(player_limit)
        self.end()

    def _iterate_rows(self, player_limit: int):
        '''Iterates through rows of a dataframe, completes desired number of unfinished rows.'''
        players_found = 0
        for index, row in self.df.iterrows():
                if players_found >= player_limit and player_limit != -1:
                    print("Limit reached. Ending execution.")
                    break
                try:
                    # If row has missing data, we will attempt to create a request for data.
                    if pandas.isna(row['damage_per_round']):
                        self.df.loc[index] = self._request_loop(index, row)
                        players_found += 1
                except KeyboardInterrupt:
                        print('\nKeyboardInterrupt caught. Ending execution.')
                        break
                except UserExit:
                        print('Ending execution.')
                        break
    
    def _request_loop(self, index: int, row: pandas.Series):
        '''Loop which controls the process of requesting and completing a row of player data.'''
        while True:
                # If a request is blocked, we will prompt the user if they would like to try again.
                try:
                    self._complete_row(row)
                    print(f"Successfully added data for player {row['name']}{row['tag']} [index #{index}].")
                    return row
                except AttributeError:
                    if self.auto:
                        print(f"Attempt for player {row['name']}{row['tag']} [index #{index}] blocked. Sleeping for 30 seconds, then trying again...")
                        time.sleep(30)
                    else:
                        print(f"Attempt for player {row['name']}{row['tag']} [index #{index}] blocked. Try again?\n[1] yes\n[0] no:")
                        response = input()
                        if response == "1":
                            print("Sleeping for 30 seconds, then trying again.")
                            time.sleep(30)
                        else:
                            raise UserExit
    
    def _complete_row(self, row: pandas.Series) -> None:
        '''Completes a dataframe row by checking the players stat page, then appending the missing columns.'''
        page = requests.get(row['url'])
        soup = BeautifulSoup(page.text, 'html.parser')

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

    def end(self):
        '''Prompts user whether or not they would like to update data'''
        print('Add to csv?\n[1] yes\n[0] no:')
        response = input()
        if response == '1':
            self.df.to_csv(self.path, index=False)
            print('Added to csv!')
        else:
            print('Exiting.')

path = 'testing_data.csv'
pp = PlayerPage(path, auto=True)
pp.start()