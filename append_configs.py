"""Run this to append 400 new algo configs to algo_configs.py"""
import sys
sys.path.insert(0, '.')
from generate_configs import generate_configs

new_cfgs = generate_configs()
lines = []
lines.append('')
lines.append('    # ── GENERATED (101-500) ────────────────────────────────────────────────')

for c in new_cfgs:
    params_str = repr(c['params'])
    csv_val    = repr(c['csv'])
    cid        = c['id']
    lines.append('    {')
    lines.append(f'        "id": "{cid}", "name": {repr(c["name"])}, "category": {repr(c["category"])},')
    lines.append(f'        "description": {repr(c["description"])},')
    lines.append(f'        "market": {repr(c["market"])}, "tick_value": {c["tick_value"]}, "timeframe": {repr(c["timeframe"])}, "period": {repr(c["period"])},')
    lines.append(f'        "status": "TESTING", "engine": {repr(c["engine"])},')
    lines.append(f'        "params": {params_str},')
    lines.append(f'        "script": None, "csv": {csv_val}, "alt_csv": None, "chart": None, "alt_chart": None,')
    lines.append('    },')

append_text = '\n'.join(lines)

with open('algo_configs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Insert before the closing ] of ALGO_CONFIGS
insert_pos = content.rfind(']')
new_content = content[:insert_pos] + append_text + '\n' + content[insert_pos:]

with open('algo_configs.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Appended {len(new_cfgs)} configs. Total file size: {len(new_content):,} bytes')
