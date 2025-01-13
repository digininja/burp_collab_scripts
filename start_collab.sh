#!/usr/bin/env bash

java -jar /opt/burp/burpsuite_pro.jar --collaborator-server  --collaborator-config=/etc/collab/collab.json | tee /var/log/collab/collab.log
