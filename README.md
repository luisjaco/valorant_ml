# valorant_ml
Welcome to `valorant_ml`! `valorant_ml` is a simple project containing classes for **web scraping** Valorant player data as well as notebooks for performing **EDA** and **linear regression modeling**.

In this project, you will find two classes to be used to scrape player data from tracker.gg's Valorant ranked leaderboard. The class `LeaderboardScraper` contains methods used to populate a csv file with player data found on a set amount of pages from the Valorant leaderboards. The second module `PlayerProfileScraper` contains methods to be used to complete created rows of players with more in-depth statistics.

You will also find two notebooks along with a sample dataset `sample.csv`. In `eda.ipynb`, we perform EDA on our sample dataset to find variables which we could use as features in a linear regression model for predicting a players K/D Ratio. We prepare and test our features in different models in `modeling.ipynb`. 

> [!NOTE]  
> The sample dataset contained in `sample.csv` was created on February 20th, 2024.

### Populating a csv file
```python
from scraping_tools import LeaderboardScraper

# Set csv path.
path = "example.csv"
# Initialize LeaderboardScraper.
lp = LeaderboardScraper(path, delay=2, auto=False)
# Begin execution.
lp.start()
```
### Completing a csv file
```python
from scraping_tools import PlayerProfileScraper

# Set path from populated csv.
path = 'example.csv'
# Initialize PlayerProfileScraper.
pps = PlayerProfileScraper(path, delay=2, auto=False)
# Begin execution.
pps.start()
```

### License
[MIT](https://choosealicense.com/licenses/mit/)