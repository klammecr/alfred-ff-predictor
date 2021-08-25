# Import 3rd party
from bs4 import BeautifulSoup
import re
import numpy as np
import json
import logging
import sys
import os

sys.path.append(os.path.dirname(sys.path[0]))

# Import custom classes
from DataRetrieval.AbstractScraper import AbstractScraper
from Data.PlayerDatabase import PlayerDatabase


class PFRScraper(AbstractScraper):

    def __init__(self, reqDelay):
        # Threshold to give up when looking for a player
        self.thresh = 5

        # What columns do we care about?
        self.rb_filter = ["Year", "Tm", "Rush", "Yds", "TD", "Tgt", "Rec", "AV", "A/G"]

        # RB cache
        self.player_dict_rb = {}
        
        # Initialize the superclass
        AbstractScraper.__init__(self, reqDelay)

    # This could all use a little bit of cleanup bit it's digestible for now
    def ScrapePlayer(self, player_first, player_last, position):
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
        while correct_player is False:
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
                if self.DoesPlayerMatch(player_first, player_last, resp.content):
                    # We got our guy
                    correct_player = True

                    # Scrape differently depending on position
                    if position == "QB":
                        data = self.ScrapeQB(player_first, player_last, resp.content)
                    if position == "RB":
                        data = self.ScrapeRB(player_first, player_last, resp.content)
                        # Put the player in the dictionary
                        self.player_dict_rb[player_first + " " + player_last] = data
                    if position == "WR":
                        data = self.ScrapeWR(player_first, player_last, resp.content)
                    if position == "TE":
                        data = self.ScrapeTE(player_first, player_last, resp.content)

            else:
                # Something went wrong with the request
                logging.warning('{0} returned: {1} {2}'.format(url, resp.status_code, resp.reason))

            # Increment the count
            counter += 1

    def DoesPlayerMatch(self, player_first, player_last, content):
        # Return boolean to see if there is a player match
        player_match = False

        # Parse my response text with beautiful soup
        soup = BeautifulSoup(content, "lxml")
        name = soup.find("h1",attrs={"itemprop":"name"}).text
        name = name[1:-1]
        separatedName = name.split(" ")
        if separatedName[0] == player_first and separatedName[1] == player_last:
            player_match = True

        return player_match


    def ScrapeQB(self, player_first, player_last, content):
        pass

    def ScrapeRB(self, player_first, player_last, content):
        soup = BeautifulSoup(content, "lxml")

        # Get the header to get the categories of stats
        stats_header = soup.findAll('table')[0].findAll('th', attrs={"scope":"col"})
        headers = [i.text for i in stats_header if i.text != "Year"]

        # Get the table of past years
        stats_table = soup.findAll('table')[0].findAll('tr', attrs={"class":"full_table"})

        # Data for each year
        stat_data = {}
        
        # Store the data in a table
        for row in stats_table:
            # Start year at as default, if it doesn't change, this is an error
            year = row.find("th").text
            year = re.sub("[^0-9]", "", year)

            # Empty dictionary for the stats from that year for now
            stat_data[year] = {}

            # Get all the data columns
            cols = row.find_all("td")

            # Iterate through each column and store the information
            for idx, col in enumerate(cols):
                # What stat are we getting
                stat_label = headers[idx]

                # Do we care about the stat?
                if stat_label in self.rb_filter:
                    if year == 0:
                        logging.error("Year Cannot be 0")
                    # Get the content and put it in the json
                    if stat_label == "Yds" and not "rush_yds" in stat_data[year].keys():
                        stat_data[year]["rush_yds"] = col.text
                    elif stat_label == "Yds" and "rush_yds" in stat_data[year].keys():
                        stat_data[year]["rec_yds"] = col.text
                    elif stat_label == "TD" and not "rush_td" in stat_data[year].keys():
                        stat_data[year]["rush_td"] = col.text
                    elif stat_label == "TD" and "rush_td" in stat_data[year].keys():
                        stat_data[year]["rec_td"] = col.text
                    else:
                        stat_data[year][stat_label.lower()] = col.text
        return stat_data

    def ScrapeWR(self, player_first, player_last, content):
        pass

    def ScrapeTE(self, player_first, player_last, content):
        pass

    def GetRBCache(self):
        return self.player_dict_rb

    def ClearRBCache(self):
        self.player_dict_rb = {}

    def GetAndClearRBCache(self):
        cache = self.GetRBCache()
        self.ClearRBCache()
        return cache

# Main script for testing functionality/sandboxing
if __name__ == '__main__':
    # See if the inheiritance/init is working
    scraper = PFRScraper(0.5)

    # Test the scrape player function
    scraper.ScrapePlayer("Alvin", "Kamara", "RB")
    scraper.ScrapePlayer("Saquon", "Barkley", "RB")
    scraper.ScrapePlayer("Aaron", "Jones", "RB")
    scraper.ScrapePlayer("Tevin", "Coleman", "RB")