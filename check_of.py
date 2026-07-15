import algo_configs
of_algos = [a for a in algo_configs.ALGO_CONFIGS if a.get("category") == "Order Flow"]
print(f"Order Flow configs: {len(of_algos)}")
for a in of_algos:
    print(f"  [{a['id']}] {a['name']} -- {a['engine']}")
