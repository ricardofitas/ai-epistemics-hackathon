"""Explicit source adapters for generative choice evaluation, before inference.

This is a proposed research correction, not a change to official benchmark code.
It refuses unavailable gold, preserves the correct option through permutations,
and keeps typed references separate from heuristic answer-text extraction.
"""
import hashlib
import json
import string


class UnscorableSource(ValueError):
    pass


def normalize_record(bench, row, row_id, permute=False):
    if bench == 'sciq':
        choices = [row[k] for k in ('correct_answer','distractor1','distractor2','distractor3')]
        gold = 0
    elif bench == 'winogrande':
        choices = [row['option1'],row['option2']]
        label = str(row['answer']).strip()
        if label not in ('1','2'):
            raise UnscorableSource('unavailable_or_invalid_one_based_gold')
        gold = int(label)-1
    elif bench == 'boolq':
        if type(row['answer']) is not bool:
            raise UnscorableSource('expected_boolean_gold')
        choices=['true','false'];gold=0 if row['answer'] else 1
    elif bench == 'pubmedqa':
        choices=['yes','no','maybe']
        if row['final_decision'] not in choices:
            raise UnscorableSource('invalid_decision_gold')
        gold=choices.index(row['final_decision'])
    elif bench == 'medmcqa':
        choices=[row[k] for k in ('opa','opb','opc','opd')]
        gold=int(row['cop'])
    elif bench == 'hellaswag':
        choices=list(row['endings']);gold=int(row['label'])
    elif bench == 'piqa':
        choices=[row['sol1'],row['sol2']];gold=int(row['label'])
    elif bench == 'lab-bench-language-agent-biology-benchmark':
        choices=[row['ideal'],*row['distractors']];gold=0
    else:
        raise UnscorableSource('no_explicit_source_contract')
    if not 2 <= len(choices) <= 26 or not 0 <= gold < len(choices):
        raise UnscorableSource('invalid_choice_count_or_label_range')
    if not all(isinstance(x,str) and x.strip() for x in choices):
        raise UnscorableSource('empty_or_nontext_choice')
    order=list(range(len(choices)))
    if permute:
        order.sort(key=lambda index:hashlib.sha256(
            ('source-contract-fix-20261113|'+str(row_id)+'|'+str(index)).encode()).digest())
    mapped=[choices[index] for index in order]
    gold_index=order.index(gold)
    normalized={**row,'choices':mapped,
                'choices_text':'\n'.join(chr(65+i)+'. '+text for i,text in enumerate(mapped)),
                '_contract_reference':'<answer>'+chr(65+gold_index)+'</answer>',
                '_contract_gold_text':choices[gold],
                '_contract_source_choice_order':order}
    assert normalized['choices'][gold_index]==choices[gold]
    return normalized


def evaluation_contract():
    return {'score_source':'typed_source_contract_research_correction',
            'official_metric':'generative_choice_accuracy_not_loglikelihood_acc_norm',
            'primary_metric':'choice_accuracy','prediction_mode':'generation','denominator':'total',
            'parser':{'type':'choice_letter','choices':None,'choices_key':'choices'},
            'failure_policy':{'parse_failed':'score_zero','empty_output':'score_zero','invalid_reference':'exclude'}}


def render_typed_prompt(source_row, normalized_row, key_mapping, template):
    question_key=key_mapping['input_question_key']
    if question_key not in source_row:
        raise UnscorableSource('missing_question_field')
    context_key=key_mapping.get('input_context_key')
    fields={'question':source_row[question_key],
            'context':source_row.get(context_key,'') if context_key else '',
            **normalized_row,**source_row,
            'choices':normalized_row['choices'],
            'choices_text':normalized_row['choices_text']}
    requested=[name for _,name,_,_ in string.Formatter().parse(template) if name is not None]
    if any(name not in fields for name in requested):
        raise UnscorableSource('unbound_template_field')
    # Source values are substituted once, not interpreted as nested templates.
    return template.format_map(fields)
