"""Fix statuses: 01-05=LIVE, 06-20=TESTING, 21-100=DEV, 101-500=TESTING"""
with open('algo_configs.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# We'll process the file line by line tracking which algo ID we're in
lines = content.split('\n')
output = []
current_id = None

for line in lines:
    # Try to detect the id line
    id_match = re.search(r'"id":\s*"(\d+)"', line)
    if id_match:
        current_id = int(id_match.group(1))

    # Fix status line
    status_match = re.search(r'"status":\s*"(LIVE|TESTING|DEV)"', line)
    if status_match and current_id is not None:
        if current_id <= 5:
            correct = "LIVE"
        elif current_id <= 20:
            correct = "TESTING"
        elif current_id <= 100:
            correct = "DEV"
        else:
            correct = "TESTING"
        line = line.replace(f'"status": "{status_match.group(1)}"', f'"status": "{correct}"')

    output.append(line)

new_content = '\n'.join(output)
with open('algo_configs.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Done. Verifying...")
import importlib, sys
if 'algo_configs' in sys.modules:
    del sys.modules['algo_configs']
import algo_configs
statuses = {}
for a in algo_configs.ALGO_CONFIGS:
    s = a.get('status','?')
    statuses[s] = statuses.get(s,0) + 1
print(f"Status breakdown: {statuses}")
print(f"Total: {len(algo_configs.ALGO_CONFIGS)}")
