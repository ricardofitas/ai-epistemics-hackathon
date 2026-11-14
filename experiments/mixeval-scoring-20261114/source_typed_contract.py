"""Research typed contract with exact-source-alias acceptance before rule grading."""
import typed_contract as original
def describe(record,split):
 d=original.describe(record,split)
 if split=='free_form':d.update(parser='source_exact_alias_then_mixeval_rule_freeform',scoring_implementation='source-exact-alias guard plus original MixEval rule functions',official_rule_unmodified=False)
 return d
generate_prompt=original.generate_prompt
def evaluate(record,response,split):
 prior=original.evaluate(record,response,split)
 exact=split=='free_form' and any(response.strip().casefold()==str(a).strip().casefold() for a in record['target'])
 return {**prior,'score':1 if exact else prior['score'],'source_exact_alias':exact,'original_official_rule_score':prior['score'],'changed':bool(exact and prior['score']!=1)}
