# 3rd Party
from bs4 import BeautifulSoup
from bs4 import Comment
import re
import logging

# In House
from alfred.data_retrieval.abstract_scraper import AbstractScraper
from alfred.data.curation import TrimData

class PFRScraper(AbstractScraper):

    def __init__(self, req_delay):
        """Initialize the object

        Args:
            req_delay (int): Time between requests in ms
        """
        # Threshold to give up when looking for a player
        self.thresh = 10

        # What columns do we care about?
        self.rb_filter = ["Age", "Year", "Tm", "Att", "Rush", "Yds", "TD", "Tgt", "Rec", "AV", "A/G"]

        # RB cache
        self.player_dict_rb = {}

        # Variable to store the latest players college stats link, we are not cacheing a list right now, this can be added if we wanted to do something like making this multithreaded
        self.college_stats_link = None
        
        # Initialize the superclass
        AbstractScraper.__init__(self, req_delay)

    # This could all use a little bit of cleanup bit it's digestible for now
    def scrape_player(self, player_first, player_last, position, year = None, trim = True):
        """Scrape a single player from the PFR website

        Args:
            player_first (string): The first name of the player
            player_last (string): The last name of the player
            position (string): The position the player plays
            year (string, optional): The year to scrape for. Defaults to None.
            trim (bool, optional): Whether or not to trim the data to a specific year. Defaults to True.
        """
        # Get the last four letters of the last name, if its a short last name, just take the whole thing
        if len(player_last) >= 4:
            player_last_first_four = player_last[0:4]
        else:
            player_last_first_four = player_last

        # Get the first two letters of a first name
        player_first_first_two = player_first[0:2]

        # Iterate until we get the correct player name
        correct_player = False
        counter = 0
        while correct_player is False and counter < self.thresh + 1:
            if player_first == "Adrian" and player_last == "Peterson":
                counter = 1
            
            # There are overlaps with the url convention, we need to just iterate through until we get the right player
            index_str = str(counter)
            if len(index_str) == 1:
                index_str = '0' + index_str

            # URL to send the request to the get the player data
            if counter < self.thresh:
                url = "https://www.pro-football-reference.com/players/{0}/{1}{2}{3}.htm".format(player_last[0], player_last_first_four, player_first_first_two, index_str)
                resp = self.m_ssn.get(url, verify = True)
            else:
                url = "https://www.pro-football-reference.com/search/search.fcgi?hint={0}+{1}&search={0}+{1}".format(player_first, player_last)
                resp = self.m_ssn.get(url, verify = True)

            # Successful request
            if resp.ok:
                # Assume we got our guy for now
                correct_player = True
                data = {}

                # Scrape differently depending on position
                if position == "QB":
                    data = self.scrape_qb(player_first, player_last, resp.content)
                if position == "RB":
                    # Scrape the NFL data
                    data = self.scrape_rb(player_first, player_last, resp.content)

                    # Try again if we don't get any data
                    if data is None:
                        url = "https://www.pro-football-reference.com/search/search.fcgi?hint={0}+{1}&search={0}+{1}".format(player_first, player_last)
                        resp = self.m_ssn.get(url, verify = True)
                        data = self.scrape_rb(player_first, player_last, resp.content)

                    if data is not None:
                        # Scrape the college stats
                        college_data = self.scrape_college_data(position)
                        data['college_data'] = college_data

                        # Check if we want to trim the data to a specific range
                        if year is not None and trim is True:
                            data = TrimData(data, year)

                        correct_player = self.does_player_match(player_first, player_last, position, year, resp.content, data)
                        if correct_player:
                            # Put the player in the dictionary
                            self.player_dict_rb[player_first + " " + player_last] = data

                    if position == "WR":
                        data = self.scrape_wr(player_first, player_last, resp.content)
                    if position == "TE":
                        data = self.scrape_te(player_first, player_last, resp.content)

            else:
                # Something went wrong with the request
                logging.warning('{0} returned: {1} {2}'.format(url, resp.status_code, resp.reason))

            # Increment the count
            counter += 1

    def does_player_match(self, player_first, player_last, position, year, content, data):
        """Check if a player matches the time period and the full name

        Args:
            player_first (string): Player first name
            player_last (string): Player last name
            position (string): Player's position
            year (int): The year that the player has played
            content (?): The content of the webpage
            data (dict): The player data from the webpage

        Returns:
            boolean: If the player matches or not
        """
        # Return boolean to see if there is a player match
        player_match = False

        # Parse my response text with beautiful soup
        soup = BeautifulSoup(content, "lxml")

        # Find their name
        name = soup.find("strong").text
        separatedName = name.split(" ")

        # Find their position
        p_content = soup.find_all("p")
        scraped_position = None
        for i in range(0, len(p_content)):
            p = p_content[i]
            if "Position" in p.text:
                colon_idx = p.text.index(":")
                scraped_position = p.text[colon_idx+2:colon_idx+4]
                break

        # See if the player matches
        if separatedName[0] == player_first and separatedName[1] == player_last and scraped_position == position:
            player_match = True

        # See if the years match up and this isn't some bozo from another time period (Adrian Peterson I'm looking at you bro)
        year_keys = [key for key in data.keys() if key.isnumeric()]
        if len(year_keys) == 0 or str(year) not in year_keys:
            player_match = False

        return player_match


    def scrape_qb(self, player_first, player_last, content):
        """Scrape the quarterbacks from the site

        Args:
            player_first (string): First name
            player_last (string): Last name
            content (string): Web page content
        """
        pass

    def scrape_rb(self, player_first, player_last, content):
        """Scrape the running backs

        Args:
            player_first (string): First name
            player_last (string): Last name
            content (string): Web page content
        """
        soup = BeautifulSoup(content, "lxml")

        # Find the link to the college stats and cache it if it exists
        self.college_stats_link = soup.find("a", href=re.compile("https://www.sports-reference.com/cfb/players"))
        if self.college_stats_link is not None:
            self.college_stats_link = self.college_stats_link['href']

        # Get the header to get the categories of stats
        try:
            stats_header = soup.findAll('table')[0].findAll('th', attrs={"scope":"col"})
        except:
            # Couldn't find any tables, likely a faulty page
            return None

        # Get all the table headers that aren't year
        headers = [i.text for i in stats_header if i.text != "Year"]

        # Get the table of past years
        stats_table = soup.findAll('table')[0].findAll('tr', attrs={"class":"full_table"})

        # Parse the table
        stat_data = self.parse_pfr_table(stats_table, headers)

        # Add draft position
        stat_data['draft_position'] = self.get_draft_position(soup)
        
        return stat_data

    def parse_pfr_table(self, stats_table, headers):
        """Parse the PFR table for all the stats

        Args:
            stats_table (list): The web content string for the table
            headers (list): The headers for each table column

        Returns:
            _dict: The statistics for all the rows and columns in the table
        """
        # Data for each year
        stat_data = {}

        # Store the data in a table
        for row in stats_table:
            # Start year at as default, if it doesn't change, this is an error
            year = row.find("th").text
            year = re.sub("[^0-9]", "", year)

            # Store the data for a given year
            stat_data[str(year)] = self.parse_table_row(row, headers)

        return stat_data

    def parse_table_row(self, row, headers):
        # Get all the data columns
        cols = row.find_all("td")

        # Iterate through each column and store the information
        out = {}
        for idx, col in enumerate(cols):
            # What stat are we getting
            stat_label = headers[idx]

            # Do we care about the stat?
            if stat_label in self.rb_filter:

                # Get the content and put it in the json
                if stat_label == "Yds" and not "rush_yds" in out.keys():
                    out["rush_yds"] = col.text
                elif stat_label == "Yds" and "rec_yds" not in out.keys() and "rush_yds" in out.keys():
                    out["rec_yds"] = col.text
                elif stat_label == "Yds" and "rec_yds" in out.keys():
                    out["scrim_yds"] = col.text
                elif stat_label == "TD" and not "rush_td" in out.keys():
                    out["rush_td"] = col.text
                elif stat_label == "TD" and "rec_td" not in out.keys() and "rush_td" in out.keys():
                    out["rec_td"] = col.text
                elif stat_label == "TD" and "rec_td" in out.keys():
                    out["scrim_td"] = col.text
                else:
                    out[stat_label.lower()] = col.text
        return out

    def scrape_college_data(self, position):
        if self.college_stats_link is not None:
            # Create the soup and access the college stats link
            resp = self.m_ssn.get(self.college_stats_link, verify = True)
            soup = BeautifulSoup(resp.content, "lxml")

            # Get last season stats, that's all we really care about for now, [-1] is the career stats
            try:
                last_season = soup.find('table', attrs={"id":"rushing"}).find_all('tr')[-2]
            except:
                try:
                    soup = BeautifulSoup(soup.find(string=lambda text: isinstance(text, Comment) and 'Rushing &amp; Receiving' in text), "lxml")
                    last_season = soup.find('table', attrs={"id":"rushing"}).find_all('tr')[-2]
                except:
                    return None

            # Get the header to get the categories of stats
            try:
                stats_header = soup.findAll('table')[0].findAll('th', attrs={"scope":"col"})
            except:
                # Couldn't find any tables, likely a faulty page
                return None

            # Get all the table headers that aren't year
            headers = [i.text for i in stats_header if i.text != "Year"]

            # Parse the row and get the stats from the last college season
            data = self.parse_table_row(last_season, headers)

            return data
        else:
            return None

    def get_draft_position(self, soup):
        # Get draft position
        draft_position = re.findall("[(][0-9]*.+ overall[)]", soup.find('div', attrs={"id":"info"}).text)
        if len(draft_position) > 0:
            draft_position = re.sub("[^0-9]", "", draft_position[0])
        else:
            draft_position = 'Undrafted'

        return draft_position

    def scrape_wr(self, player_first, player_last, content):
        """Scrape wide receivers from the site

        Args:
            player_first (string): First name
            player_last (string): Last name
            content (string): Web page content
        """
        pass

    def scrape_te(self, player_first, player_last, content):
        """Scrape tight ends from the site

        Args:
            player_first (string): First name
            player_last (string): Last name
            content (string): Web page content
        """
        pass

    def get_rbs(self):
        """Get the running backs

        Returns:
            _type_: _description_
        """
        return self.player_dict_rb

    def clear_rbs(self):
        """
        Clear the running back cache to empty
        """
        self.player_dict_rb = {}

    def get_and_clear_rbs(self):
        """Grab the RB cache and clear it afterwards

        Returns:
            dict: The running backs
        """
        cache = self.get_rb_cache()
        self.clear_rb_cache()
        return cache

# Main script for testing functionality/sandboxing
if __name__ == '__main__':
    # See if the inheiritance/init is working
    scraper = PFRScraper(0.5)

    # Test the scrape player function
    scraper.scrape_player("Alvin", "Kamara", "RB")
    scraper.scrape_player("Saquon", "Barkley", "RB")
    scraper.scrape_player("Aaron", "Jones", "RB")
    scraper.scrape_player("Tevin", "Coleman", "RB")