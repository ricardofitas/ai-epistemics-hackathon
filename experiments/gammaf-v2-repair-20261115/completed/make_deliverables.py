from pathlib import Path
import hashlib,json,zipfile
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("DVS","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVS-Bold","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFontFamily("DVS",normal="DVS",bold="DVS-Bold",italic="DVS",boldItalic="DVS-Bold")
R=Path(__file__).resolve().parent; O=R/'deliverables';O.mkdir(exist_ok=True)
title='GAMMAF v2: Full-Option Replication Addendum'
authors='Antonio Galasso, Ricardo Fitas, Vittoria Lanzo, Kunal Sharma'
sections=[
('Scope and fixed design', 'This addendum reports a separate, completed full-option replication. It does not replace the original 256-pair experiment, whose prompts omitted option text. Before inference, we fixed 32 previously used questions (14 MMLU, 10 CSQA and 8 MMLU-Pro), two graphs (chain and star), three rounds and two policies: final filtering (FixedTarget-PostHoc) and early intervention (Inline). All 64 paired worlds completed, yielding 128 debates. The question, three insiders, incorrect target and first-round votes matched within every pair. We used Qwen3.8-27B at temperature 0.7. Notifications retained the original simulator knowledge of agent roles.'),
('Paired results', 'With the frozen reader and tally, Inline recovered five correct delivered answers and lost one: 51/64 correct answers became 55/64, a net gain of 6.25 percentage points (pp). The 95% within-task question-cluster bootstrap interval was [-1.56, +15.63] pp, based on 20,000 resamples of 32 questions. The interval does not resolve the direction of the accuracy effect. There were 50 pairs correct under both policies and eight incorrect under both.'),
('Measurement and scope limits', 'The frozen vote reader scans combined reasoning and content, prioritising the first recognised structured field and otherwise the last standalone legal label. Of 2,327 successful provider replies, 919 contained reasoning with no content-channel answer. Among 1,408 replies with nonempty content, 76 yielded different labels when the same reader was applied to content alone. These are channel-sensitivity diagnostics, not regenerated content-only debates: changing earlier votes would also change later prompts. The provider finish status was not retained, so the number of truncated replies cannot be established. The protocol also contains competing answer-format instructions. Results therefore describe the implemented reader and intervention pipeline, rather than a validated final-answer-only evaluation.'),
('Interpretation', 'The repaired panel has a positive accuracy point estimate, unlike the original option-omitting experiment. A categorical claim that early intervention never improves accuracy is therefore unwarranted. The gated switch metric decreased more clearly than accuracy improved; fixed-population target-switch uncertainty still includes zero. The evidence supports reporting both vote-change metrics and delivered correctness, without claiming general accuracy superiority, equivalence, or causal mediation. This is a small, previously exposed panel with one model and role-informed notifications; it is not a held-out multi-model confirmation.'),
('Verification and resources', 'An offline replay reproduced all 128 debates from 3,840 cache lookups without a cache miss or provider request. All 33 frozen files and the downloaded archive hash were verified. There were 2,331 physical attempts, including four transport failures; no planned debate is missing. Reported token usage was zero for every successful reply, so actual token totals and billing remain unknown. The conservative request reservations sum to 3.175870401 nominal units; these are not an observed billed cost.')]
table=[['Outcome (debates)','Final filtering','Inline','Difference, pp (95% CI)'],['Delivered correct','51/64','55/64','+6.25 [-1.56, +15.63]'],['Honest correct-to-target switch, fixed population','12/64','8/64','-6.25 [-14.06, +1.56]'],['Policy-gated target switch','9/64','4/64','-7.81 [-15.63, -1.56]'],['Honest correct-to-any-wrong switch','36/64','26/64','-15.63 [-29.69, -3.13]']]
plain=title+'\n\n'+authors+'\nAI Epistemics Research Team\n16 November 2026\n\n'
for h,t in sections:
 plain+=h+'\n'+t+'\n\n'
plain+='Outcomes (64 paired worlds; 32 question clusters)\n'+'\n'.join(' | '.join(x) for x in table)+'\n\nRun: https://github.com/rfitas-lab/rfdl-lab-os/actions/runs/43759531220\n'
(O/'GAMMAF_v2_full_options_addendum.txt').write_text(plain)
styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodySmall',fontName='DVS',fontSize=9.2,leading=12,spaceAfter=6));styles.add(ParagraphStyle(name='AuthorSmall',fontName='DVS',fontSize=9,leading=12,alignment=TA_CENTER,spaceAfter=8));styles['Title'].fontName='DVS-Bold';styles['Title'].fontSize=16;styles['Title'].leading=19
story=[Paragraph(title,styles['Title']),Paragraph(authors+'<br/>AI Epistemics Research Team | 16 November 2026',styles['AuthorSmall'])]
for i,(h,t) in enumerate(sections):
 story.extend([Paragraph('<b>'+h+'</b>',styles['BodySmall']),Paragraph(t,styles['BodySmall'])])
 if i==1:
  cells=[[Paragraph(c,styles['BodySmall']) for c in row] for row in table]
  tab=Table(cells,colWidths=[204,63,53,165],repeatRows=1)
  tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eef5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#62788f')),('LINEBELOW',(0,-1),(-1,-1),.6,colors.HexColor('#62788f')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
  story.extend([tab,Spacer(1,8)])
story.append(Paragraph('Execution record: github.com/rfitas-lab/rfdl-lab-os/actions/runs/43759531220',styles['BodySmall']))
SimpleDocTemplate(str(O/'GAMMAF_v2_full_options_addendum.pdf'),pagesize=(595.28,841.89),leftMargin=50,rightMargin=50,topMargin=40,bottomMargin=40).build(story)
report='# Completed full-option replication\n\n'+plain+'\n## Manuscript disposition\n\nThe original humanised manuscript remains unchanged. Add this separate addendum rather than rewriting existing sentences. The original title and conclusion must be understood as statements about its explicitly option-omitting experiment; do not silently extend them to full-option prompts. A neutral overall title such as **Recorded Vote Switches and Delivered Answers** is an optional editorial change, not an automatically applied rewrite. Do not combine the 64 repaired pairs with the original 256 pairs for a new pooled significance test. Neither the old nor repaired observational switch counts identify which neighbour caused a change.\n\n## Channel audit\n\nThe 76 content-channel disagreements do not establish semantic accuracy of either parse. They expose dependence on the answer reader. No discarded reply was retried for content quality, no trajectory was replaced and no additional model inference was launched after reviewing outcomes. Explicit finish reasons are absent from the retained response schema; reasoning-only is not labelled a confirmed truncation.\n\n## Provenance\n\nRead the pinned frozen package for all methods and code. Archive parts under `raw/` reconstruct the unmodified GitHub results ZIP (including raw ledger, SQLite cache, outcomes, manifest and receipts). Run `python reconstruct_archive.py` in this directory. `verify_replay.py` and `VERIFICATION.json` record the independent offline checks. The fresh frozen analysis is identical to the uploaded analysis.\n'
(O/'REPORT.md').write_text(report)
reconstruct="from pathlib import Path\nimport hashlib\np=Path(__file__).resolve().parent\nb=b''.join(x.read_bytes() for x in sorted((p/'raw').glob('results.zip.part*')))\nassert hashlib.sha256(b).hexdigest()=='b1a4a40ea417a0faff8578cfe2cdbebc3f660516e1fb69ace580b807a1ad8bad'\n(p/'results.zip').write_bytes(b)\nprint('Verified results.zip written')\n"
(O/'reconstruct_archive.py').write_text(reconstruct)
with zipfile.ZipFile(O/'GAMMAF_v2_full_options_verified_bundle.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in [O/'GAMMAF_v2_full_options_addendum.pdf',O/'GAMMAF_v2_full_options_addendum.txt',O/'REPORT.md',R/'verify_replay.py',R/'audit/VERIFICATION.json',R/'audit/repaired_fixed_population_analysis.json',R/'results.zip']:
  z.write(p,p.name)
print(json.dumps({'deliverables':{p.name:p.stat().st_size for p in O.iterdir()}},indent=2))
