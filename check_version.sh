#!/usr/bin/env sh

install_directory=/opt/burp
installed_version=$(basename `readlink -f $install_directory/burpsuite_pro.jar`)
current_version=`curl 'https://portswigger.net/burp/releases/download?product=pro' -sI | grep content-disposition | sed "s/.*filename=\(.*\);.*/\1/"`

if [ "$installed_version" != "$current_version" ]; then
	cd $install_directory
	curl -OJs --location 'https://portswigger.net/burp/releases/download?product=pro'
	rm burpsuite_pro.jar
	ln -s $current_version burpsuite_pro.jar
	/usr/sbin/service collab restart

	echo "Burp Collaborator upgraded from $installed_version to $current_version"
fi
