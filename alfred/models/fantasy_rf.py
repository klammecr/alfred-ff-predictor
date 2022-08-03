# Third party
import sys
import os
from math import floor
import numpy as np
import random
import pandas as pd

# Sklearn helpers
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error as mse

# Our modules
from alfred.data.dataset_generator import DatasetGenerator

class FantasyRF:

    def __init__(self,seed):
        # Seed for rng
        self.m_seed = seed
        random.seed(seed)
        
    # Wrapper for sklearn RMSE
    def calc_mse(self):
        return mse(self.m_y_actual, self.m_y_pred)

    # Experimental method
    def random_search_hyperparameters(self, X, y):
        from sklearn.model_selection import RandomizedSearchCV
        param_grid = {
            'bootstrap': [True],
            'max_depth': [70, 80, 90, 100],
            'max_features': ["sqrt", "log2"],
            'min_samples_leaf': list(range(1, 9)),
            'min_samples_split': [2, 5, 8, 10, 12],
            'n_estimators': [1000]
        }
        rf_random = RandomizedSearchCV(estimator = RandomForestRegressor(), param_distributions = param_grid, n_iter = 100, cv = 5, verbose=1, random_state=7269, n_jobs = -1, return_train_score=True)
        # Fit the random search model
        rf_random.fit(X, y)
        print("Best hyperparameters: \n" )
        print(rf_random.best_params_)

    # Experimental method for Cross-Validation Testing
    # def experiment_forest(self):
    #     # Change
    #     self.m_bScrape = True
    #     print("Running for User: ", self.m_user)
    #     data_dict = self.PrepareData(15)
    #     print("Numbers of Records: ", len(data_dict["data"]))
    #     X = get_x(data_dict["data"])
    #     y = GetY(data_dict["data"])
    #     splits = 5
    #     # Split the data with 5 Fold Cross-Validation
    #     kf = KFold(n_splits = splits)
    #     # MSE of splits
    #     mse = []
    #     for train_idx, test_idx in kf.split(X):
    #         X_train, X_test = X[train_idx], X[test_idx]
    #         y_train, self.m_y_actual = y[train_idx], y[test_idx]
    #         self.MakeForest(X_train, y_train, True)
    #         self.m_y_pred = self.Predict(X_test)
    #         mse.append(self.CalcMSE())

    #     cv_mse = str(sum(mse) / len(mse))
    #     print(self.m_user + " Mean Squared Error: " + cv_mse)

    #     # Print out the hyperparametrs
    #     # self.RandomSearchHyperparameters(X, y)
    #     return cv_mse

    def make_forest(self, X, y, bSuccess):
        if len(X) != 0 and len(y) != 0 and bSuccess:
            forest = RandomForestRegressor(n_estimators= 200,
                                                    min_samples_split= 8,
                                                    min_samples_leaf= 5,
                                                    max_features= "log2",
                                                    max_depth= 100,
                                                    bootstrap= True)
            self.rf = forest.fit(X, y)
        else:
            bSuccess = False
        return bSuccess


    def Predict(self, X):
        return self.rf.predict(X)


# Main script for testing functionality/sandboxing
if __name__ == '__main__':
    # See if the inheiritance/init is working
    generator = DatasetGenerator(2005, 2020)
    # rb_data = generator.Generate()
    data = generator.load_dataset
    X, y = generator.format_into_dataset(data)
    
    rf = FantasyRF(6969)
    rf.make_forest(X, y, True)