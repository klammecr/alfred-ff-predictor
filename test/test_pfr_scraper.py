# Third Party
import pytest

# In House
from alfred.data_retrieval.pfr_scraper import PFRScraper

def test_scrape_player():
    scraper   = PFRScraper(0.5)
    data      = scraper.scrape_player("Alvin", "Kamara", "RB")
    year_data = data["2021"]
    assert year_data["age"]      == "26"
    assert year_data["rush"]     == "240"
    assert year_data["rush_yds"] == "898"
    assert year_data["rush_td"]  == "4"
    assert year_data["rec"]      == "47"
    assert year_data["rec_yds"]  == "439"
    assert year_data["rec_td"]   == "5"

def test_scrape_player_multiple_names():
    scraper   = PFRScraper(0.5)
    data      = scraper.scrape_player("Adrian", "Peterson", "RB", 2012)
    year_data = data["2012"]
    assert year_data["age"]      == "27"
    assert year_data["rush"]     == "348"
    assert year_data["rush_yds"] == "2097"
    assert year_data["rush_td"]  == "12"
    assert year_data["rec"]      == "40"
    assert year_data["rec_yds"]  == "217"
    assert year_data["rec_td"]   == "1"

def test_scrape_multiple_players():
    scraper   = PFRScraper(0.5)
    scraper.scrape_player("Saquon", "Barkley", "RB")
    scraper.scrape_player("Aaron", "Jones", "RB")
    scraper.scrape_player("Tevin", "Coleman", "RB")
    players = scraper.get_rbs()
    assert len(players) == 3
    assert players.get("Saquon Barkley")
    assert players.get("Aaron Jones")
    assert players.get("Tevin Coleman")