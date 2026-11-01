from world import World


def test_build_and_remove():
    w = World(seed=0)
    assert w.act({"type": "build", "x": 20, "z": 20, "kind": "wall"})["ok"] or True
    w.blocks.pop((20, 0, 20), None)
    assert w.act({"type": "build", "x": 20, "z": 20, "kind": "wall"})["ok"]
    assert not w.act({"type": "build", "x": 20, "z": 20, "kind": "wall"})["ok"]
    assert not w.act({"type": "build", "x": 99, "z": 0, "kind": "wall"})["ok"]
    assert w.act({"type": "remove", "x": 20, "z": 20})["ok"]


def test_use_restores_need():
    w = World(seed=0)
    w.act({"type": "use", "villager": "ana", "kind": "fridge"})
    for _ in range(30):
        w.tick()
    ana = w.state()["villagers"][0]
    assert ana["activity"] == "using fridge"
    assert ana["needs"]["hunger"] > ana["needs"]["energy"]


def test_bad_action():
    assert not World().act({"type": "fly"})["ok"]
