# Import custom classes
from data_retrieval.abstract_scraper import AbstractScraper
from data_retrieval.pfr_scraper import PFRScraper
from bs4 import BeautifulSoup
import re

class FFTodayScraper(AbstractScraper):

    def __init__(self, reqDelay, format='halfppr'):
        # Initialize the superclass
        self.format = format

        self.pfr_scraper = PFRScraper(reqDelay)
        AbstractScraper.__init__(self, reqDelay)

    def ScrapeTop25RBFromYears(self, start_year, end_year):
        out = {}
        for year in range(start_year, end_year+1):
            out[str(year)] = self.ScrapeTom25RBFromYear(year)
        return out

    def ScrapeTom25RBFromYear(self, year):
        if self.format == "ppr":
            id = 107644
        elif self.format == "halfppr":
            id = 193033
        elif self.format == "standard":
            id = 1
        
        # URL to send the request to the get the player data
        url = "https://www.fftoday.com/stats/playerstats.php?Season={0}&GameWeek=&PosID=20&LeagueID={1}".format(year, id)
        resp = self.m_ssn.get(url, verify = True)

        # Parse and find the data we need for the year
        soup = BeautifulSoup(resp.content, "lxml")
        player_table = soup.find('table', attrs={"cellpadding":"2", "cellspacing":"1"}).findAll('tr')
        players = [re.findall(r'[A-Z]\S+', row.find('td').text) for row in player_table][2:27]

        # Scrape each RB
        for player in players:
            self.pfr_scraper.ScrapePlayer(player[0], player[1], "RB", year)

        return self.pfr_scraper.GetAndClearRBCache()


# Main script for testing functionality/sandboxing
if __name__ == '__main__':
    # See if the inheiritance/init is working
    scraper = FFTodayScraper(0.5)

    # Test the scrape player function
    data = scraper.ScrapeTop25RBFromYears(2005, 2008)