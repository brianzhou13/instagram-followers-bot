from dataclasses import dataclass, asdict
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient


# https://www.w3schools.com/python/python_mongodb_create_collection.asp
# The w3schools is pretty helpful with notes on how to use pymongo
#
# * we don't create the table until it's populated with something (a collection with a single document)
from aux_funcs import get_ig_api, IGUser

# load up env
load_dotenv()

client = MongoClient('localhost', 27017)

db = client['thoughtfulcoffeenyc-local']
db_collection = db['users']


def run_backfill():
    followers = []
    followings = []
    ig_response = get_ig_api()

    api = ig_response.api
    api.login()

    for i in api.getTotalSelfFollowers():
        followers.append(i.get("username"))

    for i in api.getTotalSelfFollowings():
        user = IGUser.create(
            ig_user_name=i['username'],
            ig_full_name=i['full_name'],
            ig_user_pk=i['pk'],
            tag_used=ig_response.ig_tag,
            for_account=ig_response.ig_user
        )
        if db_collection.find_one({"ig_user_pk": user.ig_user_pk}):
            print(f"Found existing user: {user.ig_user_pk} // {user.ig_user_name}")
            continue
        else:
            print(f"Inserting user: {user}")

        db_collection.insert_one(asdict(user))
        followings.append(i.get("username"))


if __name__ == "__main__":
    run_backfill()
