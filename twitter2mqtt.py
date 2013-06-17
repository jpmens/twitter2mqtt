#!/usr/bin/env python

# Copyright (C) 2013, Jan-Piet Mens <jpmens()gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


import twitter  # pip install python-twitter
                # https://pypi.python.org/pypi/python-twitter
import sys, os
import mosquitto
import ConfigParser
import codecs
import json

config_file = "twitter2mqtt.ini"

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

def getall(twitter_since_id, mqttc, prefix):

    maxid = 0
    statuses = twiapi.GetHomeTimeline(count=200, 
                                     since_id=twitter_since_id, 
                                     include_entities=True)

    for tweet in statuses:
        tweet_id = int(tweet.GetId())
        if tweet_id > maxid:
            maxid = tweet_id
        
        text = tweet.GetText()
        author = tweet.GetUser()
        author_screenname = author.GetScreenName()

        topic = "%s/%s" % (prefix, author_screenname)
        payload = json.dumps(text)
        print topic, payload
        rc, mid = mqttc.publish(topic, payload, qos=0, retain=False)

    return maxid

if __name__ == "__main__":
    try:
        config = ConfigParser.ConfigParser()
        config.readfp(open(config_file, "r"))
    except IOError as e:
        print e
        sys.exit(1)

    try:
        try:
            consumer_key = config.get("Twitter", "Consumer Key")
            consumer_secret = config.get("Twitter", "Consumer Secret")
            access_token_key = config.get("Twitter", "Access Token Key")
            access_token_secret = config.get("Twitter", "Access Token Secret")
        except ConfigParser.NoSectionError:
            print "Missing Twitter section in config file. This is a problem."
            sys.exit(1)
        except ConfigParser.NoOptionError:
            print "Missing Twitter options in config file. This is a problem."
            sys.exit(1)
    except Exception as e:
        print "Unable to parse arguments or config file"
        print e
        sys.exit(1)

    try:
        twitter_since_id = config.getint("Twitter", "sinceid")
    except ConfigParser.NoOptionError:
        twitter_since_id = 0

    try:
        host = config.get("MQTT", "host") 
    except ConfigParser.NoOptionError:
        host = os.getenv("MQTT_BROKER", "localhost")
    try:
        port = config.getint("MQTT", "port") 
    except ConfigParser.NoOptionError:
        port = int(os.getenv("MQTT_BROKER", "1883"))
    try:
        prefix = config.get("MQTT", "prefix") 
    except ConfigParser.NoOptionError:
        prefix = "twitter"

    twiapi = twitter.Api( consumer_key=consumer_key,
                          consumer_secret=consumer_secret,
                          access_token_key=access_token_key,
                          access_token_secret=access_token_secret
                          )

    mqttc = mosquitto.Mosquitto()
    mqttc.connect(host, port)
    mqttc.loop_start()

    latest_id = getall(twitter_since_id, mqttc, prefix)

    mqttc.loop_stop()
    mqttc.disconnect()

    if latest_id > twitter_since_id:
        config.set("Twitter", "sinceid", str(latest_id))
        try:
            config.write(open(config_file, "w"))
        except IOError:
            print "Unable to write config file"
