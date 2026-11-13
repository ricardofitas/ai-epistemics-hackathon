#!/usr/bin/env python3
"""Write the designer's source-only first semantic judgments; no model outputs."""
import json,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parent
# Each note was assessed against the source passage and exact replacement texts,
# with original coreference gold fixing the intended reading, not official NLI gold.
notes={
1:'Pete being credulous does not exclude Mark independently also needing skepticism; Mark skepticism is not asserted.',
2:'Dan compassion does not assert Bill lacks compassion in every respect; both can be compassionate even while Bill toys with the bird.',
3:'The intended biography statement concerns Xenophanes childhood. It does not assert the same statement about Goodman, but a biography may also convey his difficulties.',
4:'Bob is hurt by ingratitude; Charlie can independently also be hurt. Charlie hurt is neither asserted nor denied.',
5:'The stated openness concerns Janie. Emma can also be open without changing the nonpass event; it is not established.',
6:'Charlie ingratitude does not rule out some separate ingratitude by Bob; it does not assert it.',
7:'Sam eagerness explains taking classes. Adam may also be eager to become more fluent, but this is not asserted.',
8:'Sid failing to convince Mark does not exclude Mark also failing to convince Sid; the converse event is not asserted.',
9:'Susan giving Joan help does not exclude Joan also giving Susan help; the reverse thanking explanation is not asserted.',
10:'Beth calming herself does not rule out Sally also stopping and counting; it does not establish that alternate explanation.',
11:'The target it denotes a NAME, not simply the actress as person. Easier is an implicit comparison; the alternate-name causal hypothesis has unresolved comparison scope. Do not infer entailment or contradiction just because both names refer to one person.',
12:'Andrea in the aircraft sees the landing strip. Susan seeing it is compatible but not stated.',
13:'The intended winner is Frank. A sole-winner convention would contradict Bill winner, but ties/shared-winning and competition reference are not formalized; binary nonentailment is safe while three-way label remains uncertain.',
14:'Carl concern does not exclude Bob also being concerned; Bob concern is not established.',
15:'Susan nosiness does not rule out Ann nosiness, but no alternate nosiness explanation is established.',
16:'Martin success can coexist with Pete success; Pete success is not the asserted causal explanation.',
17:'Jane invitation to come out does not exclude a reciprocal invitation from Susan; the latter is not asserted.',
18:'Carol belief about Rebecca regret/theft does not entail Carol belief that Rebecca regrets Carol theft. Both belief contents can coexist; do not project the embedded belief as actual theft.',
19:'Bob generosity does not exclude Charlie generosity in another respect; Charlie generosity is not asserted.',
20:'Dora doing her best alone does not entail Maude doing her best alone. Both may do so at different times; the alternate reference is not established.',
21:'George unavailable does not exclude Paul also becoming unavailable while making/after attempting the call; it does not establish Paul unavailability.',
22:'Under the ordinary fixed comparison, Harry knowing less than Mark does not entail Harry knowing less than Harry; the self-comparison is irreflexively false.',
23:'Tom avoiding driving alone does not entail Ralph avoiding driving alone; both motives can hold.',
24:'Ann forgetting closing time does not exclude Mary forgetting it; Mary forgetting is not established.',
25:'Mama stroking Alice hair does not exclude Alice also stroking someone hair; the alternate action is not asserted. Other unresolved her remains part of the original recast.',
26:'The intended counterfactual is Bob winning absent Adam luck. Adam winning under that same antecedent is not entailed; three-way exclusivity depends on sole-winner/tie conventions.',
27:'Susan nonanswer does not entail Jane nonanswer. Both can fail to answer separate calls/knocks without contradiction.',
28:'Bill leaving after John order does not exclude John also leaving; John leaving is not established.',
29:'Robert refusing the favor does not exclude James also refusing something; the alternate refused-favor proposition is not established.',
30:'The context supplies the comparison of Kirilov and Shatov; Shatov more popular than Kirilov excludes the reverse strict popularity ordering on that same comparison.',
31:'Bob illness does not exclude Carl also being ill, but Carl illness is not stated.',
32:'Ralph avoiding a walk does not entail Tom avoiding a walk; both could otherwise have walked.',
33:'Tom reaching the top before throwing does not exclude Ray also previously reaching the top, then moving down; Ray reaching it is not established.',
34:'Thomson was an alive visitor at Cooper grave. Cooper travelling alive at that same date is inconsistent with the grave/death reading supplied by the passage; no supernatural/metaphorical travel is assumed.',
35:'Ethan being it does not logically exclude Luke also being it under a multiple-it game variant; no game rule says unique it. Luke it is not asserted.',
36:'Eric eagerness does not exclude George eagerness; the alternate causal explanation is not established.',
37:'Pete success does not exclude Martin success, and Martin success is not asserted by the concessive clause.',
38:'Paul failed call does not entail George failed attempt/call; both can fail without contradiction.',
39:'Jane disappointment does not exclude Susan disappointment; the alternate state is not asserted.',
40:'Tom selling a broken toaster to Frank does not exclude a prior/reverse sale involving Frank and Tom. The alternate sale/explanation is not established.',
41:'Thomson is an alive visitor to Cooper grave at the given date; Thomson already dead for five years contradicts that ordinary literal reading.',
42:'Jane not getting an answer does not entail Susan not getting one; both can have unanswered interactions.',
43:'The intended comparison is Kirilov less popular than Shatov. Reversing that same strict popularity comparison is incompatible.',
44:'John leaving after promising Bill does not exclude Bill also leaving; the latter is not established.',
45:'The intended research difficulties are Goodman own. The biography could also convey Xenophanes research difficulties, but that is not asserted here.',
46:'Susan invitation to come in does not exclude Jane issuing a reciprocal invitation in another interaction; Jane invitation is not established.',
47:'Ann telling Susan does not exclude Susan telling Ann too; the reverse information event is not entailed.',
48:'Alice good luck does not exclude Jade good luck; Jade luck is not established as this causal explanation.',
49:'Adam being known fluent does not exclude Sam being known fluent and seeking improvement; it does not assert that knowledge about Sam.',
50:'Emma seeing Janie open does not entail Janie seeing the relevant openness. Both perceptions can hold; other she must retain the source intended reference.',
51:'James being refused does not entail Robert being refused; both can be refused in reciprocal requests.',
52:'Fred influence does not exclude Steve influence too; the reverse influence is not established.',
53:'Too hard predicates a NAME token in a name-change explanation. Alternate-name hypothesis has unresolved causal/comparison threshold scope; require exclusion from strong binary gold rather than treating names as interchangeable person aliases.',
54:'The counterfactual gone has an implicit departure location. Replacing Adam by Bob can shift gone from work to home, where the antecedent itself says Bob left. Literal binary gold is uncertain without an explicit location repair, so exclude.',
55:'George eagerness does not exclude Eric eagerness; the alternate concessive proposition is not established.',
56:'Lucy studying hard does not exclude Anna also studying hard; Anna study effort is not established as this causal explanation.',
57:'Bill is intended winner. Frank winner is not established; a sole-winner assumption suggests contradiction but ties/competition reference leave the three-way distinction uncertain.',
58:'Ann indiscretion does not exclude Susan indiscretion, but Susan indiscretion is not asserted as this explanation.',
59:'Luke it does not entail Ethan it; multiple-it variants make compatibility possible without entailing Ethan it.',
60:'Jade red turban does not exclude Alice also having one, but Alice turban is not asserted.',
61:'Kevin upset does not exclude Jim upset; Jim upset is not established.',
62:'Bill cruelty does not exclude Dan cruelty in another context; Dan cruelty is not established.',
63:'Carol belief about Rebecca suspicion of Carol theft does not entail the corresponding belief/suspicion of Rebecca theft. The embedded suspicion must not be projected as an actual theft.',
64:'Mary forgetting closing time does not exclude Ann forgetting it; Ann forgetting is not established.',
65:'Ray reaching the bottom does not exclude Tom also reaching a lower location earlier/later; the alternate temporal/action proposition is not established.',
66:'In this fixed comparison Jackson lived two centuries after Arnold; the reverse chronology is incompatible with that same pair and reference period.',
67:'Susan out does not exclude Jane being outside; Jane already at the door can be outside without it establishing the same out/not-home sense. This is a lexical ambiguity, so preserve a secondary three-way uncertainty; binary does not entail Jane away from her own location.',
68:'Susan telling Ann does not exclude Ann also telling Susan; the reverse information event is not established.',
69:'Adam already here in the actual context does not force Adam still here in the counterfactual where Bob arrived earlier; Adam could leave once replaced. The non-gold conditional is not entailed.',
70:'Jim upset does not exclude Kevin upset; Kevin upset is not established.',
71:'Sally bad start can coexist with Sue bad start while Sue still wins; the alternate causal claim is not established.',
72:'Adam would lose absent luck; Bob losing under the same counterfactual is not entailed. Exclusive-winner assumptions affect the secondary three-way label.',
73:'Steve admiration does not exclude Fred also admiring Steve; the reverse admiration is not established.',
74:'Mark needing truthfulness does not exclude Pete also needing truthfulness for independent dishonesty; Pete truthfulness obligation is not established. This is the already used discovery witness and must remain unsampled.',
75:'John shortness does not exclude Billy also being short while blocking the view; Billy shortness is not established.',
76:'Sue good start does not exclude Sally also having a good start, with Sue better overall; the alternate causal explanation is not established.',
77:'Mark hearing Steve leave does not entail Steve running to look out of a window. Steve could later run to another window without contradicting the sequence.',
78:'Susan seeing landing gear does not entail Andrea seeing it. Andrea could see it using a mirror/camera; that compatible extra fact is not asserted.',
79:'Anna studying hard does not exclude Lucy also studying hard; Lucy study effort is not established.',
80:'Arnold lived two centuries before Jackson in the intended fixed comparison; Jackson two centuries before Arnold reverses that same chronology and is incompatible.',
81:'Sally apology does not exclude Beth also apologizing; Beth apology is not established as the reason.'}
uncertain={11,53,54}
contrad={22,30,34,41,43,66,80}
secondary_uncertain={13,26,35,57,59,67,72}
rows=[]
for source in map(json.loads,(P/'semantic_review_packet.jsonl').read_text().splitlines()):
 n=int(source['review_id'][1:]);u=n in uncertain
 row={'review_id':source['review_id'],'reviewer_id':'semantic_first_a_designer','usable_literal_binary':'uncertain' if u else 'yes','positive_entailment':'uncertain' if u else 'yes','negative_not_entailed':'uncertain' if u else 'yes','negative_compatible':'uncertain' if u or n in secondary_uncertain else ('no' if n in contrad else 'yes'),'negative_three_way':'uncertain' if u or n in secondary_uncertain else ('contradiction' if n in contrad else 'neutral'),'rationale':notes[n],'ambiguity_notes':'Official coreference fixes intended reading; full natural-language premise remains pragmatically interpreted. Source supplies no NLI gold.','discovery_family_unsampled':n in {1,74}}
 rows.append(row)
target=P/'semantic_first_a.jsonl'
assert not target.exists()
target.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows));target.chmod(0o444)
print(json.dumps({'rows':len(rows),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'frozen_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'yes':len(rows)-len(uncertain),'uncertain':len(uncertain)}))
