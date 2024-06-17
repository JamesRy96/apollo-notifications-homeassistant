#!/usr/bin/env python3

import praw
import pyotp
import json
import os
import sys
import pwd
import prawcore.exceptions
import time
from datetime import datetime
from dotenv import load_dotenv
from requests import post

def log(*a):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(timestamp, *a, file=sys.stderr)


# Get the directory of the current script
base_dir = os.path.dirname(os.path.abspath(__file__))

# Create the full path to the .env file
env_path = os.path.join(base_dir, 'config', 'notify.config')
# Load the .env file
load_dotenv(dotenv_path=env_path)

# 2FA secret (if using 2FA)
KEY             = os.getenv("REDDIT_2FA_KEY")

# reddit oauth - create "personal use script" app at https://old.reddit.com/prefs/apps/
CLIENT_ID       = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET   = os.getenv("REDDIT_CLIENT_SECRET")

# reddit username/password
USERNAME        = os.getenv("REDDIT_USERNAME")
PASSWORD        = os.getenv("REDDIT_PASSWORD")

#Home Assistant
HA_TARGET = os.getenv("NOTIFICATION_TARGET")
HA_URL = os.getenv("HOMEASSISTANT_URL") + "/api/services/notify/" + HA_TARGET
HA_TOKEN = os.getenv("HOMEASSISTANT_API_KEY")
APOLLO_ICON_URL = os.getenv("APOLLO_ICON_URL")

# Refresh Interval
REFRESH_INTERVAL = os.getenv("REFRESH_INTERVAL")

log("Loaded environment variables")

if len(KEY) >0:
    totp = pyotp.TOTP(KEY)
    log("Using 2FA in authentication")
else:
    log("Not using 2FA in authentication")

log("Reddit username: %s" % (USERNAME))
log("Home Assistant URL: %s" % (HA_URL))
log("Home Assistant notifcation target: %s" % (HA_TARGET))
log("Refresh Interval (seconds): %s" % (REFRESH_INTERVAL))
class RedditNotifications:

    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            # set this to just PASSWORD if you don't use 2FA
            password=PASSWORD if len(KEY) == 0 else PASSWORD + ":" + totp.now(),
            user_agent="APP",
            username=USERNAME
        )

        homedir = pwd.getpwuid(os.getuid()).pw_dir
        self.datafile = os.path.join(base_dir, 'data', 'reddit_seen')

        if os.path.exists(self.datafile):
            log("Loading seen data from %s" % (self.datafile))
            self.seen = json.loads(open(self.datafile).read())
        else:
            log("No seen data found, starting fresh")
            os.makedirs(os.path.dirname(self.datafile), exist_ok=True)
            self.seen = {
                'message': {},
                'comment': {}
            }

    def main(self):
        print(self.reddit.user.me())
        user_id = self.reddit.user.me()
        log("Reddit user : %s" % (self.reddit.user.me()))
        for i in range(0, 3):
            try:
                log("Checking inbox for unread post notifications...")
                for item in self.reddit.inbox.unread():
                    if type(item) == praw.models.reddit.comment.Comment:
                        if item.id in self.seen['comment']:
                            log("Unread notification in inbox, but notification was already sent. Skipping item id %s" % (item.id))
                            continue
                        log("Unread notificat