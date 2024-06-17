
# apollo-notifications-homeassistant

A fork of [apollo-notifications](https://github.com/m4rkw/apollo-notifications) modifed to send notifications via Home Assistant.

A python script polls the reddit API to get new messages and sends notifications via the Home Assistant API. 

The notifications are formatted for iOS and will automatically open the content in the Apollo App directly from the lockscreen/notification center, no "Open In Apollo" prompt needed.



# Docker (Recommended)

Run ``docker-compose build`` to create the image then ``docker-compose up -d`` to start the container. 

The network mode is set to bridge by default. If you're running Home Assistant in a container you can join this container to a network with access to the Home Assistant container.



# Standalone Non-Docker Install

### Install dependencies

````
pip3 install -r requirements.txt
````
### Run script

````
python3 ./notify.py
````



# Configuration

1. Create a "personal use script" app at https://old.reddit.com/prefs/apps/ make note of the client id/secret

2. Create a Long-Lived Access Tokens in Home Assistant.

[![Open Home Assistant User Profile](https://my.home-assistant.io/badges/profile.svg)](https://my.home-assistant.io/redirect/profile/)

3. Edit ``notify.config`` in the config folder. 

You will need to provide the following:

* Reddit client ID/secret
* Reddit username/password
    * This is needed to obtain a refresh token from Reddit. In a future build I'd like to add OAuth support to avoid the password requirement.
    * If you are using two-factor authentication on your account you will need to provide the TOTP secret key (seed), this allows the script to generate the 2FA token needed to login. This will likely require you to re-enroll in 2FA, making note of the secret key shown.
* Home Assistant URL, I recommend providing the local IP/hostname for you instance. Ex: ``http://homeassistant.local:8123`` or ``http://192.168.1.4:8123``
* The Home Assistant id of the device you would like to send notifications to. You can find this by searching for mobile_app in the services section of developer tools in Home Assistant. Do not include the ``notify.`` prefix in your value.

[![Open Home Assistant Services](https://my.home-assistant.io/badges/developer_services.svg)](https://my.home-assistant.io/redirect/developer_services/)
* Optional: Icon URL. I've provided one uploaded to GitHub, this should be a URL that is publicly accessible by your iOS device. 
* Time in seconds the script should wait before checking for notification again. I believe the Reddit API is limited to 100 request a minute. The default value is 5 minutes.


# Conclusion 

The script current supports one Reddit account per instance. I'd like to expand this in the future but would need to find a way in the ``apollo://`` URI schema to switch to the right user for the notification. 

If you have any issues or comments feel free to open an issue, I'm happy to help where I can.

Special thanks to m4rkw for their work on [apollo-notifications](https://github.com/m4rkw/apollo-notifications) for the groundwork and provided the inspiration for this project. 