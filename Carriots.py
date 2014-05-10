#!/usr/env/python

from __future__ import division, print_function

## Import General Tools
import os
import glob
import time
import datetime
import subprocess
import re

import urllib2
import time, datetime
import json


##-------------------------------------------------------------------------
## Carriots Client
##-------------------------------------------------------------------------
class Client(object):
    api_url = "http://api.carriots.com/streams"

    def __init__ (self, device_id = None, api_key = None, client_type = 'json'):
        self.client_type = client_type
        self.device_id = device_id
        self.api_key = api_key
        self.content_type = "application/vnd.carriots.api.v2+%s" % (self.client_type)
        self.headers = {'User-Agent': 'Raspberry-Carriots',
                        'Content-Type': self.content_type,
                        'Accept': self.content_type,
                        'Carriots.apikey': self.api_key}

    def send (self, data):
        self.data = json.dumps(data)
        request = urllib2.Request(Client.api_url, self.data, self.headers)
        self.response = urllib2.urlopen(request)
        return self.response

    def upload(self, data):
        carriots_data = {"protocol":"v2",
                         "device":self.device_id,
                         "at":int(time.mktime(datetime.datetime.utcnow().timetuple())),
                         "data":data,
                        }
        try:
            carriots_response=self.send(carriots_data)
        except:
            print('  Failed to upload to carriots.')
            raise

    def read_api_key_from_file(self, file=None):
        if not file:
            file = os.path.join(os.path.expandvars('$HOME'), '.carriots_api')
        try:
            apikeyFO = open(file, 'r')
            contents = apikeyFO.read()
            HasEndLine = re.match('(.*)\n', contents)
            if HasEndLine:
                self.api_key = HasEndLine.group(1)
            else:
                self.api_key = contents
            self.headers = {'User-Agent': 'Raspberry-Carriots',
                            'Content-Type': self.content_type,
                            'Accept': self.content_type,
                            'Carriots.apikey': self.api_key}
            apikeyFO.close()
        except:
            print('Could not read api key from file.')




##-------------------------------------------------------------------------
## Main Program (sample usage)
##-------------------------------------------------------------------------
def main():
    Device = Client(device_id="defaultDevice@joshwalawender")
    Device.read_api_key_from_file()
    Device.upload(1.234)


if __name__ == '__main__':
    main()
