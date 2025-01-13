# Burp Collaborator Scripts

## My Setup

In my setup I've installed collaborator in `/opt/burp` and created a symlink from `/opt/burp/burpsuite_pro.jar` to the latest version of the jar file. This way I can keep old versions around but the symlink always points to the latest version. The scripts here all assume that the system is setup like this, if you want to keep your own setup then you will need to adjust the file locations appropriately.

## Start Scripts

Rather than have to start and stop Collaborator by hand, I've created a start script and a systemd service file to make the process a lot easier and to fit with standard Linux services.

Because these files can be called from anywhere, I've put my config file at `/etc/collab/collab.json` and specify its location in the start script. There may be a better way to do this, but it work.

To use these two scripts, copy the files into these locations:

* `collab.service` -> `/etc/systemd/system/collab.service`
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

Before going any further, please, backup your current Collaborator setup, if you are on a VM, snapshot it, if not, make copies of all config files, certificates, and anything else you think might be necessary to restore the system if things go wrong.

This script is my attempt to automate renewing my Burp Collaborator certificate with Let's Encrypt. I'm using DNS TXT records which Collaborator itself is serving so the script takes the tokens passed by Let's Encrypt, updates the Collaborator config file, restarts it, then tells certbot to go ahead and do the renewal.

This process assumes you are using my start up scripts covered above as everything is automated once things are in place.

For this script to work, you need to have already setup Collaborator and have running a TLS server, there are plenty of guides for this, including the official one from [PortSwigger](https://portswigger.net/burp/documentation/collaborator/server/private).

I have two entries that need to go into the certificate SAN fields, one for the domain itself, and one for a wildcard for the domain, this requires two TXT DNS records. From what I've been able to understand from the certbot process, the bot requests a challenge from LE and then calls the hook script with that challenge, the script has to then do something with the challenge, in our case update the Collaborator config file, and then return control to certbot. Certbot then requests the second challenge and passes that to the script which updates the config for a second time. Once both challenges are in place, Collaborator needs to be restarted for the changes to take affect. After all of this, we can return control to certbot and let it tell LE we are ready to respond.

Because of this two step process of updating the config file, I've chosen to start with a template config file based on my working file, I copy that to an intermediate file containing the first challenge, and then copy that over the running config once it gets the second challenge.

If you are using my start up scripts, you will have your config file in `/etc/collab/collab.json`. This will be used as a template by the hook and needs to be copied to `/etc/collab/collab.json-template`.

Once there, you need to add (or edit) the following section. This creates two hardcoded DNS TXT records with values `CHALLENGE1` and `CHALLENGE2`. These placeholders will be replaced by the hook in the two setup process described above.

```
"customDnsRecords": [
 {
  "label": "_acme-challenge",
  "record": "CHALLENGE1",
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

The next step is to place `acme_collab.py` in the certbot directory `/etc/letsencrypt` and make it executable. You also need to copy `collab-deploy-hook.sh` to `/etc/letsencrypt/renewal-hooks/deploy/collab.sh` and make it executable as well.

Now is the time to test things.

Let's start by checking the script works, you can do this by running the following from the `/etc/letsencrypt` directory:

```
CERTBOT_VALIDATION=123 ./acme-collab.py
```

If this is successful, there will be no output to screen, but the file `/etc/collab/collab.json-int` will have been created and in the `customDnsRecords` section, `CHALLENGE1` will have been replaced by `123`. If this worked, it has successfully simulated setting up the first challenge. If this failed, I can't give much advice here as it works on my system. If there are any errors displayed to screen, read those and do a bit of googling, see what you can find. For some additional debug, the `acme-collab.py` has a bunch of commented out print statements, these can be uncommented so when the script is ran it will tell you what is going on and what stage it thinks it is at. If you are really stuck, raise a ticket and I'll see what I can do to help.

Assuming all is good so far, let's run the script again to do the second challenge:

```
CERTBOT_VALIDATION=987 ./acme-collab.py
```

If this step works, `/etc/collab/collab.json-int` will have been removed and the config file `/etc/collab/collab.json` updated with both challenge values, `123` and `987`. The collaborator server will have also been restarted. You can check this with:

```
dig TXT _acme-challenge.<your domain> @<your IP>
```

This will give you two TXT records matching the expected values.

Now all the testing is complete, we can now run it through certbot. This command tells it to use DNS for challenges and to use our script as the hook. Make sure to put your domain into the appropriate slots.

```
certbot certonly --manual --manual-auth-hook /etc/letsencrypt/acme-dns-auth.py --preferred-challenges dns --debug-challenges -d "*.<your domain>" -d <your domain> -v
```

This will give you a bunch of output, hopeful all good and no errors. This is a snippet from my system:

```
Running deploy-hook command: /etc/letsencrypt/renewal-hooks/deploy/collab

Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/<your domain>/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/<your domain>/privkey.pem
This certificate expires on 2025-04-13.
These files will be updated when the certificate renews.
Certbot has set up a scheduled task to automatically renew this certificate in the background.
```

Some things to look out for:

* The location of the certificate and key, these need to go into the Collaborator config file like this:

```
"ssl": {
  "certificateFiles": [
    "/etc/letsencrypt/live/<your domain>/fullchain.pem",
    "/etc/letsencrypt/live/<your domain>/privkey.pem"
  ]
}
```
* Check the deploy-hook command has been ran, this is what restarts Collaborator after the new certificates have been issues. If this isn't ran, you may get new certificates, but the server will still be pointing at the old ones.
* Check that the certificate is set to automatically renew, as long as you see this, you should now be able to leave the system to look after itself.

If you want to test that automatic renewals will work, you can do a dry run with this command:

```
certbot renew --dry-run
```

You should expect output similar to this:

```
Saving debug log to /var/log/letsencrypt/letsencrypt.log

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Processing /etc/letsencrypt/renewal/<your domain>.conf
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Simulating renewal of an existing certificate for *.<your domain> and <your domain>

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Congratulations, all simulated renewals succeeded: 
  /etc/letsencrypt/live/<your domain>/fullchain.pem (success)
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
```

And that is it, next time certbot decides the certificates new renewing it should be able to handle the full process itself. Like I said at the start though, this has only been tested on my own system, so there may well be bugs and cases where it doesn't work. If you get stuck, raise a ticket with as much information as you can give and I'll see what I can do to help. I'm not an expert at this, I learned all of this in a morning, so may not be much use, but I'll try.

## Automatic Collaborator Upgrade

I often end up multiple releases of Collaborator behind just because I forget to keep my eye on the releases and so created this script to automate keeping it up to date for me. It is inspired by an original script by @flakpaket but any bugs are mine, not his.

The script is `check_collab_version.sh` and to use it you can either place it in the path or in the directory with the Collaborator jar file. Once there, make it executable.

The script works by calling the PortSwigger download server and checking the filename of the latest version of the jar file. It then compares this with the file I currently have symlinked to `/opt/burp/burpsuite_pro.jar` and if they don't match, it pulls down the latest version, moves the symlink over, and then restarts the service.

To automate this I've setup a cron job to run at 2am every day to run the script:

```
0 2 * * * /usr/local/bin/check_collab_version.sh
```

If the script finds an update, it writes the details to standard out. I have a `MAILTO` address setup in my `crontab` file so that the details get sent to me so I know the upgrade has happened.
