from datetime import *


def log(msg, condition=True):
    if condition:
        print '[%s] %s' % (format_time(datetime.now()), str(msg))


def format_time(date_time):
    return date_time.strftime('%Y-%m-%d %H:%M:%S')

def epoch_time(date_time):
    return int((date_time - datetime.utcfromtimestamp(0)).total_seconds())
