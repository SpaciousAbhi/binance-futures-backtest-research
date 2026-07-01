import json

with open("reports/search_checkpoint.json", "r") as f:
    data = json.load(f)

print("completed_index:", data.get("completed_index"))
print("leaderboard size:", len(data.get("leaderboard", [])))
print("tested_hashes count:", len(data.get("tested_hashes", [])))
