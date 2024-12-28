# Hive Control

## Overview

Control your Hive heating system through git, because why wouldn't you want
that? Git is truth.

## Setup

1. Clone this repository

````
$ git clone https://github.com/m4rkw/hivecontrol
````

2. Install dependencies

````
$ pip install -r requirements.txt
````

Note: pyhiveapi2 is a fork of the original pyhiveapi that has been [updated](https://github.com/m4rkw/pyhiveapi2/commit/18c7693a69d49d5ece09e21e205afc22b85c6ec1)
to allow configuring schedules via the API.

3. Copy hive.yaml.example to hive.yaml and fill in your Hive username and
   password.

4. Generate a device key:

If you have SMS 2FA enabled you will need to enter the code sent via SMS.

````
$ ./generate_device_key.py
Enter your Hive username: <HIVE USERNAME>
Enter your Hive password:
Enter a name for this device: myserver
Enter your 2FA code: 621348
device registration successful

DEVICE KEY: eu-west-1_....
DEVICE GROUP KEY: aaaaa
DEVICE PASSWORD: bbbbb
````

Make a note of the DEVICE KEY, DEVICE GROUP KEY and DEVICE PASSWORD as you will
need these for the next step.

5. Copy hive.yaml.example to hive.yaml and fill in your Hive username, password,
   device key, device group key and device password.

6. Edit the schedule config in hive.yaml to your liking. The device names must
match the thermostat names configured in the Hive app. If "mode" is set for a
device then the script will ensure the mode is set, so for example if it's set
to "schedule" and the device is "off" it will revert it back to "schedule".

7. Apply the schedules with:

````
$ ./hivecontrol.py hive.yaml
````

## Exercises for the reader

- Implement a webhook to trigger the script on a push to main OR:
- Run the script as a lambda function on AWS to automatically apply changes when
  pushed to git
- Implement away mode (see the code for the `in_away_mode` function)
- Integrate with a weather API to adjust the schedule based on the weather (eg
  openweathermap.org)
- Deploy Home Assistant and use the Hass python library to retrieve telemetry
  for all of your hive devices
- Chart the telemetry with Grafana

See telemetry.py for an example of how to retrieve telemetry from the Home
Assistant API and from OpenWeatherMap.
