import os
import subprocess
from dataclasses import asdict
from datetime import datetime

import pync
from pymongo import MongoClient

import aux_funcs, sys, json, time, random
from LevPasha.InstagramAPI import InstagramAPI
from dotenv import load_dotenv

load_dotenv()

followers = []
followings = []
# args = aux_funcs.get_args()
# api  = InstagramAPI(args.user, args.password)

ig_user = os.getenv("IG_USER")
ig_password = os.getenv("IG_PASSWORD")
ig_tag = os.getenv("TARGET_TAG")

if not ig_user or not ig_password:
	raise Exception("Missing IG password / IG user")

api = InstagramAPI(ig_user, ig_password)

### Delay in seconds ###
min_delay = 5
max_delay = 10
MAXIMO = 100

client = MongoClient('localhost', 27017)
db = client['thoughtfulcoffeenyc-local']
db_collection = db['users']


def printUsage():
	print("Usage: \n+ python main.py -u USERNAME -p PASSWORD -o info: Show report")
	print("+ python main.py -u USERNAME -p PASSWORD -o follow-tag -t TAG: Follow users using the tags you introduce")
	print("+ python main.py -u USERNAME -p PASSWORD -o follow-location -t LOCATION_ID: Follow users from a location")
	print("+ python main.py -u USERNAME -p PASSWORD -o follow-list -t USER_LIST: Follow users from a file")
	print("+ python main.py -u USERNAME -p PASSWORD -o super-followback: Follow back all the users who you dont follow back")
	print("+ python main.py -u USERNAME -p PASSWORD -o super-unfollow: Unfollow all the users who dont follow you back")
	print("+ python main.py -u USERNAME -p PASSWORD -o unfollow-all: Unfollow all the users")


def info():
	print("I follow them but they dont follow me:\n")
	tot = 0
	for i in followings:
		if i not in followers:
			tot=tot+1
			print(str(tot)+" "+i)
	print("\nTotal: "+str(tot))

	print("\nThey follow me but i dont follow them:\n")
	tot = 0
	for i in followers:
		if i not in followings:
			tot=tot+1
			print(str(tot)+" "+i)
	print("\nTotal: "+str(tot))

	print("\nPeople following me:\n")
	tot = 0
	for i in followers:
		tot=tot+1
		print(str(tot)+" "+i)
	print("\nTotal: "+str(tot))

	print("\nPeople I follow:\n")
	tot = 0
	for i in followings:
		tot=tot+1
		print(str(tot)+" "+i)
	print("\nTotal: "+str(tot))


def follow_tag(tag):
	api.tagFeed(tag)
	media_id = api.LastJson
	tot = 0
	print("\nTAG: "+str(tag)+"\n")
	for i in media_id["items"]:
		time.sleep(float( random.uniform(min_delay*10,max_delay*10) / 10 ))
		username = i.get("user")["username"]
		user_id = i.get("user")["pk"]
		api.follow(user_id)
		tot += 1
		print("Following "+str(username)+" (with id "+str(user_id)+")")
		if(tot>=MAXIMO):
			break
	print("Total: "+str(tot)+" for tag "+tag+" (Max val: "+str(MAXIMO)+")\n")


def follow_location(target):
	api.getLocationFeed(target)
	media_id = api.LastJson
	tot = 0
	for i in media_id.get("items"):
		time.sleep(float( random.uniform(min_delay*10,max_delay*10) / 10 ))
		username = i.get("user").get("username")
		user_id = aux_funcs.get_id(username)
		api.follow(user_id)
		tot += 1
		print("Following "+str(username)+" (with id "+str(user_id)+")")
		if(tot>=MAXIMO):
			break
	print("Total: "+str(tot)+" for location "+str(target)+" (Max val: "+str(MAXIMO)+")\n")


def follow_list(target):
	user_list = open(target).read().splitlines()
	tot = 0
	for username in user_list:
		time.sleep(float( random.uniform(min_delay*10,max_delay*10) / 10 ))
		user_id = aux_funcs.get_id(username)
		api.follow(user_id)
		tot += 1
		print("Following "+str(username)+" (with id "+str(user_id)+")")
		if(tot>=MAXIMO):
			break
	print("Total: "+str(tot)+" users followed from "+str(target)+" (Max val: "+str(MAXIMO)+")\n")


def super_followback():
	count = 0
	for i in followers:
		if i not in followings:
			count+=1
			time.sleep(float( random.uniform(min_delay*10,max_delay*10) / 10 ))
			print(str(count)+") Following back "+i)
			user_id = aux_funcs.get_id(i)
			api.follow(user_id)


def super_unfollow():
	whitelist = open("whitelist.txt").read().splitlines()
	count = 0
	for i in followings:
		if (i not in followers) and (i not in whitelist):
			count+=1
			time.sleep(float( random.uniform(min_delay*10,max_delay*10) / 10 ))
			print(str(count)+") Unfollowing "+i)
			user_id = aux_funcs.get_id(i)
			api.unfollow(user_id)


def unfollowall():
	whitelist = open("whitelist.txt").read().splitlines()
	count = 0
	for i in followings:
		if i not in whitelist:
			count +=1
			time.sleep(float( random.uniform(min_delay*10,max_delay*10) / 10 ))
			print(str(count)+") Unfollowing "+i)
			user_id = aux_funcs.get_id(i)
			api.unfollow(user_id)



#### Code below is used to show a mac os notification:
# https://stackoverflow.com/questions/17651017/python-post-osx-notification
CMD = '''
on run argv
  display notification (item 2 of argv) with title (item 1 of argv)
end run
'''

def notify(title, text):
  subprocess.call(['osascript', '-e', CMD, title, text])

#### End


def main(
	total_minutes_to_add = 12,
	time_limit = 30,
	target_tag = "pourover",
):
	"""
	total_minutes_to_add: The amount of minutes to add after when the script
		is designated to run.

	"""

    # Don't use the helper function.
	api.login()

	assert api.rank_token

	for i in api.getTotalSelfFollowers():
		# looks like we work off of the username?
		followers.append(i.get("username"))

	for i in api.getTotalSelfFollowings():
		user = aux_funcs.IGUser.create(
			ig_user_name=i['username'],
			ig_full_name=i['full_name'],
			ig_user_pk=i['pk'],
			tag_used=ig_tag,
			for_account=ig_user,
		)
		if db_collection.find_one({"ig_user_pk": user.ig_user_pk}):
			print(f"Found existing user: {user.ig_user_pk} // {user.ig_user_name}")
			continue
		else:
			print(f"Inserting user: {user}")

		db_collection.insert_one(asdict(user))
		followings.append(i.get("username"))

	print(f"Starting to follow for target: {target_tag}")
	follow_tag(target_tag)
#
# while True:
# 	# How this is going to work is that every 2 hours, we are going to run
	# 	# a script to help
	#
	# 	now = datetime.now()
	# 	if now.hour % 2 == 0 and now.minute == 5:
	# 		if total_minutes_to_add > time_limit:
	# 			total_minutes_to_add = total_minutes_to_add - time_limit
	#
	# 			# Sleep for XX minutes to cause randomness
	# 			time.sleep(total_minutes_to_add * 60)
	#
	# 			print(f"Starting scrape at: {datetime.now()}")
	#
	# 			notify("IG script", "Starting follow")
	#
	# 			# Then we run
	# 			follow_tag(target_tag)


if __name__ == "__main__":
    main(target_tag=os.getenv("TARGET_TAG", ""))
