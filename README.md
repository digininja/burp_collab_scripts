# Burp Collaborator Scripts

## Start Scripts

Rather than have to start and stop Collaborator by hand, I've created a start script and a systemd service file to make the process a lot easier and to fit with standard Linux services.

Because these files can be called from anywhere, I've put my config file at `/etc/collab/collab.json` and specify its location in the start script. There may be a better way to do this, but it work.

To use these two scripts, copy the files into these locations:

* `collab.service` -> `/etc/systemd/system/multi-user.target.wants/collab.service`
* `start_collab.sh` -> `/usr/local/bin/start_collab.sh`

You then need to tell systemd that there is a new service for it to manage:

```
systemctl daemon-reload
```

And now you can enable and start the service:

```
sudo systemctl enable collab.service
sudo systemctl start collab.service
```

You can now manage the service like any other Linux service with either `systemctl` or `service`:

```
root@collab:/etc/letsencrypt# service collab status
● collab.service - Burp Collab Server
     Loaded: loaded (/etc/systemd/system/collab.service; enabled; preset: enabled)
     Active: active (running) since Mon 2025-01-13 10:33:08 GMT; 1h 6min ago
   Main PID: 483 (bash)
      Tasks: 36 (limit: 2315)
     Memory: 143.1M
        CPU: 16.316s
     CGroup: /system.slice/collab.service
             ├─483 bash /usr/local/bin/start_collab.sh
             ├─496 java -jar /opt/burp/burpsuite_pro.jar --collaborator-server --collaborator-config=/etc/collab/collab.json
             └─497 tee /var/log/collab/collab.log
```

The start script uses `tee` to push the log entries out to `/var/log/collab/collab.log`.

To stop this file getting too big, I have the `collab_logrotate` in `/etc/logrotate.d/` and that rotates the file every night.

## ACME Certbot Hook

*Warning, this script works for me but has not been tested beyond my server, use it at your own risk.*

This script is my attempt to automate renewing my Burp Collaborator certificate with Let's Encrypt. I'm using DNS TXT records which Collaborator itself is serving so the script takes the tokens passed by Let's Encrypt, updates the Collaborator config file, restarts it, then tells certbot to go ahead and do the renewal.

For this script to work, you need to have already setup Collaborator and have running a TLS server, there are plenty of guides for this, including the official one from [PortSwigger](https://portswigger.net/burp/documentation/collaborator/server/private).

I have two entries that need to go into the certificate, one for the domain itself, and one for a wildcard certificate for the domain, this requires two custom DNS records. From what I've been able to understand from the certbot process, the bot requests a challenge from LE and then calls the hook script with that challenge, the script has to then do something with the challenge, in our case update the config file, and then return control to certbot. It then requests the second challenge and passes that to the script which updates the config for a second time. Once both challenges are in place, Collaborator needs to be restarted for the changes to take affect. After all of this, we can return control to certbot and let it tell LE we are ready to respond.

Because of this two step process of updating the config file, I've chosen to start with a template config file based on my working file, copy that to an intermediate file containing the first challenge, and then copy that over the running config once it gets the second challenge.

To set this up, I'

```
"customDnsRecords": [
 {
  "label": "_acme-challenge",
  "record": "",
  "type": "TXT",
  "ttl": 60
 },
 {
  "label": "_acme-challenge",
  "record": "CHALLENGE2",
  "type": "TXT",
  "ttl": 60
 }
],
```

For this to work, you will have already needed to get Collaborator working
