import json
import os
import requests
import sys
from pathlib import Path

VALIDATION_TOKEN = os.environ["CERTBOT_VALIDATION"]
BASE_DIR = "/etc/collab"

class CollabClient(object):
    def __init__(self, base_dir):
        # print ("in init")
        self.base_dir = base_dir

    def update_txt_record(self, txt):
        # print ("I've been called and the token is " + txt) 

        # If the intermediate file is there then we've already done one challenge so this is the second
        if os.path.isfile(self.base_dir + "/collab.json-int"):
            # print ("Second call, creating config file")
            contents = Path (self.base_dir + "/collab.json-int").read_text()
            contents = contents.replace ("CHALLENGE2", txt)
            f = open (self.base_dir + "/collab.json", "w")
            f.write (contents)
            f.close()
            os.remove (self.base_dir + "/collab.json-int")
            os.system ("service collab restart")
        else:   
            # print ("First call, creating intermediate")
            contents = Path (self.base_dir + "/collab.json-template").read_text()
            contents = contents.replace ("CHALLENGE1", txt)
            f = open (self.base_dir + "/collab.json-int", "w")
            f.write (contents)
            f.close()

if __name__ == "__main__":
    # Init
    client = CollabClient(BASE_DIR)

    # Update the TXT record 
    client.update_txt_record(VALIDATION_TOKEN)
