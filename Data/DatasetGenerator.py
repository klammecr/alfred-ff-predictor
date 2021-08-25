import sys
import os
 
sys.path.append(os.path.dirname(sys.path[0]))

# Modules
from PlayerDatabase import PlayerDatabase
from DataRetrieval.FFTodayScraper import FFTodayScraper

class DatasetGenerator:
    def __init__(self, start_year, stop_year, position_group = "RB"):
        self.start_year = start_year
        self.stop_year = stop_year
        self.position_group = position_group     
        # Database interface
        self.db = PlayerDatabase()
        # FFToday Scraper
        self.fft_scraper = FFTodayScraper(0.5)
    
    def Generate(self):
        if self.position_group == "RB":
            rb_data = self.fft_scraper.ScrapeTop25RBFromYears(self.start_year, self.stop_year)
            pass

# Main script for testing functionality/sandboxing
if __name__ == '__main__':
    # See if the inheiritance/init is working
    generator = DatasetGenerator(2005, 2009)
    generator.Generate()