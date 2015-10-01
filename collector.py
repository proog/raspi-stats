import requests
import json
from datetime import datetime
from util import log, format_time, epoch_time


class Collector:
    def __init__(self, collect_fn, url, nick, name='Unnamed collector', verbose=False, dry_run=False):
        self.collect_fn = collect_fn
        self.url = url
        self.nick = nick
        self.name = name
        self.verbose = verbose
        self.dry_run = dry_run
        self.upload_queue = []

    def collect(self):
        time_start = datetime.utcnow()
        collected_data = self.collect_fn()
        time_end = datetime.utcnow()

        data = {
            'nick': self.nick,
            'time_start': epoch_time(time_start),
            'time_end': epoch_time(time_end),
            'time_start_pretty': format_time(time_start),
            'time_end_pretty': format_time(time_end),
            'data': collected_data
        }

        log('%s: Collected the following data: %s' % (self.name, json.dumps(data, indent=2)), self.verbose)

        self.upload_queue.append(data)
        self.upload()

    def upload(self):
        def upload_filter(item):
            try:
                response = requests.post(self.url, json=item, timeout=5)

                if response.status_code == 201:
                    return False  # remove from list
            except Exception as e:
                log(e, self.verbose)

            return True

        total = len(self.upload_queue)
        log('%s: Attempting to upload %d data pack(s)...' % (self.name, total), self.verbose)

        if self.dry_run:
            self.upload_queue = []
            log('%s: Dry run, skipping upload of %d data pack(s)' % (self.name, total))
        else:
            self.upload_queue = filter(upload_filter, self.upload_queue)
            log('%s: %d of %d data pack(s) successfully uploaded' % (self.name, total - len(self.upload_queue), total))
