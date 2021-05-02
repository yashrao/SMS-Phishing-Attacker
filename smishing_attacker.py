import requests
from pprint import pprint
from time import sleep
from datetime import datetime
import configparser

## Disable warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
####

from twilio.rest import Client  # Twilio API
from twilio.base.exceptions import TwilioRestException

### Constants for parsing the message

URL = '{{URL}}'
FIRST_NAME = '{{FIRST_NAME}}'
LAST_NAME = '{{LAST_NAME}}'

###

### Other constants

CONFIG = 'config.ini'
COLUMN_HEADINGS='First Name,Last Name,Email,RID\n'
DEBUG = False

###

def set_debug():
    global DEBUG
    DEBUG = True

def write_log(info: str, info_type: str):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    if info_type == 'MESSAGE':
        with open('debug.log', 'a') as f:
            f.write('\n[{}]\n### BEGIN MESSAGE ###\n{}\n### END MESSAGE ###\n'.format(current_time, info))

def get_config(config_filename: str) -> dict:
    config = configparser.ConfigParser()
    config.read(config_filename)
    return config

def get_victims(gophish_api_key: str) -> dict:
    campaigns = requests.get('https://localhost:3333/api/campaigns/?api_key=' + gophish_api_key['GOPHISH_API_KEY'], verify=False)
    res = None

    try:
        res = campaigns.json()[0]['results']
    except KeyError as e:
        print('ERROR: Something has gone wrong')
        print('exiting...')
        print(campaigns.json())
        exit(1)
    except IndexError as e:
        print('ERROR: No Campaign Results found')
        print('exiting...')
        exit(1)

    with open('victims.csv', 'w') as f:
        f.write(COLUMN_HEADINGS)
        for user in res:
            f.write(user['first_name'] + ',' + user['last_name'] + ',' + user['email'] + ',' + user['id'] + '\n')

    return res

def get_phone_numbers(filepath: str) -> list:
    res = None
    try:
        with open(filepath, 'r') as f:
            res = f.readlines()
        
        tmp = []
        for number in res:
            number = number.strip() 
            if '+' not in number:
                print('ERROR: Number "{}" does not have area code +XXX'.format(number))
                exit(1)
            tmp.append(number) # Get rid of whitespace 
        res = tmp

        return res
    except FileNotFoundError as e:
        print('ERROR: Phone number list with filename "{}" not found.'.format(filepath))
        print('exiting...')
        exit(1)

    if res == []:
        print('ERROR: Phone number list is empty')
        print('exiting...')
        exit(1)

def check_input():
    user_input = input('Continue (Y/n)? ')
    if user_input == 'n':
        print('exiting...')
        exit(0)


def get_message(filepath: str) -> list:
    res = None
    try:
        with open(filepath, 'r') as f:
            res = f.read()
        
        print('Loaded Message:')
        print(res)
        print('### END MESSAGE ###\n')
        check_input()
        return res
    except FileNotFoundError as e:
        print('ERROR: Message with filename "{}" not found.'.format(filepath))
        print('exiting...')
        exit(1)

    if res == '':
        print('ERROR: Message is empty')
        print('exiting...')
        exit(1)

def create_custom_message(message: str, victim: dict, link: str) -> str:
    if link[-1] != '/':
        link = link + '/'
    url = link + '?rid=' + victim['id']
    first_name = victim['first_name']
    last_name = victim['last_name']

    message = message.replace(FIRST_NAME, first_name)
    message = message.replace(LAST_NAME, last_name)
    message = message.replace(URL, url)
    if DEBUG: 
        write_log(message, 'MESSAGE')
    return message

def send_sms(twilio_config: dict, phone_numbers: list, victims: list, message: str, link: str):
    print('Sending SMS...')
    client = Client(twilio_config['TWILIO_ACCOUNT_SID'], twilio_config['TWILIO_AUTH_TOKEN']) 
    
    for i in range(len(phone_numbers)):
        to_number = phone_numbers[i]
        custom_msg = create_custom_message(message, victims[i], link)
        twilio_send_sms(client, twilio_config['TWILIO_MSG_SERVICE_ID'], custom_msg, to_number) # TODO: UNCOMMENT
        print('Sent to {}'.format(to_number))
        sleep(1)  # Prevent spamming the Twilio server
        #print(message.sid)
    print('Sent all SMS!')

def twilio_send_sms(client, messaging_service_sid: str, custom_msg: str, to_number: str):
    try:
        message = client.messages.create(
                                       messaging_service_sid=messaging_service_sid,         \
                                       body=custom_msg,                                                    \
                                       to=to_number                                                        \
                                  )
    except TwilioRestException as e:
        print('ERROR: Twilio REST ERROR')
        raise e

def check_data_dimensions(phone_numbers, victims):
    if len(phone_numbers) != len(victims):
        print('ERROR: Number of phone numbers do not match the number of Gophish IDs')
        print('Ensure there is a phone number for each victim')
        print('Phone Number Count: {}'.format(len(phone_numbers)))
        print('Gophish ID Count: {}'.format(len(victims)))
        exit(1)

def main():
    config = get_config(CONFIG)
    if 'DEBUG' in config['SETTINGS'].keys():
        if config['SETTINGS']['DEBUG'] == 'True':
            set_debug()
            print('Debug mode on... Outputing all messages to out.log')

    victims = get_victims(config['GOPHISH'])
    phone_numbers = get_phone_numbers(config['SETTINGS']['PHONE_NUMBERS_PATH'])
    check_data_dimensions(phone_numbers, victims)
    message = get_message(config['SETTINGS']['MESSAGE_PATH'])

    send_sms(config['TWILIO'], phone_numbers, victims, message, config['SETTINGS']['GOPHISH_LANDING_PAGE_URL'])

    print('DONE!')
    exit(0)

if __name__ == '__main__':
    main()
