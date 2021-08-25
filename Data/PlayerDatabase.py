from pymongo import MongoClient
import urllib
import os
import sys

class PlayerDatabase():
    def __init__(self):
        uri = "mongodb+srv://alfredff.kn5rt.mongodb.net/myFirstDatabase?authSource=%24external&authMechanism=MONGODB-X509&retryWrites=true&w=majority"
        certificate = os.path.dirname(sys.path[0]) + "\\X509-cert-8030949330423776470.pem"
        self.client = MongoClient(uri,
                     tls=True,
                     tlsCertificateKeyFile=certificate)

        # Create RB table
        self.db = self.client.player_data

    def InsertRB(self, data):
        result=self.db.rb.insert_one(data)
