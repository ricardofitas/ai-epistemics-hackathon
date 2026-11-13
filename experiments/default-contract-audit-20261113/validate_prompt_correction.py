"""Source-value dependency checks for the proposed renderer on all labelled rows."""
import gzip
import json
from pathlib import Path

import audit_contracts as audit
from source_contracts import normalize_record, render_typed_prompt, UnscorableSource

def main():
    gallery=json.loads((audit.ROOT/'GALLERY_SELECTED.json').read_text())
    gallery={b['bench_name']:b for b in gallery['benches']}
    dispositions=json.loads((audit.CAPTURE/'DATASET_DISPOSITIONS.json').read_text())
    reports=[]
    for source in dispositions:
        if source['status']!='captured':continue
        entry=gallery[source['bench']];mapping=entry['meta']['key_mapping']
        template=entry['meta']['prompt']['user_template']
        rows=[json.loads(x) for x in gzip.decompress((audit.CAPTURE/source['rows_file']).read_bytes()).splitlines()]
        count=0;rejected=0;contexts=0
        for index,row in enumerate(rows):
            try:normalized=normalize_record(source['bench'],row,str(index),permute=True)
            except UnscorableSource:rejected+=1;continue
            prompt=render_typed_prompt(row,normalized,mapping,template)
            q_key=mapping['input_question_key'];question=str(row[q_key])
            assert question in prompt
            changed={**row,q_key:'QUESTION_DEPENDENCY_NONCE_'+str(index)}
            assert render_typed_prompt(changed,normalized,mapping,template)!=prompt
            context_key=mapping.get('input_context_key')
            if context_key and row.get(context_key):
                contexts+=1;assert str(row[context_key]) in prompt
                changed={**row,context_key:'CONTEXT_DEPENDENCY_NONCE_'+str(index)}
                assert render_typed_prompt(changed,normalized,mapping,template)!=prompt
            count+=1
        assert rejected in (0,len(rows))
        reports.append({'bench':source['bench'],'split':source['split'],'source_rows':len(rows),
                        'verified_question_presence_and_dependency_rows':count,
                        'verified_nonempty_context_presence_and_dependency_rows':contexts,
                        'rejected_before_inference_rows':rejected})
    report={'method':'Proposed single-pass source-field binding; all required question and nonempty context values preserved and causally influence the prompt. Unlabelled source rejected before inference.',
            'rows':reports,'verified_labelled_rows':sum(x['verified_question_presence_and_dependency_rows'] for x in reports)}
    audit.dump(audit.ROOT/'results/PROMPT_CORRECTION_VALIDATION.json',report)
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
