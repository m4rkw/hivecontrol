#!/usr/bin/env python3

import os
import sys
import json
import math
import datetime
import getpass
from pyhiveapi import Auth, API
from pyhiveapi.hive import Hive
from pyhiveapi.session import HiveSession

HIVE_USERNAME = input("Enter your Hive username: ")
HIVE_PASSWORD = getpass.getpass("Enter your Hive password: ")
DEVICE_NAME = input("Enter a name for this device: ")

if len(DEVICE_NAME) == 0:
    raise Exception("must enter a device name")

auth = Auth(HIVE_USERNAME, HIVE_PASSWORD)

try:
    authData = auth.login()
except Exception as e:
    print(f"Authentication failed: {e}")
    sys.exit(1)

if authData.get("ChallengeName") == "SMS_MFA":
    code = input("Enter your 2FA code: ")
    authData = auth.sms_2fa(code, authData)

if "AuthenticationResult" not in authData:
    print(f"Authentication failed:")
    print(json.dumps(authData, indent=4))
    sys.exit(1)

session = authData["AuthenticationResult"]

authData = auth.device_registration(DEVICE_NAME)

deviceKey = auth.device_key
deviceGroupKey = auth.device_group_key
devicePassword = auth.device_password

print("device registration successful\n")
print(f"DEVICE KEY: {deviceKey}")
print(f"DEVICE GROUP KEY: {deviceGroupKey}")
print(f"DEVICE PASSWORD: {devicePassword}")
