"""Rebuild algo_configs.py cleanly from the original LIVE configs + 400 new ones."""
import sys
sys.path.insert(0, '.')

# Import current (messy) configs and deduplicate
import algo_configs as _ac

seen = set()
clean = []
for a in _ac.ALGO_CONFIGS:
    key = str(a['id'])
    if key not in seen:
        seen.add(key)
        clean.append(a)

print(f"Deduped: {len(_ac.ALGO_CONFIGS)} -> {len(clean)} unique configs")

from generate_configs import generate_configs
new = generate_configs()
print(f"Generated {len(new)} new configs")

# Combine: keep original 100 + add 400 new
all_configs = clean[:100] + new
print(f"Total: {len(all_configs)} configs")

# Write new algo_configs.py
lines = [
    '"""',
    'ALGO CONFIGS — 500 Trading Algorithm Registry',
    'Each config defines a fully described strategy for ES/NQ/Gold/Oil/Bond futures.',
    '"""',
    'from pathlib import Path',
    '',
    'BASE = Path(__file__).parent',
    '',
    'def p(rel):',
    '    return str(BASE / rel) if rel else None',
    '',
    'ALGO_CONFIGS = [',
]

for c in all_configs:
    lines.append('    {')
    lines.append(f'        "id": {repr(c["id"])}, "name": {repr(c["name"])}, "category": {repr(c["category"])},')
    lines.append(f'        "description": (')
    # Word-wrap description
    desc = c.get("description", "")
    lines.append(f'            {repr(desc)}')
    lines.append(f'        ),')
    lines.append(f'        "market": {repr(c.get("market","ES=F"))}, "tick_value": {c.get("tick_value",50.0)}, "timeframe": {repr(c.get("timeframe","1h"))}, "period": {repr(c.get("period","730d"))},')
    lines.append(f'        "status": {repr(c.get("status","DEV"))}, "engine": {repr(c.get("engine",""))},')
    lines.append(f'        "params": {repr(c.get("params",{}))},')

    script = c.get("script")
    csv    = c.get("csv")
    alt_csv = c.get("alt_csv")
    chart  = c.get("chart")
    alt_chart = c.get("alt_chart")

    # Convert absolute paths back to p() calls for portability
    def to_p(val):
        if val is None:
            return 'None'
        val = str(val).replace('\\', '/')
        base = str(c.get('__base__', '')).replace('\\','/')
        # Try to make relative
        import re
        m = re.search(r'/(algos|results|engines)/', val)
        if m:
            rel = val[val.index(m.group())+1:]
            return f'p("{rel}")'
        return repr(val)

    lines.append(f'        "script": {to_p(script)}, "csv": {to_p(csv)}, "alt_csv": {to_p(alt_csv)}, "chart": {to_p(chart)}, "alt_chart": {to_p(alt_chart)},')

    if c.get("alt_timeframe"):
        lines.append(f'        "alt_timeframe": {repr(c["alt_timeframe"])}, "alt_period": {repr(c.get("alt_period",""))},')

    lines.append('    },')

lines.append(']')
lines.append('')

content = '\n'.join(lines)
with open('algo_configs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Wrote algo_configs.py ({len(content):,} bytes)")
