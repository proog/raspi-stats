#!/usr/bin/python

import json
import os
import subprocess
import sys
import argparse
import requests
from datetime import *
from repeater import *
from util import *

cmd_args = None
execution_count = 0
collected_data = []

def check_network():
    def ping():
        try:
            output = subprocess.check_output(['ping', '-c 1', 'google.dk'], stderr=subprocess.STDOUT)
            success = True
            summary = output.splitlines()[-2:]
        except subprocess.CalledProcessError as e:
            success = False
            summary = e.output.splitlines()
        except:
            success = False
            summary = None

        return {
            'success': success,
            'summary': summary
        }

    def ip():
        try:
            ip_address = requests.get('https://api.ipify.org/?format=json').json()['ip']
            success = True
        except:
            ip_address = None
            success = False

        return {
            'success': success,
            'ip': ip_address
        }

    return {
        'ping': ping(),
        'ip': ip()
    }

def check_system():
    def load():
        return dict(zip(['1min', '5min', '15min'], os.getloadavg()))
    def uptime():
        try:
            with open('/proc/uptime', 'r') as f:
                seconds = float(f.readline().split()[0])
                success = True
        except:
            seconds = None
            success = False

        return {
            'success': success,
            'uptime': int(seconds) if seconds else None,
            'uptime_pretty': str(timedelta(seconds = seconds)) if seconds else None
        }

    return {
        'load_avg': load(),
        'uptime' : uptime()
    }

def upload():
    global cmd_args, collected_data
    unsent = []

    log('Attempting to upload %d data pack(s)...' % len(collected_data))

    for item in collected_data:
        try:
            response = requests.post(cmd_args.url, json = item, timeout = 5)
            if response.status_code != 201:
                raise requests.exceptions.HTTPError('Wrong status code: %d' % response.status_code)
        except Exception as e:
            log(e.reason if 'reason' in e else e)
            unsent.append(item)

    log('%d of %d data packs successfully uploaded' % (len(collected_data) - len(unsent), len(collected_data)))
    collected_data = unsent

def execute():
    global execution_count, cmd_args, collected_data

    time_start = datetime.utcnow()
    system = check_system()
    network = check_network()
    time_end = datetime.utcnow()

    data = {
        'nick': cmd_args.nick,
        'time_start': int(time_start.strftime('%s')),
        'time_end': int(time_end.strftime('%s')),
        'time_start_pretty': format_time(time_start),
        'time_end_pretty': format_time(time_end),
        'system': system,
        'network': network
    }

    collected_data.append(data)
    execution_count += 1

    if(cmd_args.verbose):
        log(json.dumps(data, indent = 2))

    if len(collected_data) > 0 and execution_count % cmd_args.upload_every == 0:
        upload()

def main():
    global cmd_args

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', type = str, default = 'http://lololololol.bike.camera:3000/', help = 'Server to connect to')
    parser.add_argument('-i', '--interval', type = int, default = 2, help = 'Interval between executions in seconds')
    parser.add_argument('-j', '--upload', dest = 'upload_every', type = int, default = 1, help = 'Every n executions will trigger upload of collected data')
    parser.add_argument('-v', '--verbose', action = 'store_true', help = 'Log collected data to console')
    parser.add_argument('nick', type = str, help = 'Unique nickname to associate collected data with')
    cmd_args = parser.parse_args()

    print '\n-- Press enter to exit at any time --\n'

    log('Scheduling...')

    Repeater(cmd_args.interval, execute, 'Task').schedule()
    raw_input()

    log('Exiting...')

if __name__ == '__main__':
    main()