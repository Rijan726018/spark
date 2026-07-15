import algo_configs
total = len(algo_configs.ALGO_CONFIGS)
live = [a for a in algo_configs.ALGO_CONFIGS if a.get("status") == "LIVE"]
print(f"Total configs: {total}")
print(f"LIVE: {len(live)}")
print(f"Last ID: {algo_configs.ALGO_CONFIGS[-1]['id']}")
