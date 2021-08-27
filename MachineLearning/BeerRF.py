from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
#from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error as mse
from sklearn.externals import joblib
import pandas as pd
from sklearn.ensemble import forest
from sklearn.pipeline import Pipeline
from math import floor
import numpy as np
import random
from json import loads, dumps

# Get Data Retrieval Modules
import sys
sys.path.append("../../DataRetrieval/src")
from UntappdWebScraper import UntappdWebScraper
from DescriptionTagger import DescriptionTagger

# Recommender System Modules
from EncoderHelper import GetX, GetY
from FeatureExtractor import FeatureExtractor
from BayesianTargetEncoder import BayesianTargetEncoder

class BeerRF:

    def __init__(self, user, seed, tagger, encoder, settings):
        # Seed for rng
        self.m_seed = seed
        random.seed(seed)
        # Mostly for debug
        self.m_bScrape = True
        if self.m_bScrape:
            # Untappd Web Scraper for retreving user information
            self.m_scraper = UntappdWebScraper(settings["servers"]["untappd_proxy"],
                                                    .5,
                                                    settings["keys"]["ratebeer"])
        # User the random forest it for (Untappd Username)
        self.m_user = user
        # Beer list data for user
        self.m_beerList = []
        # Create Random Forest object
        # Best hyperparameters as calculated by most often
        self.m_rf = RandomForestRegressor(n_estimators= 500,
                                                min_samples_split= 8,
                                                min_samples_leaf= 5,
                                                max_features= "sqrt",
                                                max_depth= 100,
                                                bootstrap= True)
        # Beer tagger object
        self.m_tagger = tagger
        # Beer encoder object
        self.m_encoder = encoder
        # List of all the features
        self.m_features = self.m_tagger.GetBETags() + self.m_encoder.GetBaseStyles()
        # Predictions
        self.m_y_pred = np.array([])
        self.m_y_actual = np.array([])
        # Opposite of the debug flag
        self.m_bProduction = bool(1 ^ int(settings["debug"]))

    def GetBeerList(self):
        return self.m_beerList
    def GetNumBeers(self):
        return len(self.m_beerList)

    # Wrapper for sklearn RMSE
    def CalcMSE(self):
        return mse(self.m_y_actual, self.m_y_pred)

    def GetDataFromFile(self):
        glob_data = open("../../Data/global_data_new.json", "r")
        glob_json = loads(glob_data.read())
        beerList = []
        if self.m_user in glob_json.keys():
            beerList = glob_json[self.m_user]
        return beerList

    def LoadModelFromFile(self, file):
        self.m_pipeline = joblib.load(file)

    # Experimental method
    def RandomSearchHyperparameters(self, X, y):
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
        print("Best hyperparameters for: " + self.m_user + "\n" )
        print(rf_random.best_params_)

    # Experimental method for Cross-Validation Testing
    def ExperimentForest(self):
        # Change
        self.m_bScrape = True
        print("Running for User: ", self.m_user)
        data_dict = self.PrepareData(15)
        print("Numbers of Records: ", len(data_dict["data"]))
        X = GetX(data_dict["data"])
        y = GetY(data_dict["data"])
        splits = 5
        # Split the data with 5 Fold Cross-Validation
        kf = KFold(n_splits = splits)
        # MSE of splits
        mse = []
        for train_idx, test_idx in kf.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, self.m_y_actual = y[train_idx], y[test_idx]
            self.MakeForest(X_train, y_train, True)
            self.m_y_pred = self.Predict(X_test)
            mse.append(self.CalcMSE())

        cv_mse = str(sum(mse) / len(mse))
        print(self.m_user + " Mean Squared Error: " + cv_mse)

        # Print out the hyperparametrs
        # self.RandomSearchHyperparameters(X, y)
        return cv_mse

    def PrepareData(self, threshold):
        if self.m_bScrape:
            # Scrape the user's information
            beers = self.m_scraper.ScrapeUser(self.m_user)
        else:
            beers = self.GetDataFromFile()

        # Instaniate a return structure
        returnDict = {"success":True, "data":[]}
        # Give the pure list to the encoders
        beers = beers["beers"]
        if len(beers) >= threshold:
            beers = [self.m_encoder.TagAndEncodeBeer(beer) for beer in beers]
            # Randomize the lisst to rid implicit trends
            random.shuffle(beers)
            # Set the class variable
            self.m_beerList = beers.copy()
            returnDict["data"] = beers
        else:
            # We failed to prepare data
            returnDict["success"] = False
        return returnDict

    def MakePredictProductionForest(self, inData, threshold):
        [outData, bSuccess] = self.MakeProductionForest(inData, True, threshold)
        return [outData, bSuccess]

    def MakeProductionForest(self, inBeerList, bGetPrediction, threshold):
        outData = []
        # Get the data and create the forest
        [train_X, train_y, bSuccess] = self.GetData(threshold)
        if bSuccess:
            bSuccess = self.MakeForest(train_X, train_y, bSuccess)

        if bSuccess:
            if bGetPrediction and inBeerList:
                # Tag and encode beers to be predicted
                inBeerList = [self.m_encoder.TagAndEncodeBeer(beer) for beer in inBeerList]
                X = GetX(inBeerList)
                print("inBeerList", inBeerList)
                print("X inBeerList: ", X)
                outData = self.Predict(X)
                print(outData)

            # Dump the file
            filename = '../../Data/models/' + self.m_user + '.sav'
            joblib.dump(self.m_pipeline, filename)
            """
            Bugfix: Need to store the number of beers a user has.
            I was doing this incorrectly before, eventually we will have a DB
            now, lets just make a text file in the models directory
            """
            f = open('../../Data/user_info/' + self.m_user + ".json","w+")
            if f:
                user_info = {"num_beers" : str(train_y.size)}
                f.write(dumps(user_info))
                f.close()
            else:
                bSuccess = False
        return [outData, bSuccess]

    def GetData(self, threshold):
        data_dict = self.PrepareData(threshold)
        data = data_dict["data"]
        X = GetX(data) if data else []
        y = GetY(data) if data else []
        return [X, y, data_dict["success"]]

    def MakeForest(self, X, y, bSuccess):
        if X.size != 0 and y.size != 0 and bSuccess:
            sample_forest = RandomForestRegressor(n_estimators= 200,
                                                    min_samples_split= 8,
                                                    min_samples_leaf= 5,
                                                    max_features= "log2",
                                                    max_depth= 100,
                                                    bootstrap= True)
            rf = sample_forest.fit(X, y)
            # Pipeline for selecting features and predicting
            self.m_pipeline = Pipeline([
                ("feat_select" , FeatureExtractor(y, self.m_features, rf)),
                ("encoder", BayesianTargetEncoder(3)),
                ("predictor", self.m_rf)
            ])
            self.m_pipeline.fit(X, y)
        else:
            bSuccess = False
        return bSuccess


    # Wrapper for outside functions to predict and return results
    # Pass in the beer list not the JSON object
    def Predict(self, inData):
        if isinstance(inData, (np.ndarray, np.generic) ):
            X = inData
        else:
            inData = [self.m_encoder.TagAndEncodeBeer(beer) for beer in inData]
            X = GetX(inData)
        return self.m_pipeline.predict(X)
