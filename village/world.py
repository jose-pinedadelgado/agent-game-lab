"""Tiny voxel village simulation. Pure Python, deterministic given a seed."""
from __future__ import annotations

import random
import threading

SIZE = 24
# kind -> which need it satisfies (None = structural)
KINDS = {
    "wall": None, "floor": None, "roof": None, "door": None, "tree": None, "path": None,
    "bed": "energy", "fridge": "hunger", "tv": "fun", "sofa": "fun",
}
NEEDS = ("hunger", "energy", "fun", "social")


class World:
    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)
        self.lock = threading.Lock()
        self.tick_count = 0
        self.blocks: dict[tuple[int, int, int], str] = {}
        self.events: list[dict] = []
        self.villagers = [
            {"id": "ana", "name": "Ana", "x": 5, "z": 5, "target": None, "activity": "idle",
             "needs": {n: 80.0 for n in NEEDS}},
            {"id": "ben", "name": "Ben", "x": 8, "z": 6, "target": None, "activity": "idle",
             "needs": {n: 70.0 for n in NEEDS}},
        ]
        for _ in range(10):
            self.blocks[(self.rng.randrange(SIZE), 0, self.rng.randrange(SIZE))] = "tree"
        self._starter_house(3, 3)

    def _starter_house(self, ox: int, oz: int) -> None:
        for dx in range(5):
            for dz in range(5):
                edge = dx in (0, 4) or dz in (0, 4)
                pos = (ox + dx, 0, oz + dz)
                if edge:
                    self.blocks[pos] = "door" if (dx, dz) == (2, 4) else "wall"
                else:
                    self.blocks[pos] = "floor"
        self.blocks[(ox + 1, 0, oz + 1)] = "bed"
        self.blocks[(ox + 3, 0, oz + 1)] = "fridge"
        self.blocks[(ox + 3, 0, oz + 3)] = "tv"

    # ---- observation -------------------------------------------------
    def state(self) -> dict:
        with self.lock:
            return {
                "tick": self.tick_count, "size": SIZE, "kinds": list(KINDS),
                "blocks": [{"x": x, "y": y, "z": z, "kind": k} for (x, y, z), k in self.blocks.items()],
                "villagers": [dict(v, needs=dict(v["needs"])) for v in self.villagers],
                "events": self.events[-20:],
            }

    # ---- actions -----------------------------------------------------
    def act(self, action: dict) -> dict:
        with self.lock:
            t = action.get("type")
            try:
                if t == "build":
                    return self._build(int(action["x"]), int(action.get("y", 0)), int(action["z"]), action["kind"])
                if t == "remove":
                    pos = (int(action["x"]), int(action.get("y", 0)), int(action["z"]))
                    if self.blocks.pop(pos, None) is None:
                        return {"ok": False, "error": "nothing there"}
                    return self._log({"type": "remove", "pos": pos})
                if t == "move":
                    v = self._villager(action["villager"])
                    v["target"] = [int(action["x"]), int(action["z"])]
                    v["activity"] = "walking"
                    return self._log({"type": "move", "villager": v["id"], "to": v["target"]})
                if t == "use":
                    return self._use(self._villager(action["villager"]), action["kind"])
            except (KeyError, ValueError) as e:
                return {"ok": False, "error": f"bad action: {e}"}
            return {"ok": False, "error": f"unknown action type {t!r}"}

    def _build(self, x, y, z, kind):
        if kind not in KINDS:
            return {"ok": False, "error": f"unknown kind {kind!r}"}
        if not (0 <= x < SIZE and 0 <= z < SIZE and 0 <= y < 4):
            return {"ok": False, "error": "out of bounds"}
        if (x, y, z) in self.blocks:
            return {"ok": False, "error": "occupied"}
        self.blocks[(x, y, z)] = kind
        return self._log({"type": "build", "kind": kind, "pos": [x, y, z]})

    def _use(self, v, kind):
        spots = [(x, z) for (x, y, z), k in self.blocks.items() if k == kind]
        if not spots or KINDS.get(kind) is None:
            return {"ok": False, "error": f"no usable {kind}"}
        spots.sort(key=lambda p: abs(p[0] - v["x"]) + abs(p[1] - v["z"]))
        v["target"] = list(spots[0])
        v["activity"] = f"going to {kind}"
        v["use"] = kind
        return self._log({"type": "use", "villager": v["id"], "kind": kind})

    def _villager(self, vid):
        for v in self.villagers:
            if v["id"] == vid:
                return v
        raise KeyError(vid)

    def _log(self, ev):
        ev["tick"] = self.tick_count
        self.events.append(ev)
        return {"ok": True, "event": ev}

    # ---- simulation --------------------------------------------------
    def tick(self) -> None:
        with self.lock:
            self.tick_count += 1
            for v in self.villagers:
                for n in NEEDS:
                    v["needs"][n] = max(0.0, v["needs"][n] - self.rng.uniform(0.2, 0.6))
                if v["target"]:
                    tx, tz = v["target"]
                    if (v["x"], v["z"]) == (tx, tz):
                        kind = v.pop("use", None)
                        v["target"] = None
                        v["activity"] = f"using {kind}" if kind else "idle"
                        if kind:
                            need = KINDS[kind]
                            v["needs"][need] = min(100.0, v["needs"][need] + 40)
                    else:
                        v["x"] += (tx > v["x"]) - (tx < v["x"])
                        v["z"] += (tz > v["z"]) - (tz < v["z"])
            a, b = self.villagers[0], self.villagers[1]
            if abs(a["x"] - b["x"]) + abs(a["z"] - b["z"]) <= 1:
                for v in (a, b):
                    v["needs"]["social"] = min(100.0, v["needs"]["social"] + 2)
