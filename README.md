# instagram-followers-bot

---

# Our Edits:

### Added Functionality:

* [ ] Have this script run autonomously. So we execute it, and then the program knows when to kickoff the scraping
  function
        - lower priority
* [ ] Add in a cron/section that'll check when to remove/unfollow certain followers
    - We should unfollow the users that don't follow us back. This way, our profile seems more even.
    - This'll require us to read from a database or a store. I'm thinking mongo.
        - By doing it mongo, we can probably add in additional metadata behind the users we are following. For example,
          we can capture the hashtag for the run, date when we followed them, etc. There is the chance that this is useless..
          * [ ] Define the mongo schema
                - We can create the database in atlas, then we'll connect to it through jupyter
                - With the connection, then we can run scripts against it to build out the schema
            

- I'm thinking we can just use heroku now. We just need a box that runs.. in the cloud. Technically, this can just be an EC2 instance; however, we'd have to figure out how to pull that code.

 
## Workflow:
1. We kick off the script to start following:
2. We get back a list of users per the hashtag
3. For each match, do a DB read against that user to see its status/standing
    - If it's on `.on_blacklist`:
        - Don't follow
    - Else:
        - Follow account and persist the account
    
5. _cron job that runs_:
    - Loop through existing followers
    - Build a list of people that don't follow us back
    - Read that user's info from our DB 
        - If they are on whitelist:
            - No-op
        - Else:
            - Begin unfollow
            - Update the account instance with unfollow information
                - set date_unfollowed
                - set on_blacklist
                - set is_a_follower (?)
                    - this might be how we track/persist this field
            

```
{
    'pk': 9379218679,
    'username': 'choux_soutenable',
    'full_name': '川口 衆',
    'is_private': False,
    'profile_pic_url': 'https://scontent-lga3-1.cdninstagram.com/v/t51.2885-19/s150x150/90433716_261037404897788_1773551554553446400_n.jpg?_nc_ht=scontent-lga3-1.cdninstagram.com&_nc_ohc=ILcdDSCnpBcAX-noovj&edm=APQMUHMBAAAA&ccb=7-4&oh=3464465743b238ec35404f8caad0619c&oe=614E197D&_nc_sid=e5d0a6',
    'profile_pic_id': '2272295535497736256_9379218679', 
    'is_verified': False, 
    'follow_friction_type': 0,
    'has_anonymous_profile_picture': False,
    'account_badges': [],
    'latest_reel_media': 0
}
## ^ what is returned from `getTotalSelfFollowers`
##  I don't think we really need the other bits of information

# would there be any reason we don't want to follow a match?

{
    ig_user_name: str
    ig_user_pk: str
    tag_used: str
    for_account: [thoughtfulcoffeenyc/ thoughtfulcandlesnyc]
    datetime: date
        - date we've followed this match
    dont_unmatch: bool
        - These are whitelisted users that we want to follow even though they don't follow us
            - ex: Devocion / Partners / Sey
    on_blacklist: bool
        - default: False
            - this'll get set automatically per the cron job
    is_a_follower: bool
        - but how do we track this?
}
```
            

---

Functionality:

- **Info**: Show report

- **Follow users**: from tag, from location, from a list or follow back who you do not follow back

- **Unfollow users**: who do not follow you back or all of them

---------------------

## Usage:

**Show report (who follows, unfollows, follows you back):**

```
python main.py -u USERNAME -p PASSWORD -o info
```

**Follow users using the tag you introduce:**

```
python main.py -u USERNAME -p PASSWORD -o follow-tag -t TAG
```

**Follow users from a location:**

```
python main.py -u USERNAME -p PASSWORD -o follow-location -t LOCATION_ID
```

**Follow back all the users who you don't follow back:**

```
python main.py -u USERNAME -p PASSWORD -o super-followback
```

**Follow users from a list:**

```
python main.py -u USERNAME -p PASSWORD -o follow-list -t USER_LIST
```

**Unfollow all the users who don't follow you back:**

```
python main.py -u USERNAME -p PASSWORD -o super-unfollow
```

**NOTE**: Fill "whitelist.txt" file with the accounts you will never want to unfollow

**Unfollow all the users:**

```
python main.py -u USERNAME -p PASSWORD -o unfollow-all
```

**NOTE**: Fill "whitelist.txt" file with the accounts you will never want to unfollow

---------------------

## Examples:

*python main.py -u USERNAME -p PASSWORD -o follow-tag -t cat* : **Follow users using the tag 'cat'**

*python main.py -u USERNAME -p PASSWORD -o follow-location -t 127963847* : **Follow users from Spain**

*python main.py -u USERNAME -p PASSWORD -o super-followback*: **Now you are following users you didn't follow but they
followed you**

*python main.py -u USERNAME -p PASSWORD -o follow-list -t userlist.txt* : **Follow users in each line of userlist.txt**

*python main.py -u USERNAME -p PASSWORD -o super-unfollow*: **Now you are not following users who don't follow you**


---------------------

## Acknowledgment

The really good repo is the levpasha's one (https://github.com/LevPasha/Instagram-API-python)

---------------------

## Note

Tested both in Python2.x (2.7.15rc1) and Python 3.x (3.6.7)