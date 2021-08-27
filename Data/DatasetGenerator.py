import sys
import os
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(sys.path[0]))

# Modules
from Data.PlayerDatabase import PlayerDatabase
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

        self.stat_features = {}
        self.other_features = {}
        self.stat_features['rb'] = ['rush', 'rush_yds', 'rush_td', 'rec', 'rec_yds', 'rec_td', 'av', 'college_data', 'scrim_yds', 'scrim_tds']
        self.other_features['rb'] = ['age']
    
    def Generate(self):
        if self.position_group == "RB":
            data = self.fft_scraper.ScrapeTop25RBFromYears(self.start_year, self.stop_year)
        return data

    def Save(self, data, position_group):
        if position_group == "RB":
            self.db.InsertRB(data)

    def LoadDataset(self):
        data = self.db.ReadAllRBData()
        return data

    def FormatIntoDataset(self, col):
        # Features
        X = []
        # Where they finished in RB Rankings
        y = []
        for all_year_data in col:
            for year in all_year_data:
                if year.isnumeric():
                    year_data = all_year_data[year]              
                    for idx, player in enumerate(year_data):
                        # Extract what we care about into the dataset
                        player_data = year_data[player]
                        
                        # Deal with the historical data
                        years = list(player_data.keys())
                        years = [year for year in years if year.isnumeric()]
                        if len(years) > 1:
                            features = list(player_data[years[0]].keys())
                            # Arrays of numpy arrays for storage
                            historical_data = []
                            truth_data = []
                            for year in years:
                                # Don't get the last year, that is our truth                               
                                player_year_data = {}
                                for feature in features:                                                    
                                    if feature in self.stat_features['rb']:
                                        stat = player_data[year][feature]
                                        if stat.isnumeric():
                                            stat_val = int(player_data[year][feature])
                                        else:
                                            stat_val = 0
                                        if 'td' in feature:
                                            if 'td' in player_year_data:
                                                player_year_data['td'] += stat_val
                                            else:
                                                player_year_data['td'] = stat_val
                                        elif 'yds' in feature:
                                            if 'yds' in player_year_data:
                                                player_year_data['yds'] += stat_val
                                            else:
                                                player_year_data['yds'] = stat_val
                                        else:
                                            player_year_data[feature] = stat_val
                                if year != years[-1]:
                                    historical_data.append(np.array(list(player_year_data.values())))
                                else:
                                    truth_data.append(np.array(list(player_year_data.values())))
                            
                            # Make sure it's in the correct format
                            historical_data = np.array(historical_data)
  
                            # We have the current year data (truth) and previous year data, let's combine for some features
                            historical_data_len = len(years) - 1
                            weight_mtx = np.array([(i+1) / historical_data_len for i in range(historical_data_len)])
                            weight_mtx = np.divide(weight_mtx, np.sum(weight_mtx, axis=0))
                            weight_mtx = np.reshape(weight_mtx, (1, historical_data_len))
                            
                            # Weight the stats
                            weight_stats = np.matmul(weight_mtx, historical_data)

                            # Add some historical context like if it is decreasing or increasing over time
                            roc_data = (historical_data[-1, :] - historical_data[0, :]) / 2
                            weight_stats = np.hstack((weight_stats[0], roc_data))

                            # Include other factors like age or categorical variables
                            other_vec = []
                            for feature in self.other_features['rb']:
                                if feature == "age":
                                    age = int(player_data[years[-1]]['age'])
                                    age_oh_enc_1 = 0
                                    age_oh_enc_2 = 0
                                    age_oh_enc_3 = 0
                                    if age <= 25:
                                        pass
                                    elif age > 25 and age <=30:
                                        age_oh_enc_3 = 1
                                    elif age > 30 and age <= 35:
                                        age_oh_enc_2 = 1
                                    elif age > 35 and age <= 40:
                                        age_oh_enc_2 = 1
                                        age_oh_enc_3 = 1
                                    elif age > 40:
                                        age_oh_enc_1 = 1

                                    other_vec.append(age_oh_enc_1)
                                    other_vec.append(age_oh_enc_2)
                                    other_vec.append(age_oh_enc_3)

                            # Add the other features
                            player_feats = np.hstack((weight_stats, np.array(other_vec)))

                        # Append the data as a row
                        X.append(player_feats)
                        y.append(idx+1)
        return (X, y)

# Main script for testing functionality/sandboxing
if __name__ == '__main__':
    # See if the inheiritance/init is working
    generator = DatasetGenerator(2005, 2020)
    # rb_data = generator.Generate()
    data = generator.LoadDataset()
    X, y = generator.FormatIntoDataset(data)
    pass
