# SMS Phishing Attacker

## Prerequisites
* Used Gophish and understand how to launch campaigns
* Have Twilio API Key and Secret
* Have ready a list of Phone Numbers **with the correct area code** for every victim user that is inputted in Gophish (**Order of users in Gophish should be the same as the phone number list or else the numbers will send to the wrong people**)

## Installation
The program is very easy to setup, to get the program simply follow these steps:

First clone the repo and cd into the directory
```
git clone https://github.com/yashrao/SMS-Phishing-Attacker
cd SMS-Phishing-Attacker
```

Then it's recommended but not mandatory to set up a Python virtualenv, you can do this by simply running the following:
```
python3 -m venv venv # Optional but recommended
source venv/bin/activate # Optional but recommended
```

Then finally for the dependencies:
```
pip3 install -r requirements.txt
```

TLDR; Run these commands:
```
git clone https://github.com/yashrao/SMS-Phishing-Attacker
cd SMS-Phishing-Attacker
python3 -m venv venv
source venv/bin/activate
source venv/bin/activate
```

## Getting Started
The first thing you need to do is change the `config.ini` file. Provided in this repo is a `sample_config.ini`, rename this to `config.ini` and replace the keys with your own:
* GOPHISH_API_KEY: API key found in Gophish settings
* GOPHISH_LANDING_PAGE_URL: This is setup by you and the URL is found in the config.json of the Gophish directory
* TWILIO_ACCOUNT_SID: Twilio account ID found in Twilio dashboard
* TWILIO_AUTH_TOKEN: Twilio AUTH token found in Twilio dashboard
* TWILIO_MSG_SERVICE_ID: Twilio Message Service ID found in Twilio Dashborad

You may also enable DEBUG mode by setting it to True if you want to save the messages being sent. These messages will be saved in a debug.log file.

PREVIEW_ONLY, if set to True, will not send the SMS but simply preview the first message that will be send with all the variables replaced with their respective values. Useful to test out before sending out any messages just to make sure things are fully prepared.

You also must create a **Message file** (default path: message.txt), this is the message that will be sent via SMS.
```
Dear {{FIRST_NAME}},

This is a test message for {{LAST_NAME}}.

Please click the link in this message: {{URL}}.
```
Here you can use the following variables that will be replaced by the user information from Gophish.
* {{FIRST_NAME}}: for the first name of each Gophish victim
* {{LAST_NAME}}: for the last name of each Gophish victim
* {{URL}}: landing page URL with the **Gophish Tracking ID for each user**

Additional variables are as followed:
* {{FIRST_NAME_LOWER}}: for a lowercase version of first name
* {{LAST_NAME_LOWER}}: for a lowercase version of last name
* {{TODAY_DATE_FORMAT}}: today's date format in strftime format (NOTE: you must add an extra '%' sign for each '%' sign present for the config.ini file)

## Setting up Gophish
* Make sure to create a group of users either manually or import a CSV into Gophish, the email for each user does not matter and can be anything as the goal is not to send emails but SMS messages only.
* Make sure the landing page is setup and that it is accessible to outside users.

## Launching the Campaign
Once everything is setup, while creating the campaign **make sure you select the correct user group that corresponds with the phone number list you have prepared or else it will send the messages with the wrong information to the wrong people**.

Finally you can launch the campaign for Gophish, if you've inputted fake/invalid emails for the users you might have to wait for the campaign screen to error out before sending the SMS otherwise it will clear any existing data. Once you see ERROR on all the emails then you can begin SMS phishing.

Once that is all done, you can begin the SMS Phishing by running:
```
python3 smishing_attacker.py
```

You will see a preview of the message to be sent and simply hit "n" to cancel or any key to continue and the SMS Phishing will have started.

**NOTE:** For the time being, make sure there is only one campaign in Gophish as this hasn't been tested with more than one.
