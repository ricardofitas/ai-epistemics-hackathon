from pathlib import Path
import json,collections
P=Path(__file__).resolve().parent
CONDITIONS=('free_form__absent','free_form__A.None','choice__absent','choice__A.None')
COEFF={'instruction_freeform_minus_choice_at_absent':(1,0,-1,0),'instruction_freeform_minus_choice_at_present':(0,1,0,-1),'carrier_absent_minus_present_at_freeform':(1,-1,0,0),'carrier_absent_minus_present_at_choice':(0,0,1,-1),'interaction_instruction_gain_absent_minus_present':(1,-1,-1,1)}
def join(a,b):return 1 if a==b=='correct' else 0 if a==b=='incorrect' else None
def main():
 packet={x['opaque_id']:x for x in json.load(open(P/'packet.json'))};key=json.load(open(P/'key.json'));reviews=[{x['opaque_id']:x for x in json.load(open(P/f'REVIEW_{r}.json'))} for r in ['A','B']]
 assert all(set(r)==set(packet) for r in reviews)
 rows=[]
 for k in key:
  row=dict(k,final_score=None,content_score=None,tag_consensus=None,review_labels=None)
  if k['eligible']:
   a,b=[r[k['opaque_id']] for r in reviews]
   row.update(final_score=join(a['final_label'],b['final_label']),content_score=join(a['content_label'],b['content_label']),tag_consensus=a['tag_format'] if a['tag_format']==b['tag_format'] else None,review_labels=[{f:r[f] for f in ['final_label','content_label','tag_format']} for r in [a,b]])
  rows.append(row)
 models={}
 for model in sorted({x['model'] for x in rows}):
  xs=[x for x in rows if x['model']==model];ids=sorted({x['source_index'] for x in xs});assert len(ids)==20 and len(xs)==80
  lookup={(x['source_index'],x['condition']):x for x in xs};axes={}
  for axis in ['final','content']:
   counts={};effects={}
   for cond in CONDITIONS:
    vs=[lookup[(i,cond)][axis+'_score'] for i in ids];counts[cond]=dict(planned=20,correct=sum(v==1 for v in vs),incorrect=sum(v==0 for v in vs),unknown=sum(v is None for v in vs))
   for name,coeff in COEFF.items():
    lo=hi=0
    for i in ids:
     for cond,c in zip(CONDITIONS,coeff):
      v=lookup[(i,cond)][axis+'_score']
      if v is None:lo+=min(0,c);hi+=max(0,c)
      else:lo+=c*v;hi+=c*v
    effects[name]={'lower':lo/20,'upper':hi/20}
   axes[axis]={'counts':counts,'contrasts':effects}
  tags={cond:dict(collections.Counter(x['tag_consensus'] or 'unknown' for x in xs if x['condition']==cond)) for cond in CONDITIONS}
  credit=[x['trial_id'] for x in xs if x['score']==1 and x['final_score']==0]
  anycontent=[x['trial_id'] for x in xs if x['content_score']==1 and x['final_score']==0]
  models[model]={'source_cases':20,'axes':axes,'tag_format_counts':tags,'rule_credit_with_incorrect_final':credit,'correct_content_with_incorrect_final':anycontent}
 agreement={field:sum(reviews[0][i][field]==reviews[1][i][field] for i in packet) for field in ['final_label','content_label','tag_format']}
 disagreements=[dict(opaque_id=i,dimension=f,reviewer_a=reviews[0][i][f],reviewer_b=reviews[1][i][f]) for i in packet for f in ['final_label','content_label','tag_format'] if reviews[0][i][f]!=reviews[1][i][f]]
 out=dict(status='complete_assistant_secondary',planned=160,source_questions=20,reviewed=152,capture_unknowns=8,agreement=agreement,disagreements=disagreements,models=models,new_model_api_calls=0,new_judge_api_calls=0,scope='Prespecified secondary assistant adjudication; originalRULEendpointunchanged. Same20sourcecases/model; unknown sensitivity bounds not confidence intervals, human validation or globalcapability.')
 (P/'SECONDARY_CAPTURES.json').write_text(json.dumps(rows,indent=2)+'\n');(P/'SECONDARY_SUMMARY.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
