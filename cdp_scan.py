# -*- coding: utf-8 -*-
import requests, json

resp = requests.get('http://127.0.0.1:9227/json/list', timeout=5)
tabs = resp.json()
for t in tabs:
    print(t.get('title','?'), '->', t.get('url','?')[:120])
