# raspi-stats
A very funny project for the Pi, ha ha ha ha ha.

This is a utility that collects information about the system and network at given intervals and uploads them to a server for later analysis. The client is written in Python 2. The server is written in node.js and stores the data in a MongoDB database.

## Client install

    sudo apt-get install screen python-pip
    sudo pip install requests
    git clone https://github.com/proog/raspi-stats.git
    
    screen
    raspi-stats/raspi-stats.py -u <url> -v <nickname>
    Ctrl+A D

## Server install
    cd raspi-stats
    sudo npm install
    node server.js
