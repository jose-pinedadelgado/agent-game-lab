# Pixel Village (prototype)

A tiny 3D voxel/pixel-art life sim (build a home, villagers with needs), designed so **agents can observe and act** over a simple HTTP JSON API.

## Run
```bash
python village/server.py          # open http://localhost:8765
python village/agent_example.py   # optional: rule-based agent that tends villager needs
```
Python stdlib only; three.js loads from a CDN in the browser.

## Controls
Left-click: place selected block on current layer · Right-click: remove · Middle-drag: orbit · Wheel: zoom.

## Agent API
- `GET /state` → `{tick, size, kinds, blocks:[{x,y,z,kind}], villagers:[{id,name,x,z,activity,needs}], events}`
- `POST /action`, one of:
  - `{"type":"build","x":10,"y":0,"z":4,"kind":"wall"}`
  - `{"type":"remove","x":10,"y":0,"z":4}`
  - `{"type":"move","villager":"ana","x":12,"z":12}`
  - `{"type":"use","villager":"ana","kind":"fridge"}` (fridge→hunger, bed→energy, tv/sofa→fun)

Needs decay every tick (0.5s); villagers standing adjacent gain `social`.

## Tests
`uv run pytest -q village/test_world.py`

## Next steps
Pathfinding around walls, more villagers & relationships, save/load, WebSocket push, per-agent identity/permissions, LLM agent adapter.
