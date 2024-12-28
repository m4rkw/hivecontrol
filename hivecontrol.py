#!/usr/bin/env python3

import os
import sys
import json
import yaml
import math
import datetime
from pyhiveapi import Auth, API
from pyhiveapi.hive import Hive
from pyhiveapi.session import HiveSession

class HiveSchedules:

    def main(self, config_file):
        if not os.path.exists(config_file):
            raise Exception(f"config file {config_file} not found")

        self.out(f"loading config ... ")

        self.config = yaml.safe_load(open(config_file).read())

        devices = {}

        for device in self.config['devices']:
            devices[device['name']] = device

        self.out("OK\n")

        self.out("authenticating ... ")

        for i in range(0, 3):
            try:
                session = self.authenticate()
                break
            except Exception as e:
                if i == 2:
                    raise e

                time.sleep(3)

        self.out("OK\n")

        self.out("reading current Hive config ... ")

        data = session.api.getAll()

        current_schedules = {}
        current_modes = {}

        for product in data['parsed']['products']:
            if product['type'] in ['heating','trvcontrol']:
                current_schedules[product['state']['name']] = product['state']['schedule']
                current_modes[product['state']['name']] = product['state']['mode']

        self.out("OK\n")

        for device in session.deviceList['climate']:
            if current_modes[device['hiveName']].lower() == 'boost':
                # devices in boost mode are ignored so manual boost in the Hive app isn't reverted
                self.out(f"ignoring {device['hiveName']} in boost mode\n")
                continue

            if device['hiveName'] not in devices:
                self.out(f"ignoring {device['hiveName']} (not in config)\n")
                continue

            if 'mode' not in devices[device['hiveName']]:
                continue

            target_mode = devices[device['hiveName']]['mode'].upper()

            if target_mode in ['MANUAL','SCHEDULE'] and self.in_away_mode():
                target_mode = 'OFF'

            if current_modes[device['hiveName']] != target_mode:
                self.out(f"setting {device['hiveName']} from {current_modes[device['hiveName']].lower()} to {target_mode} ... ")
                resp = session.api.setState(device['hiveType'], device['hiveID'], mode = target_mode)

                if 'original' in resp and resp['original'] == 200:
                    self.out("OK\n")
                else:
                    self.out("FAILED\n")
                    print(json.dumps(resp,indent=4))

        for device in session.deviceList['climate']:
            if device['hiveName'] not in devices:
                self.out(f"ignoring {device['hiveName']} (not in config)\n")
                continue

            if 'schedule' not in devices[device['hiveName']]:
                self.out(f"ignoring {device['hiveName']} (no schedule config)\n")
                continue

            self.out(f"checking schedule for zone: {device['hiveName']} ... ")

            schedule = {}

            for day in ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']:
                schedule[day] = []

                today = datetime.datetime.now().strftime('%Y.%m.%d')

                if 'override' in self.config and \
                    'devices' in self.config['override'] and \
                    device['hiveName'] in self.config['override']['devices'] and \
                    'schedule' in self.config['override']['devices'][device['hiveName']] and \
                    today in self.config['override']['devices'][device['hiveName']]['schedule']:

                    use_schedule = self.config['override']['devices'][device['hiveName']]['schedule'][today]

                else:
                    use_schedule = devices[device['hiveName']]['schedule']

                if day in use_schedule:
                    day_schedule = use_schedule[day]
                else:
                    day_schedule = use_schedule['default']

                for start in day_schedule:
                    hours, mins = start.split(':')

                    offset = (int(hours) * 60) + int(mins)

                    target = day_schedule[start]

                    schedule[day].append({
                        'value': {'target': target},
                        'start': offset
                    })

            if current_schedules[device['hiveName']] != schedule:
                self.out("UPDATING ... ")

                resp = session.api.setState(device['hiveType'], device['hiveID'], schedule = schedule)

                if 'original' in resp and resp['original'] == 200:
                    self.out("OK\n")
                else:
                    self.out("FAILED\n")
                    print(json.dumps(resp,indent=4))
            else:
                self.out("NO CHANGE\n")


    def authenticate(self):
        session = Hive(username=self.config['hive_username'], password=self.config['hive_password'])

        session.auth.device_key = self.config['device_key']
        session.auth.device_group_key = self.config['device_group_key']
        session.auth.device_password = self.config['device_password']

        resp = session.deviceLogin()

        if 'AuthenticationResult' not in resp or 'AccessToken' not in resp['AuthenticationResult']:
            raise Exception("authentication failed")

        session.startSession()

        return session


    def out(self, msg):
        sys.stdout.write(msg)
        sys.stdout.flush()


    def in_away_mode(self):
        # implement your own away mode state tracking logic here
        return False


if len(sys.argv) <2:
    print(f"Usage: {sys.argv[0]} <config file>")
    sys.exit(0)


hs = HiveSchedules()
hs.main(sys.argv[1])
