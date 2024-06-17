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
                        log("Unread notification in inbox, item id %s" % (item.id) + " sending notification to Home Assistant")
                        self.ha_handle_comment(item)

                    elif type(item) == praw.models.reddit.message.Message or type(item) == praw.models.reddit.message.SubredditMessage:
                        if item.id in self.seen['message']:
                            log("Unread message in inbox, but notification was already sent. Skipping item id %s" % (item.id))
                            continue

                        self.ha_handle_message(item)
                    else:
                        raise Exception("unknown item type: %s" % (type(item)))
                break
            except prawcore.exceptions.OAuthException:
                time.sleep(1)


    def ha_send_notification(self, title, message, action_url):
        url = HA_URL
        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json",
        }

        data = {
            "message": f"{message}",
            "title": f"{title}",
            "data": {
                "image": f"{APOLLO_ICON_URL}",
                "url": f"{action_url}"
            }
        }

        response = post(url, headers=headers, json=data)
        # Print the response text for debugging purposes
        print(response.text)


    def ha_handle_comment(self, item):
        action_url = 'apollo://reddit.com' + item.context
        
        log("Found new comment notification in inbox, sending to Home Assistant")
        subject = "New Comment: " + item.submission.title
        self.ha_send_notification(subject, item.body, action_url)

        log("Notification sent to Home Assistant")
        self.seen['comment'][item.id] = 1
        self.save()



    def ha_handle_message(self, item):
        action_url = 'apollo://reddit.com/message/messages/' + item.id


        log("Found new message notification in inbox, sending to Home Assistant")
        subject = "New Message: " + item.subject
        self.ha_send_notification(subject, item.body, action_url)
        log("Message notification sent to Home Assistant")

        self.seen['message'][item.id] = 1
        self.save()


    def save(self):
        with open(self.datafile + '.new','w') as f:
            f.write(json.dumps(self.seen,indent=4))

        os.rename(self.datafile + '.new', self.datafile)
        log("Saved seen data to %s" % (self.datafile))


while True:
    r = RedditNotifications()
    r.main()
    #Wait the number of seconds specified in the REFRESH_INTERVAL environment variable before checking for new messages again
    time.sleep(int(REFRESH_INTERVAL))
