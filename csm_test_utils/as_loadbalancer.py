"""Script for new dashboard (sandbox)"""

import time

import requests

telegraf = "localhost:8080/telegraf"
MEASUREMENT = "as_loadbalancer"


def report(result, reason):
    influx_row = f"${MEASUREMENT},reason=${reason} state=\"${result}\""
    res = requests.post(telegraf, data=influx_row)
    assert res.status_code == 204, f'Status is {res.status_code}'


# HINTS TODO: setup telegraf local на вмку поставить запустить скрипт указать адрес телеграфа и смотреть (селектом смотреть) *requests*
# continuous.py
# kappelmeister delatore start daemon

def main():
    while True:
        if 1:
            report('connected', 'ok')
            time.sleep(10)
        else:
            report('connection_lost', 'fail')
            time.sleep(10)


if __name__ == "__main__":
    main()
