from flask import Flask, request, jsonify, send_from_directory
from json import load, dump
from typing import Any

app = Flask(__name__, static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 1 << 16

records: dict[str, dict[str, Any]] = {}
try:
    with open("records.json") as f:
        data = dict(load(f))
        for k, v in data.items():
            records[k] = dict(v)
except:
    pass

@app.route("/rename", methods=["POST"])
def rename():
    if request.remote_addr in records:
        name = request.get_data(as_text=True)
        if len(name) > 100:
            name = f"({len(name)} chars) {name[:100]}..."
        records[request.remote_addr]["name"] = name
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "PLAY A GAME FIRST!!!"}), 400

@app.route("/action", methods=["POST"])
def calc_action():
    if request.remote_addr == "172.16.22.230":
        return jsonify("讨厌！！！！"), 403
    try:
        req = request.json
        assert req is not None
        pt: float = 0.0
        ph: float = 1.0
        action = 0.0
        for t, h in req:
            t = float(t)
            dt = t - pt
            if t < 0.01 or t >= 4.9 or dt <= 0:
                continue
            h = 1 - float(h)
            assert h >= 0 and h <= 1
            dh = h - ph
            action += dh * dh / (2 * dt) - 0.08 * ((ph + h) / 2) * dt
            pt = t
            ph = h
        if pt < 4.85:
            action -= 0.08 * ph * (4.9 - pt)
            pt = 4.9
        dt = 5 - pt
        dh = -ph
        action += dh * dh / (2 * dt) - 0.08 * (ph / 2) * dt + 2 / 15
        rename = False
        if request.remote_addr:
            if request.remote_addr not in records:
                records[request.remote_addr] = {"record": action}
                rename = True
            elif records[request.remote_addr]["record"] > action:
                records[request.remote_addr]["record"] = action
                if not records[request.remote_addr].get("name", ""):
                    rename = True
        with open("records.json", "w") as f:
            dump(records, f)
        if rename:
            return jsonify({"status": "success", "action": action, "rename": True})
        return jsonify({"status": "success", "action": action})
    except:
        return jsonify({"status": "error", "message": "bad JSON data"}), 400

@app.route("/leaderboard")
def leaderboard():
    return jsonify(sorted([
        {"name": v.get("name", ""), "record": v["record"], "its_you": True}
        if k == request.remote_addr else
        {"name": v.get("name", ""), "record": v["record"]}
        for k, v in records.items()
    ], key=lambda x: x["record"]))

@app.route("/<path:filename>")
@app.route("/")
def index(filename: str | None = None):
    assert app.static_folder is not None
    return send_from_directory(app.static_folder, filename or "index.html")

@app.errorhandler(404)
def debugging_required(_):
    assert app.static_folder is not None
    return send_from_directory(app.static_folder, "404.html")

if __name__ == '__main__':
    app.run("0.0.0.0", 80, True)
