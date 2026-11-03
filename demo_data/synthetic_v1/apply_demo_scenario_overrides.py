from pathlib import Path
import csv, json, hashlib

ROOT = Path(__import__("sys").argv[1]).resolve() if len(__import__("sys").argv) > 1 else Path(__file__).resolve().parent

def read_rows(name):
    with (ROOT/'csv'/f'{name}.csv').open('r',encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def write_rows(name, rows):
    if not rows: return
    headers=list(rows[0].keys())
    with (ROOT/'csv'/f'{name}.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=headers,lineterminator='\n')
        w.writeheader(); w.writerows(rows)
    (ROOT/'json'/f'{name}.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
    with (ROOT/'jsonl'/f'{name}.jsonl').open('w',encoding='utf-8') as f:
        for row in rows: f.write(json.dumps(row,ensure_ascii=False)+'\n')

# Build a proper five-person, time-consented Commons cohort. These customers are all
# in Jaipur / North Jaipur and have active COMMONS_DEMAND_AGGREGATION consent at 2026-10-20.
cohort = ['CUS00003','CUS00004','CUS00012','CUS00013','CUS00065']
customers = {r['customer_id']:r for r in read_rows('customers')}
consents = {(r['customer_id'],r['purpose']):r for r in read_rows('consents')}
signal_date='2026-10-20'
from datetime import date
for cid in cohort:
    c=customers[cid]
    assert c['city']=='Jaipur' and c['locality_cluster']=='North Jaipur Cluster', (cid,c)
    consent=consents[(cid,'COMMONS_DEMAND_AGGREGATION')]
    assert consent['granted_at']
    granted=date.fromisoformat(consent['granted_at'][:10])
    expiry=date.fromisoformat(consent['expires_at'][:10]) if consent['expires_at'] else None
    revoked=date.fromisoformat(consent['revoked_at'][:10]) if consent['revoked_at'] else None
    assert granted <= date.fromisoformat(signal_date) and (expiry is None or expiry>=date.fromisoformat(signal_date)) and (revoked is None or revoked>date.fromisoformat(signal_date)), cid

signals=read_rows('demand_signals')
# Remove any previous outputs from this deterministic override (idempotent rerun).
signals=[s for s in signals if s['demand_signal_id'] not in {f'DEMO-COM-{i:02d}' for i in range(1,6)}]
new_signals=[]
for i,cid in enumerate(cohort,1):
    new_signals.append({
      'demand_signal_id':f'DEMO-COM-{i:02d}',
      'customer_id':cid,
      'consent_purpose':'COMMONS_DEMAND_AGGREGATION',
      'service_category':'EDUCATION',
      'city':'Jaipur',
      'locality_cluster':'North Jaipur Cluster',
      'quantity_band':'1',
      'price_band_inr':'1500-5000',
      'aggregatable':'True',
      'raw_transaction_data_included':'False',
      'signal_date':signal_date,
      'status':'ACTIVE_FIXTURE',
      'data_class':'SYNTHETIC_FIXTURE'
    })
signals.extend(new_signals)
signals.sort(key=lambda x:x['demand_signal_id'])
write_rows('demand_signals',signals)

participants=read_rows('commons_participants')
participants=[p for p in participants if p['campaign_id']!='CAM00001']
for i,(cid,sig) in enumerate(zip(cohort,new_signals),1):
    participants.append({
      'campaign_participant_id':f'CMP-001-{i:05d}',
      'campaign_id':'CAM00001',
      'customer_id':cid,
      'demand_signal_id':sig['demand_signal_id'],
      'consent_purpose':'COMMONS_DEMAND_AGGREGATION',
      'participation_status':'OPTED_IN_FIXTURE',
      'individual_data_disclosed_to_provider':'False',
      'data_class':'SYNTHETIC_FIXTURE'
    })
participants.sort(key=lambda x:x['campaign_participant_id'])
write_rows('commons_participants',participants)

campaigns=read_rows('commons_campaigns')
for c in campaigns:
    if c['campaign_id']=='CAM00001':
        c.update({
          'campaign_title':'Demo Collective Education Opportunity - Quorum Reached',
          'service_category':'EDUCATION','city':'Jaipur','locality_cluster':'North Jaipur Cluster',
          'minimum_participants':'5','participant_count_fixture':'5',
          'campaign_status':'QUORUM_REACHED_SIMULATION','linked_offer_id':'OFF00004',
          'funding_source':'SIMULATED_PROVIDER_SPONSOR','aggregate_only':'True',
          'individual_income_or_transactions_exposed':'False','data_class':'SYNTHETIC_FIXTURE'
        })
    elif c['campaign_id'] in {'CAM00002','CAM00004','CAM00005','CAM00006'}:
        # No matching city/category offer has been created. Keep these as honest
        # demand-gathering campaigns without a fabricated provider quote.
        c['linked_offer_id']=''
        c['funding_source']='NO_PROVIDER_OFFER_YET'
    elif c['campaign_id']=='CAM00003':
        c['campaign_status']='GATHERING_DEMAND_SIMULATION'
        c['linked_offer_id']='OFF00030'
        c['funding_source']='SIMULATED_PROVIDER_SPONSOR_CANDIDATE_NOT_YET_QUALIFIED'
write_rows('commons_campaigns',campaigns)

scenario_path=ROOT/'api_scenarios'/'03_collective_commons.json'
scenario=json.loads(scenario_path.read_text(encoding='utf-8'))
scenario['campaign'].update({
  'campaign_title':'Demo Collective Education Opportunity - Quorum Reached',
  'service_category':'EDUCATION','city':'Jaipur','locality_cluster':'North Jaipur Cluster',
  'minimum_participants':5,'participant_count_fixture':5,
  'campaign_status':'QUORUM_REACHED_SIMULATION','linked_offer_id':'OFF00004',
  'funding_source':'SIMULATED_PROVIDER_SPONSOR','participant_customer_ids':cohort,
  'participant_demand_signal_ids':[x['demand_signal_id'] for x in new_signals],
  'aggregate_only':True,'individual_income_or_transactions_exposed':False,
  'data_class':'SYNTHETIC_FIXTURE'
})
scenario['expected_safety']='Five synthetic participants have active purpose-specific Commons consent at signal time. Only service category, city/locality cluster, quantity band and price band are aggregatable. Individual identity, income and transactions are never shown to the provider. The linked offer and sponsor are simulated; no quote or fulfilment is real.'
scenario_path.write_text(json.dumps(scenario,indent=2,ensure_ascii=False),encoding='utf-8')

# Keep schema row counts in sync with the overridden CSV exports.
catalog=json.loads((ROOT/'metadata'/'schema_catalog.json').read_text(encoding='utf-8'))
for t in ('demand_signals','commons_participants','commons_campaigns'):
    catalog['tables'][t]['row_count']=len(read_rows(t))
(ROOT/'metadata'/'schema_catalog.json').write_text(json.dumps(catalog,indent=2),encoding='utf-8')

# Keep PostgreSQL seed data coherent: regenerate INSERTs only for the changed Commons
# tables while preserving the original schema and all other fixtures.
seed_path=ROOT/'sql'/'seed.sql'
seed=seed_path.read_text(encoding='utf-8')
# Strip any previous generated override block so reruns stay idempotent.
marker='COMMIT;'
if '-- Deterministic demo-scenario override:' in seed:
    seed=seed.split('-- Deterministic demo-scenario override:',1)[0] + marker
# Existing base seed closes with COMMIT; insert deterministic override SQL before it.
if seed.count(marker)!=1: raise RuntimeError('Expected one COMMIT in seed.sql')
override_sql=[]
override_sql.append('-- Deterministic demo-scenario override: create a five-person consented Commons quorum.\n')
override_sql.append('DELETE FROM "commons_participants" WHERE "campaign_id" = \'CAM00001\';\n')
for row in new_signals:
    cols=list(row)
    vals=[]
    for v in row.values():
        if v is None or v=='': vals.append('NULL')
        elif v in ('True','False'): vals.append('TRUE' if v=='True' else 'FALSE')
        else: vals.append("'"+str(v).replace("'","''")+"'")
    override_sql.append(f'INSERT INTO "demand_signals" ({", ".join(chr(34)+c+chr(34) for c in cols)}) VALUES ({", ".join(vals)});\n')
for row in [p for p in participants if p['campaign_id']=='CAM00001']:
    cols=list(row); vals=[]
    for v in row.values():
        if v is None or v=='': vals.append('NULL')
        elif v in ('True','False'): vals.append('TRUE' if v=='True' else 'FALSE')
        else: vals.append("'"+str(v).replace("'","''")+"'")
    override_sql.append(f'INSERT INTO "commons_participants" ({", ".join(chr(34)+c+chr(34) for c in cols)}) VALUES ({", ".join(vals)});\n')
override_sql.append("UPDATE \"commons_campaigns\" SET \"campaign_title\"='Demo Collective Education Opportunity - Quorum Reached', \"service_category\"='EDUCATION', \"city\"='Jaipur', \"locality_cluster\"='North Jaipur Cluster', \"minimum_participants\"=5, \"participant_count_fixture\"=5, \"campaign_status\"='QUORUM_REACHED_SIMULATION', \"linked_offer_id\"='OFF00004', \"funding_source\"='SIMULATED_PROVIDER_SPONSOR' WHERE \"campaign_id\"='CAM00001';\n")
override_sql.append("UPDATE \"commons_campaigns\" SET \"linked_offer_id\"='OFF00030', \"funding_source\"='SIMULATED_PROVIDER_SPONSOR_CANDIDATE_NOT_YET_QUALIFIED' WHERE \"campaign_id\"='CAM00003';\n")
for cid in ['CAM00002','CAM00004','CAM00005','CAM00006']:
    override_sql.append(f"UPDATE \"commons_campaigns\" SET \"linked_offer_id\"=NULL, \"funding_source\"='NO_PROVIDER_OFFER_YET' WHERE \"campaign_id\"='{cid}';\n")
seed=seed.replace(marker,''.join(override_sql)+marker)
seed_path.write_text(seed,encoding='utf-8')

# Extend the multimodal manifest with the rendered PNG equivalents.
mm_path=ROOT/'metadata'/'multimodal_document_manifest.json'
mm=json.loads(mm_path.read_text(encoding='utf-8'))
for doc in mm:
    pdf_name=Path(doc['pdf_path']).stem
    candidates=list((ROOT/'source_documents'/'invoices_png').glob(pdf_name+'*.png'))
    if candidates:
        png=candidates[0]
        doc['png_path']=str(png.relative_to(ROOT))
        doc['png_sha256']=hashlib.sha256(png.read_bytes()).hexdigest()
mm_path.write_text(json.dumps(mm,indent=2),encoding='utf-8')

print(json.dumps({'new_signals':len(new_signals),'campaign_participants':len([x for x in participants if x['campaign_id']=='CAM00001']),'quorum_campaign':next(x for x in campaigns if x['campaign_id']=='CAM00001')},indent=2))
