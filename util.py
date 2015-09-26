from datetime import *

def log(msg):
    print '[%s] %s' % (format_time(datetime.now()), str(msg))

def format_time(datetime):
    return datetime.strftime('%Y-%m-%d %H:%M:%S')