#!/usr/bin/python

import os
import subprocess
import argparse
import requests
import re
import urlparse
from collector import Collector
from repeater import Repeater
from util import *

cmd_args = None
fail_data = {'success': False}


def check_network():
    global cmd_args
    def ping():
        try:
            lines = subprocess.check_output(['ping', '-c 10', 'google.com'], stderr=subprocess.STDOUT).splitlines()

            packet_loss = float(re.search('^.* (\d+(?:\.\d+)?)% packet loss.*$', lines[-2]).group(1))
            roundtrip_regex = re.search('^.* (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+) ms.*$', lines[-1])
            roundtrip_min = float(roundtrip_regex.group(1))
            roundtrip_avg = float(roundtrip_regex.group(2))
            roundtrip_max = float(roundtrip_regex.group(3))

            return {
                'success': True,
                'packet_loss': packet_loss,
                'roundtrip_min': roundtrip_min,
                'roundtrip_avg': roundtrip_avg,
                'roundtrip_max': roundtrip_max
            }
        except Exception as e:
            log(e, cmd_args.verbose)
            return fail_data

    def ip():
        try:
            return {
                'success': True,
                'ip': requests.get('https://api.ipify.org/?format=json').json()['ip']
            }
        except Exception as e:
            log(e, cmd_args.verbose)
            return fail_data

    def speed():
        try:
            url = urlparse.urljoin(cmd_args.url, '/speedtest')
            tstart = datetime.utcnow()
            response = requests.get(url)
            tend = datetime.utcnow()
            length = len(response.content)
            seconds = (tend - tstart).total_seconds()

            return {
                'success': True,
                'bytes': length,
                'seconds': round(seconds, 2),
                'mbps': round((length / 1024 / 1024 * 8) / seconds, 2)
            }
        except Exception as e:
            log(e, cmd_args.verbose)
            return fail_data

    return {
        'ping': ping(),
        'ip': ip(),
        'speed': speed()
    }


def check_system():
    global cmd_args
    def load():
        return dict(zip(['1min', '5min', '15min'], map(lambda x: round(x, 2), os.getloadavg())))

    def uptime():
        proc_uptime = '/proc/uptime'

        if not os.path.isfile(proc_uptime):
            return fail_data

        with open(proc_uptime, 'r') as f:
            seconds = int(float(f.readline().split()[0]))

            return {
                'success': True,
                'uptime': seconds,
                'uptime_pretty': str(timedelta(seconds=seconds)) if seconds else None
            }

    def cpu_temp():
        sys_temp = '/sys/class/thermal/thermal_zone0/temp'

        if not os.path.isfile(sys_temp):
            return fail_data

        with open(sys_temp, 'r') as f:
            return {
                'success': True,
                'temperature': round(float(f.readline()) / 1000, 2)
            }

    def memory():
        proc_meminfo = '/proc/meminfo'

        if not os.path.isfile(proc_meminfo):
            return fail_data

        with open(proc_meminfo, 'r') as f:
            lines = f.readlines()

        regex_total = '^MemTotal\:\s*(\d+).*$'
        regex_free = '^MemFree\:\s*(\d+).*$'
        regex_swap_total = '^SwapTotal\:\s*(\d+).*$'
        regex_swap_free = '^SwapFree\:\s*(\d+).*$'
        reduce_fn = lambda expression: lambda previous, line: previous or re.search(expression, line)

        return {
            'success': True,
            'total': int(reduce(reduce_fn(regex_total), lines, None).group(1)),
            'free': int(reduce(reduce_fn(regex_free), lines, None).group(1)),
            'swap_total': int(reduce(reduce_fn(regex_swap_total), lines, None).group(1)),
            'swap_free': int(reduce(reduce_fn(regex_swap_free), lines, None).group(1))
        }

    def disk_space():
        try:
            output = subprocess.check_output(['df', '-Plm'], stderr=subprocess.STDOUT)
            lines = output.splitlines()
            root_line = reduce(
                lambda previous, line: previous or re.search('^.*\s+(\d+)\s+\d+\s+(\d+)\s+\d+%\s+/\s*$', line), lines,
                None)

            if not root_line:
                return fail_data

            return {
                'success': True,
                'total': int(root_line.group(1)),
                'free': int(root_line.group(2))
            }
        except Exception as e:
            log(e, cmd_args.verbose)
            return fail_data

    return {
        'load_avg': load(),
        'uptime': uptime(),
        'cpu_temp': cpu_temp(),
        'memory': memory(),
        'disk_space': disk_space()
    }


def main():
    global cmd_args

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', type=str, default='http://localhost:3000/', help='Server to upload data to and use for speed tests')
    parser.add_argument('-i', '--interval', type=int, default=600, help='Interval (in seconds) between system checks')
    parser.add_argument('-n', '--network-interval', type=int, default=3600, help='Interval (in seconds) between network checks')
    parser.add_argument('--verbose', action='store_true', help='More log messages, including collected data')
    parser.add_argument('--dry-run', action='store_true', help='Do not upload collected data')
    parser.add_argument('nick', type=str, help='Unique nickname to associate collected data with')
    cmd_args = parser.parse_args()

    print '\n-- Press enter or ctrl-c to exit --\n'

    log('Scheduling...', cmd_args.verbose)

    upload_url = urlparse.urljoin(cmd_args.url, '/stats')
    system_collector = Collector(check_system, upload_url, cmd_args.nick, 'System collector', cmd_args.verbose, cmd_args.dry_run)
    network_collector = Collector(check_network, upload_url, cmd_args.nick, 'Network collector', cmd_args.verbose, cmd_args.dry_run)

    Repeater(cmd_args.interval, system_collector.collect, 'System repeater', cmd_args.verbose).run()
    Repeater(cmd_args.network_interval, network_collector.collect, 'Network repeater', cmd_args.verbose).run()

    raw_input()

    log('Exiting...', cmd_args.verbose)


if __name__ == '__main__':
    main()
