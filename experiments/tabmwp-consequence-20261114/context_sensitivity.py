"""Retrospective context interpretation sensitivity; never human gold."""
from pathlib import Path
from decimal import Decimal, InvalidOperation
from collections import Counter
import json,re
from analyze import norm,independent_similarity,BASE_T,BASE_U
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent/'upstream'
def amount(x):
    text=norm(str(x)).replace(',','')
    if not re.fullmatch(r'[$€£]?\s*[-+]?\d+(?:\.\d+)?',text):return None
    try:return Decimal(re.sub(r'[$€£\s]','',text))
    except InvalidOperation:return None
def table_rows(item):
    lines=[line.split('|') for line in item['table'].splitlines()]
    if not lines or any(len(row)!=2 for row in lines):return []
    return [(norm(row[0]),amount(row[1])) for row in lines[1:]]
def decode(item,output):
    val=amount(output)
    if val is None:return None
    rows=table_rows(item)
    opts=item['choices']
    labels={norm(o):o for o in opts}
    indexed={label:[v for k,v in rows if k==label] for label in labels}
    if all(len(v)==1 and v[0] is not None for v in indexed.values()):
        hit=[label for label,values in indexed.items() if values[0]==val]
        if len(hit)==1:return dict(option=labels[hit[0]],method='unique_table_value_to_offered_row')
    q=norm(item['question'])
    match=re.fullmatch(r'.+ has \$(?P<budget>[\d,.]+)\. does (?:he|she|[a-z]+) have enough to buy (?P<items>.+)\?',q)
    if match and set(labels)=={'yes','no'}:
        fragment=match['items']; found=[]
        for label,price in rows:
            if price is None:continue
            hits=list(re.finditer(r'(?<!\w)'+re.escape(label)+r'(?!\w)',fragment))
            if len(hits)==1:found.append((label,price,hits[0].span()))
        if len(found)==2:
            spans=sorted(x[2] for x in found)
            if spans[0][1]>spans[1][0]:return None
            remaining=fragment
            for start,end in sorted(spans,reverse=True):remaining=remaining[:start]+remaining[end:]
            if set(re.findall(r'\w+',remaining))<={'a','an','and','pair','of'}:
                total=sum(x[1] for x in found)
                if val==total:
                    choice='yes' if total<=amount(match['budget']) else 'no'
                    return dict(option=labels[choice],method='returned_exact_total_of_two_requested_items')
    return None
def main():
    source=json.loads((ROOT/'data/tabmwp/problems_test.json').read_bytes())
    summary={};witnesses=[]
    for path in [BASE_T,BASE_U]:
        archive=json.loads((ROOT/path).read_bytes()); c=Counter()
        for pid,row in archive['results'].items():
            item=source[pid];opts=item['choices']
            if not opts or max(independent_similarity(o,row['output']) for o in opts)>0:continue
            if sum(norm(o)==norm(row['output']) for o in opts)==1:continue
            decoded=decode(item,row['output'])
            if decoded is None:continue
            correct=norm(decoded['option'])==norm(item['answer'])
            c['resolved']+=1;c['correct']+=correct;c[decoded['method']]+=1
            witnesses.append(dict(archive=path,id=pid,question=item['question'],table=item['table'],choices=opts,
                                  raw=row['output'],interpretation=decoded,source_answer=item['answer'],interpretation_correct=correct))
        summary[path]=dict(c)
    primary=json.loads((HERE/'results/results.json').read_bytes())['scores']
    scores={path:primary[path]['correct']['residual_zero']+summary[path].get('correct',0) for path in [BASE_T,BASE_U]}
    result=dict(scope='Exploratory secondary context interpretation; source-aware arithmetic, no human or model adjudication. Frozen primary scores unchanged.',
                summary=summary,correct_if_other_residuals_zero=scores,
                difference=scores[BASE_T]-scores[BASE_U],human_labels=0,model_calls=0)
    (HERE/'results/context-sensitivity.json').write_text(json.dumps(result,indent=2)+'\n')
    (HERE/'results/context-witnesses.json').write_text(json.dumps(witnesses,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()

