#!/usr/bin/python

import threading
import httplib
import json
import os
import subprocess
import time
import sys
from datetime import *

class Repeater:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action

    def schedule(self):
        next = datetime.now() + timedelta(seconds=self.interval)
        log("Next execution in " + str(self.interval) + "s (" + format_time(next) + ")")

        t = threading.Timer(self.interval, self.run)
        t.daemon = True
        t.start()
        return t

    def run(self):
        log("Executing...")
        self.action()
        log("Execution finished")
        self.schedule()

def log(msg):
    print "[" + format_time(datetime.now()) + "] " + str(msg)

def format_time(datetime):
    return datetime.strftime("%Y-%m-%d %H:%M:%S")

def check_network():
    def ping():
        try:
            output = subprocess.check_output(["ping", "-c 5", "google.dk"], stderr=subprocess.STDOUT)
            success = True
            summary = output.splitlines()[-2:]
        except subprocess.CalledProcessError as e:
            success = False
            summary = e.output.splitlines()
        except Exception:
            success = False
            summary = None

        return {
            "success": success,
            "summary": summary
        }

    def ip():
        connection = httplib.HTTPSConnection("api.ipify.org")

        try:
            connection.request("GET", "/?format=json")
            response = connection.getresponse().read()
            ip_address = json.JSONDecoder().decode(response)["ip"]
            success = True
        except Exception:
            ip_address = None
            success = False

        return {
            "success": success,
            "ip": ip_address
        }

    return {
        "ping": ping(),
        "ip": ip()
    }

def upload(data):
    print "stub"

def execute():
    time_start = datetime.utcnow()
    load_avg = dict(zip([1, 5, 15], os.getloadavg()))
    network = check_network()
    time_end = datetime.utcnow()

    log(json.JSONEncoder(indent=2).encode({
        "time_start": int(time_start.strftime("%s")),
        "time_end": int(time_end.strftime("%s")),
        "time_start_pretty": format_time(time_start),
        "time_end_pretty": format_time(time_end),
        "load_avg": load_avg,
        "network": network
    }))

def main(args):
    if len(args) < 2:
        print "Missing argument specifying interval in seconds"
        sys.exit(1)

    print "\nPress enter to exit at any time\n"

    log("Scheduling...")

    repeater = Repeater(int(args[1]), execute)
    repeater.schedule()
    raw_input()

    log("Exiting...")

if __name__ == '__main__':
    main(sys.argv)