content = open("D:/AEGIS-local/api.py", "r", encoding="utf-8").read()

live_block = """
# --- Live Replay Endpoints -------------------------------------------
from src.live_replay import replay_manager

@app.get("/api/live/tick")
def live_tick(dataset: str = Query(...)):
    _require_dataset(dataset)
    return replay_manager.tick(dataset)

@app.get("/api/live/status")
def live_status(dataset: str = Query(...)):
    _require_dataset(dataset)
    return replay_manager.status(dataset)

@app.post("/api/live/reset")
def live_reset(dataset: str = Query(...)):
    _require_dataset(dataset)
    replay_manager.reset(dataset)
    return {"status": "reset", "dataset": dataset}

"""

marker = 'if __name__ == "__main__":'
content = content.replace(marker, live_block + marker)
open("D:/AEGIS-local/api.py", "w", encoding="utf-8").write(content)
print("Done")