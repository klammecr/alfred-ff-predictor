from pymongo import MongoClient
import os
import sys

class PlayerDatabaseInterface():
    def __init__(self):
        uri = "mongodb+srv://alfredff.kn5rt.mongodb.net/myFirstDatabase?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
        certificate = os.path.dirname(sys.path[0]) + "\\X509-cert-8030949330423776470.pem"
        self.client = MongoClient(uri,
                     tls=True,
                     tlsCertificateKeyFile=certificate)

        # Create RB table
        self.db = self.client.player_data

    def insert_rb(self, data):
        """Insert a running back into the database

        Args:
            data (dict): The data for one running back
        """
        result = self.db.rb.insert_one(data)

    def ReadAllRBData(self):
        data = self.db.rb.find({})
        return data
