#!/usr/bin/env python3

import os
import re
import sys
import json
import time
import datetime
import warnings
import requests
from hassapi import Hass
from elasticsearch import Elasticsearch

TOKEN = '<HASS TOKEN>'
WEATHER_API_KEY = '<OPENWEATHERMAP API KEY>'
OPENSEARCH_USERNAME = 'admin'
OPENSEARCH_PASSWORD = '<OPENSEARCH PASSWORD>'

# GPS coords of your home to use with OpenWeatherMap
HOME_GPS_LATITUDE = ''
HOME_GPS_LONGITUDE = ''

CAPTURE = [
    {
        "data_type": "printer-ink",
        "metadata": {
            "printer": "downstairs"
        },
        "sources": [
            "sensor.hp_photosmart_b110_series_black_ink",
            "sensor.hp_photosmart_b110_series_cyan_ink",
            "sensor.hp_photosmart_b110_series_magenta_ink",
            "sensor.hp_photosmart_b110_series_yellow_ink",
        ]
    },
    {
        "data_type": "hive",
        "sources": [
            "climate.kids_bedroom",
            "climate.dining_room",
            "climate.hallway",
            "climate.living_room",
            "climate.main_bedroom",
            "climate.office",
            "binary_sensor.kids_bedroom_state",
            "binary_sensor.kids_bedroom_boost",
            "binary_sensor.dining_room_state",
            "binary_sensor.dining_room_boost",
            "binary_sensor.hallway_state",
            "binary_sensor.hallway_boost",
            "binary_sensor.living_room_state",
            "binary_sensor.living_room_boost",
            "binary_sensor.main_bedroom_state",
            "binary_sensor.main_bedroom_boost",
            "binary_sensor.office_state",
            "binary_sensor.office_boost",
            "sensor.kids_bedroom_current_temperature",
            "sensor.kids_bedroom_target_temperature",
            "sensor.kids_bedroom_mode",
            "sensor.dining_room_current_temperature",
            "sensor.dining_room_target_temperature",
            "sensor.dining_room_mode",
            "sensor.hallway_current_temperature",
            "sensor.hallway_target_temperature",
            "sensor.hallway_mode",
            "sensor.living_room_current_temperature",
            "sensor.living_room_target_temperature",
            "sensor.living_room_mode",
            "sensor.main_bedroom_current_temperature",
            "sensor.main_bedroom_target_temperature",
            "sensor.main_bedroom_mode",
            "sensor.office_current_temperature",
            "sensor.office_target_temperature",
            "sensor.office_mode",
            "sensor.hallway_battery_level",
            "sensor.office_battery_level",
            "sensor.main_bedroom_battery_level",
            "sensor.kids_bedroom_battery_level",
            "sensor.living_room_battery_level",
            "sensor.dining_room_battery_level"
        ]
    },
    {
        "data_type": "printer-ink",
        "metadata": {
            "printer": "upstairs"
        },
        "sources": [
            "sensor.hp_deskjet_2600_series_black_ink",
            "sensor.hp_deskjet_2600_series_tri_color_ink"
        ]
    }
]

INTERVAL = 10

warnings.filterwarnings("ignore")

class Telemetry:

    def __init__(self):
        self.hass = Hass(hassurl="http://localhost:8123/", token=TOKEN)

        self.es = Elasticsearch(
            'https://localhost:9200',
            http_auth=(OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD),
            verify_certs=False
        )


    def main(self):
        while 1:
            self.capture()
            self.get_temperature()

            time.sleep(INTERVAL)


    def capture(self):
        data = self.hass.get_states()

        today = datetime.datetime.now().strftime('%Y.%m.%d')

        index = f"telemetry-{today}"

        for entry in CAPTURE:
            obj = self.extract_data(data, entry['sources'])

            obj['s_data_type'] = entry['data_type']

            if 'metadata' in entry:
                for key in entry['metadata']:
                    obj[f"s_{key}"] = entry['metadata'][key]

            obj['@timestamp'] = datetime.datetime.now().isoformat()

            self.es.index(index=index, body=obj)


    def get_temperature(self):
        resp = requests.get(f"http://api.openweathermap.org/data/2.5/weather?lat={HOME_GPS_LATITUDE}&lon={HOME_GPS_LONGITUDE}&appid={WEATHER_API_KEY}&units=metric")

        try:
            data = json.loads(resp.text)

            if 'main' in data and 'temp' in data['main']:
                obj = {
                    '@timestamp': datetime.datetime.now().isoformat(),
                    's_data_type': 'temperature',
                    's_latitude': '51.3883575',
                    's_longitude': '-0.2133371',
                    's_weather': data['weather'][0]['main'],
                    's_description': data['weather'][0]['description'],
                    'f_temperature': data['main']['temp'],
                    'f_feels_like': data['main']['feels_like'],
                    'i_pressure': data['main']['pressure'],
                    'i_humidity': data['main']['humidity'],
                    'i_visibility': data['visibility'],
                    'i_wind_speed': data['wind']['speed'],
                    'i_wind_deg': data['wind']['deg']
                }

                today = datetime.datetime.now().strftime('%Y.%m.%d')

                index = f"telemetry-{today}"

                self.es.index(index=index, body=obj)

        except:
            pass


    def extract_data(self, data, sources):
        obj = {}

        for source in sources:
            obj.update(self.extract_data_source(data, source))

        for key in obj:
            m = re.match('^f_sensor_(.*?)_current_temperature$', key)

            if m and m.group(1) != 'hallway':
                zone = m.group(1)

                target = f"f_sensor_{zone}_target_temperature"

                if obj[target] - obj[key] < 0.5:
                    obj[f"s_binary_sensor_{zone}_state"] = 'off'
                    obj[f"i_binary_sensor_{zone}_state"] = 0

        return obj


    def extract_data_source(self, data, source):
        obj = {}

        for item in data:
            if item.entity_id == source:
                if item.state.isdigit():
                    key = f"i_{item.entity_id.replace('.','_')}"
                    obj[key] = int(item.state)
                elif re.match(r'^[\d]+[\d\.]+[\d]+$', item.state):
                    key = f"f_{item.entity_id.replace('.','_')}"
                    obj[key] = float(item.state)
                else:
                    key = f"s_{item.entity_id.replace('.','_')}"
                    obj[key] = str(item.state)

                    if str(item.state) in ['on','off']:
                        key = f"i_{item.entity_id.replace('.','_')}"

                        if str(item.state) == 'on':
                            obj[key] = 1
                        else:
                            obj[key] = 0

        return obj


t = Telemetry()
t.main()
