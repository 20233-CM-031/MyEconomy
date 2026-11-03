from __future__ import annotations
import csv, hashlib, json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.units import mm

import sys
root=Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
def read_csv(name):
    with (root/'csv'/f'{name}.csv').open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
bills=read_csv('bills'); lines=read_csv('bill_line_items'); providers={p['provider_id']:p for p in read_csv('providers')}
# Balanced examples: normal + each anomaly type, across distinct bill ids.
selected=[]
for anomaly in ['POSSIBLE_DUPLICATE_LINE_ITEM','UNEXPECTED_FEE','PRICE_SPIKE_VS_PRIOR_PERIOD','NONE']:
    selected.extend([b for b in bills if b['anomaly_label']==anomaly][:3])
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='SyntheticBanner',parent=styles['Normal'],fontName='Helvetica-Bold',fontSize=10,leading=13,textColor=colors.HexColor('#7A3E00'),backColor=colors.HexColor('#FFF2CC'),borderColor=colors.HexColor('#D69E2E'),borderWidth=1,borderPadding=8,spaceAfter=12))
styles.add(ParagraphStyle(name='Right',parent=styles['Normal'],alignment=TA_RIGHT))
manifest=[]
for b in selected:
    bid=b['bill_id']; p=providers[b['provider_id']]
    filename=f'{bid}_synthetic_invoice.pdf'; pdf=root/'source_documents'/'invoices_pdf'/filename
    doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=16*mm,bottomMargin=16*mm)
    story=[]
    story.append(Paragraph('SYNTHETIC DEMO DOCUMENT - NOT A REAL CUSTOMER BILL OR PAYMENT REQUEST',styles['SyntheticBanner']))
    story.append(Paragraph('UTILITY / SERVICE STATEMENT',styles['Title']))
    story.append(Paragraph(f"<b>Demo supplier:</b> {p['provider_name']}<br/><b>Provider reference:</b> {p['provider_id']}<br/><b>Customer fixture:</b> {b['customer_id']}",styles['BodyText']))
    story.append(Spacer(1,8*mm))
    story.append(Paragraph(f"<b>Invoice:</b> {b['invoice_number']}<br/><b>Issue date:</b> {b['issue_date']}<br/><b>Due date:</b> {b['due_date']}<br/><b>Bill type:</b> {b['bill_type']}",styles['BodyText']))
    story.append(Spacer(1,6*mm))
    rows=[['Description','Qty','Unit price (INR)','Line total (INR)']]
    for line in [x for x in lines if x['bill_id']==bid]:
        rows.append([line['description'],'1',line['unit_price_inr'],line['line_total_inr']])
    rows.append(['TOTAL DUE','','',b['total_due_inr']])
    tbl=Table(rows,colWidths=[76*mm,17*mm,42*mm,42*mm],repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCE8F4')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#1F344A')),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold'),
        ('BACKGROUND',(0,-1),(-1,-1),colors.HexColor('#EAF4EA')),
        ('GRID',(0,0),(-1,-1),.4,colors.HexColor('#AAB7C4')),
        ('ALIGN',(1,1),(-1,-1),'RIGHT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),
    ]))
    story += [tbl,Spacer(1,8*mm)]
    story.append(Paragraph(f"<b>Fixture anomaly label:</b> {b['anomaly_label']}<br/><b>Fixture payment status:</b> {b['status']}",styles['BodyText']))
    story.append(Spacer(1,5*mm))
    story.append(Paragraph('All information on this page is generated for testing. This document has no payment authority, does not represent a real provider, and must not be used to request or make payments.',styles['Italic']))
    doc.build(story)
    manifest.append({'bill_id':bid,'customer_id':b['customer_id'],'anomaly_label':b['anomaly_label'],'pdf_path':str(pdf.relative_to(root)),'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),'html_path':b['source_document_path'],'synthetic':True})
(root/'metadata'/'multimodal_document_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({'created_pdfs':len(manifest),'types':{a:sum(1 for m in manifest if m['anomaly_label']==a) for a in sorted({m['anomaly_label'] for m in manifest})}},indent=2))
