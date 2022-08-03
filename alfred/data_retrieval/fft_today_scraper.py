# Third Party
from bs4 import BeautifulSoup
import re

# In House
from alfred.data_retrieval.abstract_scraper import AbstractScraper
from alfred.data_retrieval.pfr_scraper import PFRScraper

class FFTodayScraper(AbstractScraper):
    """This is a data scraper that scrapes FFToday Webpages.

    Inherits from: AbstractSCraper
    """

    def __init__(self, reqDelay, format='halfppr'):
        """Constructor for the FFTodayScraper

        Args:
            reqDelay (int): How many seconds to delay each request
            format (str, optional): Fantasy football scoring format. Defaults to 'halfppr'.
        """
        # Initialize the superclass
        self.format = format

        self.pfr_scraper = PFRScraper(reqDelay)
        AbstractScraper.__init__(self, reqDelay)

    def scrape_rb_from_years(self, start_year, end_year, top = 25):
        """Scrape the running backs (top 25) from a range of years

        Args:
            start_year (int): The start year
            end_year (int): The end year
            top (int, optional): Number of players to grab

        Returns:
            dict: The players from those years
        """
        out = {}
        for year in range(start_year, end_year+1):
            out[str(year)] = self.scrape_rb_from_year(year, top)
        return out

    def scrape_rb_from_year(self, year, top = 25):
        """Scrape the running backs (top 25) from a single year

        Args:
            year (int): The year to scrape RBs for
            top (int, optional): Number of players to grab

        Returns:
            dict: The running back
        """
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
        players = [re.findall(r'[A-Z]\S+', row.find('td').text) for row in player_table][2 : top + 2]

        # Scrape each RB
        for player in players:
            self.pfr_scraper.ScrapePlayer(player[0], player[1], "RB", year)

        return self.pfr_scraper.GetAndClearRBCache()


# Main script for testing functionality/sandboxing
if __name__ == '__main__':
    # See if the inheiritance/init is working
    scraper = FFTodayScraper(0.5)

    # Test the scrape player function
    data = scraper.scrape_rb_from_years(2005, 2008)