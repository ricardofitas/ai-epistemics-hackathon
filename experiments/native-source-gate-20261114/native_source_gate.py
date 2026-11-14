"""Experimental source registry -> actual native request snapshot -> counting sink gate."""
import hashlib,json,copy
canonical=lambda v:json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
sha=lambda v:hashlib.sha256(canonical(v)).hexdigest()
class Blocked(ValueError):
 def __init__(self,report):self.report=report;super().__init__(report['status'])
class SourceGate:
 def __init__(self,registry):self._registry=copy.deepcopy(registry)
 def dispatch(self,key,instances,reference,sink):
  # Only these primitive immutable values are dispatched, never mutable Instance objects.
  frozen=tuple((r.request_type,int(r.doc_id),int(r.idx),str(r.args[0]),str(r.args[1])) for r in instances)
  report=dict(status='PASS',failures=[],source_key=key,snapshot_sha256=sha(frozen),option_requests=len(frozen))
  anchor=self._registry.get(key)
  if anchor is None:report['status']='INCOMPLETE';report['failures']=['trusted_source_unavailable'];raise Blocked(report)
  source=anchor['record'];expected_hash=anchor['source_sha256'];task=anchor['task'];opts=source['choices']['text'];labels=list(map(str,source['choices']['label']));gold=labels.index(str(source['answerKey']));question=source['question'] if task=='arc_challenge' else source['question_stem']
  for r in instances:
   if sha(r.doc)!=expected_hash:report['failures'].append('native_document_differs_from_trusted_source')
  if len(frozen)!=len(opts):report['failures'].append('option_count_changed')
  if [r[2] for r in frozen]!=list(range(len(opts))):report['failures'].append('option_indices_changed')
  if any(r[0]!='loglikelihood' for r in frozen):report['failures'].append('request_type_changed')
  if any(r[1]!=anchor['native_doc_id'] for r in frozen):report['failures'].append('document_id_changed')
  if any(question.strip() not in r[3] for r in frozen):report['failures'].append('source_question_missing_from_actual_context')
  if [r[4] for r in frozen]!=[' '+x for x in opts]:report['failures'].append('actual_continuations_differ_from_official_option_order')
  if type(reference) is not int or reference!=gold:report['failures'].append('reference_differs_from_official_gold')
  report['failures']=sorted(set(report['failures']))
  if report['failures']:report['status']='FAIL';raise Blocked(report)
  return report,sink(frozen)
