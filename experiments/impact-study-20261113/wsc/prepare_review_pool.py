#!/usr/bin/env python3
"""Build a source-only, model-output-blind WSC recast audit pool."""
import collections,datetime as dt,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(b):return hashlib.sha256(b).hexdigest()
def dump(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def main():
 raw=(ROOT/'source/train.jsonl').read_bytes()
 assert sha(raw)=='0ffaa3fd8d21e58a0805962565d1619aa4819bc3d034255777f606f801ae5a42'
 groups=collections.defaultdict(list)
 for line_n,line in enumerate(raw.splitlines(),1):
  r=json.loads(line);t=r['target'];k=(r['text'],t['span2_index'],t['span2_text'])
  groups[k].append({'line_1indexed':line_n,'record':r,'raw_line_utf8':line.decode(),'raw_line_sha256':sha(line)})
 packet=[];pool=[]
 for k,entries in sorted(groups.items(),key=lambda kv:min(e['record']['idx'] for e in kv[1])):
  text,index,pronoun=k;reasons=[]
  if len(entries)!=2 or sum(e['record']['label'] for e in entries)!=1:reasons.append('require_exactly_two_source_candidates_one_true_one_false')
  if pronoun.lower() not in {'he','she','it','they'}:reasons.append('outside_simple_subject_pronoun_filter')
  if len(text.split())>70:reasons.append('more_than70_whitespace_words')
  if not all(re.fullmatch(r'[A-Z][a-z]+(?: [A-Z][a-z]+)*',e['record']['target']['span1_text']) for e in entries):reasons.append('candidate_not_full_titlecase_name_pattern')
  spans=list(re.finditer(r'\S+',text));start=spans[index].start() if 0<=index<len(spans) else None
  if start is None or text[start:start+len(pronoun)]!=pronoun:reasons.append('source_target_offset_not_exactly_reproducible')
  row={'source_indices':[e['record']['idx'] for e in entries],'mechanically_eligible':not reasons,'mechanical_exclusion_reasons':reasons}
  if not reasons:
   gold=next(e for e in entries if e['record']['label']);bad=next(e for e in entries if not e['record']['label'])
   gname=gold['record']['target']['span1_text'];bname=bad['record']['target']['span1_text']
   replace=lambda name:text[:start]+name+text[start+len(pronoun):]
   row['review_id']=f'W{len(packet)+1:03d}'
   packet.append({'review_id':row['review_id'],'source_split':'train','source_text':text,'pronoun':pronoun,'pronoun_token_index':index,'pronoun_char_start':start,'gold_coreference_entity':gname,'non_gold_coreference_entity':bname,'hypothesis_gold_replacement':replace(gname),'hypothesis_non_gold_replacement':replace(bname),'source_gold_record':gold,'source_non_gold_record':bad,'nli_annotation_status':'Not supplied by source. Both source labels concern coreference only. Semantic review must assess recast validity separately.','review_fields':{'usable_literal_binary':None,'gold_replacement_entailment_under_intended_reading':None,'non_gold_replacement_not_entailed':None,'non_gold_compatible_with_premise':None,'three_way_negative_if_confident':None,'reason_or_countermodel':None,'grammar_or_ambiguity_notes':None}})
  pool.append(row)
 b=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in packet).encode()
 target=ROOT/'semantic_review_packet.jsonl'
 if target.exists():assert target.read_bytes()==b
 else:target.write_bytes(b)
 dump(ROOT/'mechanical_pool_manifest.json',{'source_groups':len(groups),'eligible_groups':len(packet),'unique_passages':len({r['source_text'] for r in packet}),'source_train_sha256':sha(raw),'packet_sha256':sha(b),'filters_are_source_only':'Mechanical restrictions improve exact recast grammar; they are not a random/representative WSC sample. No candidate outputs exist or were examined.','all_group_decisions':pool})
 if not (ROOT/'selection_intent.json').exists():
  dump(ROOT/'selection_intent.json',{'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'prospective_before_candidate_predictions','mechanical_pool':len(packet),'semantic_packet_sha256':sha(b),'semantic_review':'Independent first agent checks before candidate inference, with exact source labels/provenance visible but no candidate responses. Human validation pending. Preserve first files and separate adjudication.','semantic_eligibility':'Accept only recasts whose source gold reading supports the positive replacement and whose non-gold full replacement is not entailed. Retain valid contradiction negatives as well as neutral negatives; do not select only compatible negatives to maximize bad-label penalties. Reject grammar corruption, entailed alias cases and unresolved binary validity. Preserve all excluded/uncertain rows.','intended_reading_convention':'Original unresolved source passage is transmitted. Official coreference gold fixes intended reading for analyst binary interpretation, not an official NLI label or a proof all arbitrary readings agree.','desired_size':'Use all source-only semantically eligible passages up to80, deterministically selected before candidate outputs; aim64–80. If fewer than40 valid passages, do not treat as impact-grade execution without a separately reviewed redesign.','maximum_passages':80,'candidate_configurations':['gemma-4-31b-it','glm-5.2','qwen3.8-27b','deepseek-v4-flash'],'no_weight_snapshot_claim':True,'selection_confirmation':'Disjoint source passage/similarity-family clusters assigned50/50 before candidate outputs. Preserve cross-variant dependency and source-cluster bootstrap. No source passage duplicated between selection and confirmation.','primary_comparison':'Same frozen3way predictions scored by literal Q48 positive=entailment/negative=contradiction versus repaired directional-entailment binary scoring where neutral+contradiction=nonentailment. This isolates scoring-rule consequences conditional on fixed predictions, not causal real-user adoption.','secondary_three_way':'Use independently confident analyst C/N labels only as a secondary sensitivity, with ambiguous labels retained/excluded transparently and no official NLI gold claim.','all_pairs':'Report all6pairwise model comparisons and tied rankings. Select unique winning candidate by each rule on selection split; assess repaired binary accuracy difference on disjoint confirmation split. Ties indeterminate, negative/zero differences retained.','no_activation_reuse':'New exploratory Q48 mechanism study; failed historical PAWS gate is unchanged and not reused.','no_inference_made':True})
 print(json.dumps({'packet_rows':len(packet),'unique_source_passages':len({r['source_text'] for r in packet}),'packet_sha256':sha(b)}))
if __name__=='__main__':main()
