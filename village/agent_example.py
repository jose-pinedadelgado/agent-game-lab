"""Minimal rule-based agent: keeps villagers' needs up. Swap the rule for an LLM call."""
import json
import time
import urllib.request

URL = "http://localhost:8765"
NEED_TO_KIND = {"hunger": "fridge", "energy": "bed", "fun": "tv"}


def call(path, payload=None):
    req = urllib.request.Request(URL + path, data=json.dumps(payload).encode() if payload else None,
                                 headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req))
    except urllib.error.HTTPError as e:
        return json.load(e)


while True:
    state = call("/state")
    for v in state["villagers"]:
        if v["target"]:
            continue
        need, value = min(((n, x) for n, x in v["needs"].items() if n in NEED_TO_KIND), key=lambda p: p[1])
        if value < 50:
            print(v["name"], "->", NEED_TO_KIND[need], call("/action", {"type": "use", "villager": v["id"], "kind": NEED_TO_KIND[need]}))
    time.sleep(2)
