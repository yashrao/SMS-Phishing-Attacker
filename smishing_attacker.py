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
TODAY_DATE_FORMAT = '{{TODAY_DATE}}'
FIRST_NAME_LOWER = '{{FIRST_NAME_LOWER}}'
LAST_NAME_LOWER = '{{LAST_NAME_LOWER}}'

###

### Other constants

CONFIG = 'config.ini'
COLUMN_HEADINGS='First Name,Last Name,Email,RID\n'

###

### GLOBALS
DEBUG = False
PREVIEW_ONLY = False
NO_NUMBERS_TXT = False
MASK = False 
MASK_CHARACTER = None
DELAY = 30

FIRST_FULL_NAME = False
FULL_NAME_PATTERN = {}
###

def set_first_full_name(pattern: str, is_triple: bool, triple_pattern=None):
    if pattern == 'None':
        print('ERROR: Pattern Enabled but no pattern specified in config.ini')
        print('exiting...')
    global FIRST_FULL_NAME
    FIRST_FULL_NAME = True

    pattern = pattern.split(',')
    
    try:
        first_name_index = pattern.index('FIRST_NAME')
        last_name_index = pattern.index('LAST_NAME')
        global FULL_NAME_PATTERN
        FULL_NAME_PATTERN['FIRST_NAME'] = first_name_index
        FULL_NAME_PATTERN['LAST_NAME'] = last_name_index
        if is_triple:
            if triple_pattern == None:
                print('ERROR: Triple enabled but no TRIPLE_PATTERN present in config.ini...')
                print('exiting...')
                exit(1)
            triple_pattern = triple_pattern.split(',')       
            FULL_NAME_PATTERN['TRIPLE'] = {
                    'FIRST_NAME': triple_pattern.index('FIRST_NAME'), 
                    'LAST_NAME': triple_pattern.index('LAST_NAME'), 
                    'MIDDLE_NAME': triple_pattern.index('MIDDLE_NAME'), 
                    }
    except ValueError as e:
        print('ERROR: Please make sure FIRST_NAME, LAST_NAME and if a triple pattern is present MIDDLE_NAME are all in the pattern when configuring config.ini')
        raise e
    print('FIRST_FULL_NAME ENABLED SHOWING PATTERN')
    print(FULL_NAME_PATTERN)

def set_debug():
    global DEBUG
    DEBUG = True

def set_preview_only():
    global PREVIEW_ONLY
    PREVIEW_ONLY = True

def set_no_numbers_txt():
    global NO_NUMBERS_TXT
    NO_NUMBERS_TXT = True

def set_mask():
    global MASK
    MASK = True

def set_mask_character(character: str):
    global MASK_CHARACTER
    MASK_CHARACTER = character

def write_log(info: str, info_type: str):
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    if info_type == 'MESSAGE':
        with open('debug.log', 'a') as f:
            f.write('\n[{}]\n### BEGIN MESSAGE ###\n{}\n### END MESSAGE ###\n'.format(current_time, info))

def set_delay(delay: int):
    global DELAY
    DELAY = delay

def get_config(config_filename: str) -> dict:
    config = configparser.ConfigParser()
    config.read(config_filename)
    return config

def get_campaign_index(campaigns: dict):
    ## ID | NAME
    ## _________
    ##    | 
    print('####### BEGIN CAMPAIGN OPTIONS #######')
    campaigns = campaigns.json()
    res = {}
    index = 0
    for campaign in campaigns:
        res[campaign['id']] = (index, campaign['name'])
        print('{}:{}'.format(campaign['id'], campaign['name']))
        index += 1

    print('#####################################\n')
    return res

def get_victims_no_gophish(filepath: str):
    res = None
    with open(filepath, 'r') as f:
        users = f.readlines()

    # id, first_name, last_name
    heading = users[0].split(',') # CSV headings
    users = users[1:]
    first_name_index = heading.index('first_name')
    id_index = heading.index('id')
    last_name_index = heading.index('last_name')

    res = []

    for user in users:
        user = user.split(',')
        victim = {}
        victim['id'] = user[id_index]
        victim['first_name'] = user[first_name_index]
        victim['last_name'] = user[last_name_index]
        res.append(victim)

    return res

def get_victims(gophish_settings: str) -> dict:
    campaign_id = gophish_settings['CAMPAIGN_ID']
    campaigns = requests.get('https://localhost:3333/api/campaigns/?api_key=' + gophish_settings['GOPHISH_API_KEY'], verify=False)
    res = None
    
    campaign_index = get_campaign_index(campaigns)
    try:
        campaign_id = int(campaign_id)
    except ValueError as e:
        print('No campaign ID specified... Displaying')
        print('\nPlease select a Campaign ID and update the config.ini file\n')
        print('exiting...')
        exit(1)

    try:
        res = campaigns.json()[campaign_index[campaign_id][0]]['results']
    except KeyError as e:
        print('ERROR: Campaign index not found')
        print('exiting...')
        exit(1)
    except IndexError as e:
        #raise e ## TODO: change this
        print('ERROR: No Campaign Results found')
        print('exiting...')
        exit(1)

    with open('victims.csv', 'w') as f:
        print('Found Users... Check victims.csv')
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
    if PREVIEW_ONLY:
        preview_msg = '[Preview Only]'
    else:
        preview_msg = '[WARNING: Sending Real SMS]'

    user_input = input('Continue (Y/n)? {} (Delay: {}): '.format(preview_msg, DELAY))
    if user_input == 'n':
        print('exiting...')
        exit(0)

# Create list of phone numbers by grabbing them from each user's "last name"
def create_phone_number_list(victims: dict) -> list:
    res = []
    for victim in victims:
        res.append(victim['last_name'])
    return res

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

def create_custom_message(message: str, victim: dict, link: str, date_format: str) -> str:
    if link[-1] != '/':
        link = link + '/'
    url = link + '?rid=' + victim['id']
    first_name = victim['first_name']
    if not FIRST_FULL_NAME:
        last_name = victim['last_name']
    else:
        ## If there is a special pattern when using full name in first name 
        full_name = first_name.split(' ')
        print(full_name)
        last_name = ''
        if len(full_name) == 2:
            first_name = full_name[FULL_NAME_PATTERN['FIRST_NAME']]
            last_name = full_name[FULL_NAME_PATTERN['LAST_NAME']]
            first_name = first_name + last_name # combine to get fullname
        elif len(full_name) == 3:
            #TODO:
            print(FULL_NAME_PATTERN)
            full_name = {
                    'FIRST_NAME': full_name[0],
                    'MIDDLE_NAME': full_name[1],
                    'LAST_NAME': full_name[2]
                    }
            #first_name = full_name[FULL_NAME_PATTERN]['TRIPLE']
            #first_name_index = full_name[FULL_NAME_PATTERN['TRIPLE']['FIRST_NAME']]
            #middle_name_index = full_name[FULL_NAME_PATTERN['TRIPLE']['MIDDLE_NAME']]
            #last_name_index = full_name[FULL_NAME_PATTERN['TRIPLE']['LAST_NAME']]
            first_name_index = FULL_NAME_PATTERN['TRIPLE']['FIRST_NAME']
            middle_name_index = FULL_NAME_PATTERN['TRIPLE']['MIDDLE_NAME']
            last_name_index = FULL_NAME_PATTERN['TRIPLE']['LAST_NAME']

            res = ['', '', '',]
            res[first_name_index] = full_name['FIRST_NAME']
            res[middle_name_index] = full_name['MIDDLE_NAME']
            res[last_name_index] = full_name['LAST_NAME']

            first_name = ''.join(res)
            #first_name = full_name[0]
            #middle_name = full_name[1]
            #last_name = full_name[2]
            #first_name = first_name + last_name # combine to get fullname

    if MASK:
        if len(first_name) > 2:
            mask = len(first_name[2:]) * MASK_CHARACTER
            first_name = first_name[0:2] + mask
        else:
            first_name = len(first_name) * MASK_CHARACTER
    message = message.replace(FIRST_NAME, first_name)
    if not NO_NUMBERS_TXT:
        message = message.replace(LAST_NAME, last_name)
    message = message.replace(FIRST_NAME_LOWER, first_name.lower())
    message = message.replace(LAST_NAME_LOWER, last_name.lower())
    message = message.replace(TODAY_DATE_FORMAT, datetime.now().strftime(date_format)) #TODO: Add support for custom date
    message = message.replace(URL, url)
    if DEBUG: 
        write_log(message, 'MESSAGE')
    if PREVIEW_ONLY:
        print('\n\n ~~~~~~ PRINTING PREVIEW MESSAGE ~~~~~~\n\n')
        print(message)
    return message

def send_sms(twilio_config: dict, phone_numbers: list, victims: list, message: str, link: str, date_format: str):
    print('Sending SMS...')
    client = Client(twilio_config['TWILIO_ACCOUNT_SID'], twilio_config['TWILIO_AUTH_TOKEN']) 
    
    for i in range(len(phone_numbers)):
        to_number = phone_numbers[i]
        custom_msg = create_custom_message(message, victims[i], link, date_format)
        if PREVIEW_ONLY:
            print('[PREVIEW] Sent to {}'.format(to_number))
        else:
            twilio_send_sms(client, twilio_config['TWILIO_MSG_SERVICE_ID'], custom_msg, to_number)
            print('Sent to {}'.format(to_number))
        sleep(DELAY)  # Prevent spamming the Twilio server
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

def set_configuration(config):
    #TODO: PUT THIS IN A SEPERATE FUNCTION
    if 'DEBUG' in config['SETTINGS'].keys():
        if config['SETTINGS']['DEBUG'] == 'True':
            set_debug()
            print('DEBUG mode on... Outputing all SMS messages to out.log')
    if 'PREVIEW_ONLY' in config['SETTINGS'].keys():
        if config['SETTINGS']['PREVIEW_ONLY'] == 'True':
            set_preview_only()
            print('PREVIEW ONLY mode on... will not send any messages')
    if 'NO_NUMBERS_TXT' in config['SETTINGS'].keys():
        if config['SETTINGS']['NO_NUMBERS_TXT'] == 'True':
            set_no_numbers_txt()  #TODO: might not even need a global tbh, can just put a local variable in main()
            print('NO NUMBERS.TXT mode on... will not use numbers.txt and will instead use the "Last Name" field from Gophish for phone numbers')
    if 'ENABLED' in config['MASK'].keys():
        if config['MASK']['ENABLED'] == 'True':
            set_mask()
            set_mask_character(config['MASK']['MASK_CHARACTER'])
            print('MASK ENABLED... Will mask all first names when sending SMS messages')
    if 'ENABLED' in config['FIRST_FULL_NAME'].keys():
        if config['FIRST_FULL_NAME']['ENABLED'] == 'True':
            is_triple = False
            triple_pattern = None
            if config['FIRST_FULL_NAME']['TRIPLE_PATTERN'] != 'None':
                is_triple = True
                triple_pattern = config['FIRST_FULL_NAME']['TRIPLE_PATTERN']
            set_first_full_name(config['FIRST_FULL_NAME']['PATTERN'], is_triple, triple_pattern)
    if 'DELAY' in config['SETTINGS'].keys():
        if config['SETTINGS']['DELAY'] != 'None':
            try:
                print('SETTING DELAY TO {}'.format(config['SETTINGS']['DELAY']))
                set_delay(int(config['SETTINGS']['DELAY']))
            except ValueError as e:
                print('ERROR: invalid delay value, please input an integer')
                print('exiting...')
                exit(1)

def main():
    print('')
    config = get_config(CONFIG)
    set_configuration(config)
    print('')
    if 'ENABLED' in config['GOPHISH'].keys():
        if config['GOPHISH']['ENABLED'] == 'True':
            victims = get_victims(config['GOPHISH'])
        else:
            victims = get_victims_no_gophish(config['GOPHISH']['CSV_FILEPATH'])
    else:
        victims = get_victims(config['GOPHISH'])
    if not NO_NUMBERS_TXT:
        phone_numbers = get_phone_numbers(config['SETTINGS']['PHONE_NUMBERS_PATH'])
    else:
        phone_numbers = create_phone_number_list(victims)
    check_data_dimensions(phone_numbers, victims)
    message = get_message(config['SETTINGS']['MESSAGE_PATH'])

    send_sms(config['TWILIO'], phone_numbers, victims, message, config['SETTINGS']['GOPHISH_LANDING_PAGE_URL'], config['SETTINGS']['DATE'])

    print('DONE!')
    exit(0)

if __name__ == '__main__':
    main()
