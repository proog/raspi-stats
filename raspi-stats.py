#!/usr/bin/python

import json
import os
import subprocess
import sys
import argparse
import requests
import re
from datetime import *
from repeater import *
from util import *

cmd_args = None
collected_data = []

def check_network():
    def ping():
        try:
            output = subprocess.check_output(['ping', '-c 1', 'google.dk'], stderr=subprocess.STDOUT)

            return {
                'success': True,
                'summary': output.splitlines()[-2:]
            }
        except:
            return { 'success': False }
    def ip():
        try:
            return {
                'success': True,
                'ip': requests.get('https://api.ipify.org/?format=json').json()['ip']
            }
        except:
            return { 'success': False }

    return {
        'ping': ping(),
        'ip': ip()
    }

def check_system():
    def load():
        return dict(zip(['1min', '5min', '15min'], os.getloadavg()))
    def uptime():
        proc_uptime = '/proc/uptime'

        if not os.path.isfile(proc_uptime):
            return { 'success': False }

        with open(proc_uptime, 'r') as f:
            seconds = int(float(f.readline().split()[0]))
            
            return {
                'success': True,
                'uptime': seconds,
                'uptime_pretty': str(timedelta(seconds = seconds)) if seconds else None
            }
    def cpu_temp():
        sys_temp = '/sys/class/thermal/thermal_zone0/temp'

        if not os.path.isfile(sys_temp):
            return { 'success': False }

        with open(sys_temp, 'r') as f:
            return {
                'success': True,
                'temperature': float(f.readline()) / 1000
            }        
    def memory():
        proc_meminfo = '/proc/meminfo'

        if not os.path.isfile(proc_meminfo):
            return { 'success': False }

        with open(proc_meminfo, 'r') as f:
            lines = f.readlines()

        return {
            'success'   : True,
            'total'     : reduce(lambda previous, line: previous or re.search('^MemTotal\:\s*(\d+).*$',  line), lines, None).group(1),
            'free'      : reduce(lambda previous, line: previous or re.search('^MemFree\:\s*(\d+).*$',   line), lines, None).group(1),
            'swap_total': reduce(lambda previous, line: previous or re.search('^SwapTotal\:\s*(\d+).*$', line), lines, None).group(1),
            'swap_free' : reduce(lambda previous, line: previous or re.search('^SwapFree\:\s*(\d+).*$',  line), lines, None).group(1)
        }
    def disk_space():
        try:
            output = subprocess.check_output(['df', '-Plm'], stderr=subprocess.STDOUT)
            lines = output.splitlines()
            root_line = reduce(lambda previous, line: previous or re.search('^.*\s+(\d+)\s+\d+\s+(\d+)\s+\d+%\s+\/\s*$', line), lines, None)

            if not root_line:
                return { 'success': False }

            return {
                'success': True,
                'total': int(root_line.group(1)),
                'free': int(root_line.group(2))
            }
        except:
            return { 'success': False }

    return {
        'load_avg': load(),
        'uptime' : uptime(),
        'cpu_temp': cpu_temp(),
        'memory': memory(),
        'disk_space': disk_space()
    }

def upload():
    global cmd_args, collected_data

    def upload_filter(item):
        try:
            response = requests.post(cmd_args.url, json = item, timeout = 5)

            if response.status_code == 201:
                return False # remove from list
        except Exception as e:
            log(e.reason if 'reason' in e else e)

        return True

    total = len(collected_data)
    log('Attempting to upload %d data pack(s)...' % total)

    collected_data = filter(upload_filter, collected_data)

    log('%d of %d data packs successfully uploaded' % (total - len(collected_data), total))

def execute():
    global cmd_args, collected_data

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
    
    if(cmd_args.verbose):
        log(json.dumps(data, indent = 2))

    collected_data.append(data)
    upload()

def main():
    global cmd_args

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', type = str, default = 'http://localhost:3000/', help = 'Server to connect to')
    parser.add_argument('-i', '--interval', type = int, default = 2, help = 'Interval between executions in seconds')
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