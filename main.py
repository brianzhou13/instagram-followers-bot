import os
import subprocess
from dataclasses import asdict
from datetime import datetime
import platform

from dateutil.relativedelta import relativedelta
from pymongo import MongoClient
from slack_sdk import WebClient

import aux_funcs, time, random
from LevPasha.InstagramAPI import InstagramAPI
from dotenv import load_dotenv

system = platform.system().lower()

load_dotenv()

followers = []
followings = []
# args = aux_funcs.get_args()
# api  = InstagramAPI(args.user, args.password)

ig_user = os.getenv("IG_USER")
ig_password = os.getenv("IG_PASSWORD")
ig_tag = os.getenv("TARGET_TAG")
mongo_uri = os.getenv("MONGO_URI", "")


if not ig_user or not ig_password:
	raise Exception("Missing IG password / IG user")

api = InstagramAPI(ig_user, ig_password)

MAXIMO = 100

print(f"connecting to: {mongo_uri}")

client = MongoClient(mongo_uri)
db = client['thoughtfulcoffeenyc']
db_collection = db['users']

slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
print("setup slack client")


def send_slack_msg(msg):
	print(f"sending slack msg: {msg}")
	slack_client.chat_postMessage(channel='broker', text=msg)
	print("send slack msg")


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
	# See if we can make it so _multiple_ tags can be used
	api.tagFeed(tag)
	media_id = api.LastJson
	tot = 0
	print("\nTAG: "+str(tag)+"\n")
	for i in media_id["items"]:
		aux_funcs.apply_random_time_lag()
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
		aux_funcs.apply_random_time_lag()
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
		aux_funcs.apply_random_time_lag()
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
			aux_funcs.apply_random_time_lag()
			print(str(count)+") Following back "+i)
			user_id = aux_funcs.get_id(i)
			api.follow(user_id)


def super_unfollow():
	whitelist = open("whitelist.txt").read().splitlines()
	count = 0
	for i in followings:
		if (i not in followers) and (i not in whitelist):
			count+=1
			aux_funcs.apply_random_time_lag()
			print(str(count)+") Unfollowing "+i)
			user_id = aux_funcs.get_id(i)
			api.unfollow(user_id)


def unfollowall():
	whitelist = open("whitelist.txt").read().splitlines()
	count = 0
	for i in followings:
		if i not in whitelist:
			count +=1
			aux_funcs.apply_random_time_lag()
			print(str(count)+") Unfollowing "+i)
			user_id = aux_funcs.get_id(i)
			api.unfollow(user_id)


def build_followers_followings():
	"""
	This is a weird function where we build the global lists [followers/followings].

	Then as a side-effect, we also record any users we don't have tracked within
	our database
	"""
	print("Starting to get people who follow US")
	for i in api.getTotalSelfFollowers():
		# looks like we work off of the username?
		if i not in followers:
			# looks like there might be dupes in `followers`, so only append
			# if they aren't present
			followers.append(i.get("username"))

	print("Finished getting followers")

	print("Starting to get who we follow")
	for i, val in enumerate(api.getTotalSelfFollowings()):
		if i % 100 == 0:
			print(f"Finished getting: {i} followers")

		user = aux_funcs.IGUser.create(
			ig_user_name=val['username'],
			ig_full_name=val['full_name'],
			ig_user_pk=val['pk'],
			tag_used=ig_tag,
			for_account=ig_user,
		)

		filter_dict = {
			"ig_user_pk": user.ig_user_pk,
			"for_account": ig_user,
		}

		user_doc = db_collection.find_one(filter_dict)

		if not user_doc:
			db_collection.insert_one(asdict(user))
		elif user_doc and user.status == aux_funcs.IGUserStatus.unfollowed:
			print(f"Updating user: {user.ig_user_name} back to follower status")
			# I think this is the case where the DB record says we've unfollowed them... but in reality,
			# we are still following them; therefore, this is logic to rectify our records.
			db_collection.find_one_and_update(asdict(user), {"$set": {"status": aux_funcs.IGUserStatus.follower}})

		followings.append(val.get("username"))
	print("Finished getting who we follow")


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
	print("About to login")
	api.login()
	print("finished logging in")

	assert api.rank_token

	print("Building followers followings")
	build_followers_followings()

	print(f"Starting to follow for target: {target_tag}")

	print("kicking off while-loop")
	block_unfollow = False

	follow_tag(target_tag)

	while True:
		# Note:
		# Since everything runs synchronously, the first `#if` condition takes a while, and
		# overshadows the "unfollow"; therefore, this doesn't let the while-loop consistently reach the
		# unfollow task. Consider decoupling the two (?) Have one service purely run for logging-out, while
		# another to login? Have both processes share a redis connection, and use that to apply a lock to
		# not have two "following" processes running concurrently.


		# TODO:
		# Before following, maybe do some validation on the account we are about to follow. If it's a dummy
		# account with no followings, an account with no posts, or an account that has a huge imbalance of follower-to-following
		# ratio, don't follow
		now = datetime.now()
		# Apply a second check as this'll keep calling otherwise (I think)
		if now.hour % 2 == 0 and now.minute == 33 and now.second == 45:
			aux_funcs.apply_random_time_lag()

			if system == "darwin":
				notify("IG script", "Starting follow")
			else:
				send_slack_msg(f"Starting following accounts for {ig_user} // {target_tag}")

			# Then we run
			follow_tag(target_tag)

			send_slack_msg("Done following accounts!")

			# after a successful run here, we can reset to False to allow
			# ourselves to run the unfollow code again
			block_unfollow = False

		elif now.minute == 5 and block_unfollow is False and now.second == 23:
			# Unfollow 5 at a time
			# Find instances that have been 5 days before today, and we
			# are only just following
			if system == "darwin":
				notify("IG script", "Starting unfollow")
			else:
				send_slack_msg("Starting to unfollow accounts!")

			data = list(db_collection.find({
				"created": {"$lte": datetime.today() - relativedelta(days=5)},
				"for_account": ig_user,
				"status": aux_funcs.IGUserStatus.follower,
			}).limit(5))

			print("To unfollow: ", data)

			num_accounts_unfollowed = 0

			for d in data:
				# need to figure out how to determine that they aren't following us
				# maybe before we run, we do a check that they are following us
				#     if d.ig_user_name not in following:
				# this means that they aren't following us
				# so we should likely unfollow them
				if d['ig_user_name'] not in followers:
					if block_unfollow is True:
						# keep skipping -- this only gets set as True when
						# we hit an exception
						print("SKIPPING AS block_unfollow is: True")
						continue

					print(f"Setting {d['ig_user_name']} // {d['_id']} to unfollowed")

					# unfollow user -- copied from super_unfollow
					resp = None
					try:
						user_id = aux_funcs.get_id(d['ig_user_name'])
						aux_funcs.apply_random_time_lag()
						resp = api.unfollow(user_id)
						if resp is False:
							raise Exception("Response from unfollow API is false")
						num_accounts_unfollowed += 1
					except Exception as err:
						block_unfollow = True
						send_slack_msg(f"Hit an exception {err} and done unfollowing {num_accounts_unfollowed} accounts!")
						continue

					# copied over from superunfollow
					aux_funcs.apply_random_time_lag()

					if resp is True:
						# after unfollowing, update
						db_collection.find_one_and_update(
							{
								"_id": d["_id"],
								"for_account": "thoughtfulcoffeenyc",
								"ig_user_name": d['ig_user_name'],
							},
							{
								"$set": {
									"status": aux_funcs.IGUserStatus.unfollowed,
								},
							}
						)
					else:
						raise Exception("Error with persisting unfollow on the mongo-layer")

if __name__ == "__main__":
    main(target_tag=os.getenv("TARGET_TAG", ""))

	# Run below for a info report
	# api.login()
	# build_followers_followings()
	# info()
