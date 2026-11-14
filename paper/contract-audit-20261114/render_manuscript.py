"""Render the structured private research manuscript using ReportLab."""
import json,html
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,PageBreak,Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("BodySerif","/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Sans","/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("SansBold","/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"))
P=Path(__file__).resolve().parent
pages=json.loads((P/'manuscript.json').read_text())
OUTPUT=P/'Epistemics_Contract_Audit_Working_Draft_20261114.pdf'
styles={
'p':ParagraphStyle('body',fontName='BodySerif',fontSize=10.2,leading=13.2,spaceAfter=6),
'heading':ParagraphStyle('head',fontName='SansBold',fontSize=11.4,leading=14,spaceBefore=7,spaceAfter=5,textColor=colors.HexColor('#17324D')),
'small':ParagraphStyle('small',fontName='BodySerif',fontSize=8.3,leading=10.8,spaceAfter=5,splitLongWords=True),
'meta':ParagraphStyle('meta',fontName='Sans',fontSize=8.4,leading=11,textColor=colors.HexColor('#657487'),spaceAfter=10),
'title':ParagraphStyle('title',fontName='SansBold',fontSize=20,leading=24,textColor=colors.HexColor('#17324D'),spaceAfter=8),
'page_title':ParagraphStyle('page_title',fontName='SansBold',fontSize=17,leading=21,textColor=colors.HexColor('#17324D'),spaceAfter=10),
'cell':ParagraphStyle('cell',fontName='Sans',fontSize=8,leading=10.2),
'cell_head':ParagraphStyle('cell_head',fontName='SansBold',fontSize=8,leading=10.2,textColor=colors.white)}
def safe(text):return html.escape(text).replace('&lt;br/&gt;','<br/>')
def foot(canvas,doc):
 canvas.setStrokeColor(colors.HexColor('#D6DFE8'));canvas.line(58,42,537,42)
 canvas.setFillColor(colors.HexColor('#607286'));canvas.setFont('Sans',7.5)
 canvas.drawString(58,29,'Private working manuscript | Evidence synthesis v1.2 | 14 November 2026')
 canvas.drawRightString(537,29,str(doc.page))
story=[]
for i,page in enumerate(pages):
 if i:story.append(PageBreak())
 story.append(Paragraph(safe(page['title']),styles['title' if i==0 else 'page_title']))
 if page.get('subtitle'):story.append(Paragraph(safe(page['subtitle']),styles['heading']))
 for block in page['blocks']:
  kind=block['kind']
  if kind=='table':
   data=[[Paragraph(safe(str(x)),styles['cell_head']) for x in block['headers']]]+[[Paragraph(safe(str(x)),styles['cell']) for x in row] for row in block['rows']]
   t=Table(data,colWidths=block['widths'],repeatRows=1,hAlign='LEFT')
   t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17324D')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F4F7'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#CDD6DF'))]))
   story.extend([Spacer(1,4),t,Spacer(1,9)])
  else:story.append(Paragraph(safe(block['text']),styles[kind]))
doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=58,rightMargin=58,topMargin=45,bottomMargin=55,title='When Evaluation Pipelines Change the Task',author='Private working draft',pageCompression=1)
doc.build(story,onFirstPage=foot,onLaterPages=foot)
print(OUTPUT)

