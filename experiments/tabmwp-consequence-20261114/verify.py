"""Separate arithmetic and witness check; not a human or external review."""
from pathlib import Path
from decimal import Decimal
import hashlib,json,platform,sys
import numpy

HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'results/results.json').read_bytes())
prior=HERE.parent/'upstream'
manifest=json.loads((HERE/'acquisition.json').read_bytes())
checks=0
for path,expected in manifest['blobs'].items():
    raw=(prior/path).read_bytes()
    assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==expected
    checks+=1
base=data['pairs']['primary_base'];head=data['pairs']['released_headline_seed']
# Independent integer decompositions from authenticated archive totals and counts.
assert base['differences']['original']==1209-1119==90
assert base['differences']['explicit_only']==1209+65-70-(1119+4-4)==85
assert base['differences']['residual_zero']==(1209-443+88)-(1119-29+4)==-240
assert base['difference_bounds_residual_unknown']==[854-1094-81+1,854+971-1094-1]
assert head['differences']['original']==5397-4882==515
assert head['differences']['residual_zero']==(5397-3)-(4882-184)==696
assert head['difference_bounds_residual_unknown']==[5394-4698-402+1,5394+14-4698-1]
checks+=7
permutations=json.loads((HERE/'results/permutations.json').read_bytes())
assert [x['seed'] for x in permutations]==list(range(256))
for name,pair in data['pairs'].items():
    deltas=[x['correct'][pair['a']]-x['correct'][pair['b']] for x in permutations]
    expected=pair['common_permutations_256']
    assert (min(deltas),max(deltas),sum(v>0 for v in deltas),sum(v<0 for v in deltas))==(
        expected['min'],expected['max'],expected['a_better'],expected['b_better'])
    checks+=1
source=json.loads((prior/'data/tabmwp/problems_test.json').read_bytes())
witnesses=json.loads((HERE/'results/context-witnesses.json').read_bytes())
correct=0
def parse(x):return Decimal(str(x).strip().replace('$','').replace(',',''))
for row in witnesses:
    item=source[row['id']]
    assert row['question']==item['question'] and row['table']==item['table'] and row['choices']==item['choices']
    assert row['interpretation']['method']=='unique_table_value_to_offered_row'
    rows=[line.split('|') for line in item['table'].splitlines()][1:]
    option_map={' '.join(o.casefold().split()):o for o in item['choices']}
    assert len(option_map)==len(item['choices'])
    hits=[option_map[' '.join(label.casefold().split())] for label,value in rows
          if parse(value)==parse(row['raw']) and ' '.join(label.casefold().split()) in option_map]
    assert hits==[row['interpretation']['option']]
    same=row['interpretation']['option'].casefold()==item['answer'].casefold()
    assert same==row['interpretation_correct']
    correct+=same
assert len(witnesses)==291 and correct==88
context=json.loads((HERE/'results/context-sensitivity.json').read_bytes())
assert context['difference']==854+88-1094==-152
checks+=len(witnesses)+1
result=dict(status='PASS',arithmetic_and_source_checks=checks,
            source_files=len(manifest['blobs']),context_witnesses_checked=len(witnesses),
            context_interpretations_matching_gold=correct,
            scope='Separate arithmetic/witness reconciliation by the same assistant. No independent human certification.',
            python=sys.version,numpy=numpy.__version__,platform=platform.platform())
(HERE/'results/verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
