from __future__ import annotations
import csv, json, sqlite3
from pathlib import Path

ROOT = Path(__import__("sys").argv[1]).resolve() if len(__import__("sys").argv) > 1 else Path(__file__).resolve().parent
catalog = json.loads((ROOT/'metadata/schema_catalog.json').read_text())
GEN = (ROOT/'generate_synthetic_dataset.py').read_text()
import re
m = re.search(r'primary_keys\s*=\s*(\{.*?\})\n', GEN, re.S)
if not m:
    raise RuntimeError('Could not extract primary key catalog')
# This is a Python literal dictionary from the deterministic generator.
import ast
primary_keys = ast.literal_eval(m.group(1))
relations = catalog['relationships']
db_path = ROOT/'sqlite'/'myeconomy_synthetic_demo.sqlite3'
db_path.parent.mkdir(parents=True, exist_ok=True)
if db_path.exists(): db_path.unlink()
conn = sqlite3.connect(db_path)
conn.execute('PRAGMA foreign_keys=ON')
conn.execute('PRAGMA journal_mode=DELETE')
conn.execute('PRAGMA synchronous=FULL')
for table, spec in catalog['tables'].items():
    cols = spec['columns']
    definitions = []
    pk = primary_keys[table]
    for col in cols:
        q = '"' + col.replace('"','""') + '"'
        definitions.append(f'{q} TEXT' + (' NOT NULL' if col == pk else ''))
    definitions.append(f'PRIMARY KEY ("{pk}")')
    for field, target in relations.items():
        child_table, child_col = field.split('.')
        if child_table == table:
            parent_table, parent_col = target.split('.')
            definitions.append(f'FOREIGN KEY ("{child_col}") REFERENCES "{parent_table}"("{parent_col}")')
    conn.execute(f'CREATE TABLE "{table}" ({", ".join(definitions)})')
    csv_path = ROOT/'csv'/f'{table}.csv'
    with csv_path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = [tuple(row.get(col, '') for col in cols) for row in reader]
    if rows:
        names = ','.join('"'+c.replace('"','""')+'"' for c in cols)
        placeholders = ','.join('?' for _ in cols)
        conn.executemany(f'INSERT INTO "{table}" ({names}) VALUES ({placeholders})', rows)
for field,target in relations.items():
    table,col=field.split('.')
    conn.execute(f'CREATE INDEX "idx_{table}_{col}" ON "{table}" ("{col}")')
conn.execute('CREATE TABLE dataset_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
metadata = {
    'dataset_name': 'MyEconomy Synthetic Economic Demo Dataset',
    'version':'1.0.0',
    'synthetic_only':'true',
    'generation_seed':'20261103',
    'as_of_date':'2026-11-03',
    'money_representation':'decimal strings in INR; do not parse into binary floating point',
    'disclaimer':'Fictional fixtures only; no real customers, accounts, providers, payments or benefits.'
}
conn.executemany('INSERT INTO dataset_metadata(key,value) VALUES (?,?)', metadata.items())
conn.commit()
# Verify database invariants.
integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
foreign_errors = conn.execute('PRAGMA foreign_key_check').fetchall()
counts = {table: conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in catalog['tables']}
conn.close()
if integrity != 'ok' or foreign_errors:
    raise SystemExit(f'SQLite integrity failure: {integrity}, fk={foreign_errors[:5]}')
(ROOT/'metadata'/'sqlite_validation.json').write_text(json.dumps({'passed':True,'integrity_check':integrity,'foreign_key_violations':len(foreign_errors),'table_counts':counts,'total_rows':sum(counts.values())},indent=2))
print(json.dumps({'database':str(db_path),'bytes':db_path.stat().st_size,'integrity_check':integrity,'foreign_key_violations':len(foreign_errors),'tables':len(counts),'total_rows':sum(counts.values())},indent=2))
