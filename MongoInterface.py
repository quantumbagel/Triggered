from pymongo import MongoClient


def get_client():
    return MongoClient("localhost", 27017)
