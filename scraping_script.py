# A script to that makes using both PlayerProfileScraper and LeaderboardScraper easy to use and simple.
from scraping_tools import PlayerProfileScraper, LeaderboardScraper

# Set path to desired csv file.
path = "example.csv"

print("Typically, you will want to first populate a csv with player data and then complete it.")

print("What would you like to do?\n[2] complete csv\n[1] populate csv\n[0] exit")
response = input()
if response == "2":
    # Initialize PlayerProfileScraper.
    pps = PlayerProfileScraper(path, delay=2, auto=False)
    pps.start()
elif response == "1":
    lp = LeaderboardScraper(path, delay=2, auto=False)
    lp.start()
else:
    print("Exiting.")
