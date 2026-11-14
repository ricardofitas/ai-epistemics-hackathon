#!/usr/bin/env python3
"""Independent, offline numeric-carrier audit. Standard library; no study imports.

Usage: python verify.py ARTIFACT_ROOT SOURCE_CODE_DIR --output audit.json
       python verify.py --self-test
Optional --main-root ROOT (repeatable) links parent-arm observations on the same
24 source IDs, retaining missing observations as unknown. No network operations.
"""
import argparse
import collections
import datetime
import decimal
import gzip
import hashlib
import json
from pathlib import Path
import re
from fractions import Fraction
import tempfile
import unittest

MODELS = ['gemma-4-31b-it', 'qwen3.8-27b', 'deepseek-v4-flash', 'glm-5.2']
MAIN_ARMS = ['free_clear', 'free_none', 'choice_clear', 'choice_none']
RATES = {m: tuple(map(decimal.Decimal, r)) for m, r in zip(MODELS,
    [('.09', '.34'), ('.039', '1.25'), ('.045', '.14'), ('1.40', '4.40')])}
CASES_SHA = '4ba78cd09309ac6b0793a44d449e8158a96c9605be0daed55d6514e27d153815'
EXECUTION_COMMIT = '85ef43089b098d9a8c24c3f055aeb20020d7f939'
NUMBER = r'[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)(?:/\d+)?'


def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(x):
    return hashlib.sha256(x).hexdigest()


def final_answer(text):
    tags = re.findall(r'<answer\b[^>]*>(.*?)</answer\s*>', text, re.I | re.S)
    if tags:
        return tags[-1].strip(), 'tag'
    lines = [s.strip() for s in text.strip().splitlines() if s.strip()]
    if not lines:
        return '', 'empty'
    return re.sub(r'^(?:final answer|answer)\s*:\s*', '', lines[-1], flags=re.I).strip(), 'last_line'


def number(s, unit):
    # Frozen endpoint: do not infer a numerical value from an option label or prose.
    s = s.strip().strip('*').strip().removesuffix('.').strip().replace('−', '-')
    if unit.startswith('$'):
        s = s.removeprefix('$').strip()
    suffix = unit.strip().lstrip('$, ').strip()
    if suffix and s.casefold().endswith(' ' + suffix.casefold()):
        s = s[:-len(suffix)].strip()
    if not re.fullmatch(NUMBER, s):
        return None
    try:
        return Fraction(s.replace(',', ''))
    except (ValueError, ZeroDivisionError):
        return None


def payload(case, model, i, arm='choice_none', value=None):
    parts = ['Answer the source question using its context when relevant.',
             'Give the factual answer to the question in free form.' if arm.startswith('free') else
             'Select the best answer from the provided options.',
             'Question:\n' + case['question'], 'Context:\n' + case['context']]
    if arm.endswith('none'):
        parts.append('Options:\nA. ' + ('None' if value is None else value))
    parts.append('Put your final answer in <answer>...</answer> tags.')
    return dict(model=model, input='\n\n'.join(parts), temperature=0,
                max_output_tokens=4096 if i % 4 in (0, 1) else 6144,
                stream=True, tools=[], agentic_memory=False, store=False, tool_choice='none')


def make_plan(cases):
    subset = [(i, r) for i, r in enumerate(cases) if 150 <= i < 200 and r['dataset'] == 'tabmwp']
    if len(subset) != 25:
        raise ValueError('Expected exactly 25 TabMWP cases in indices 150..199')
    subset.sort(key=lambda x: digest(('20261114-numeric-option-v1|' + x[1]['id']).encode()))
    rows = []
    for i, c in subset[:24]:
        truth = c['gold'][0]
        norm = number(truth, c['unit'])
        wrong = str(norm + 1) if '/' in truth else format(decimal.Decimal(truth.replace(',', '').strip('$')) + 1, 'f')
        if norm is None or number(wrong, c['unit']) != norm + 1:
            raise ValueError('Invalid gold+1 construction')
        for mi, m in enumerate(MODELS):
            for arm, value in [('correct', truth), ('wrong', wrong)]:
                p = payload(c, m, i, value=value)
                rows.append(dict(key=f"tab-{c['id']}-{mi}-{arm}", case=i, source_id=c['id'],
                                 model=m, arm=arm, value=value, request_sha=digest(canonical(p)), payload=p))
    rows.sort(key=lambda r: digest(('20261114-option-order|' + r['key']).encode()))
    if len(rows) != 192 or len({r['key'] for r in rows}) != 192 or len({r['request_sha'] for r in rows}) != 192:
        raise ValueError('Nonunique 192-slot design')
    return rows


def source_path(root):
    root = Path(root)
    if root.is_file():
        return root
    for rel in ['cases.json', 'src/cases.json', 'code/cases.json', 'external-contract-transfer-20261114/cases.json']:
        if (root / rel).exists():
            return root / rel
    raise FileNotFoundError('Cannot locate frozen cases.json under source-code directory')


def read_lines(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def output_text(raw):
    text = ''.join(item.get('text', '') for block in raw.get('output', [])
                   if block.get('type') == 'message' for item in block.get('content', [])
                   if item.get('type') == 'output_text')
    text = text or raw.get('output_text') or ''
    return text if isinstance(text, str) else ''


def sanitized_usage(raw):
    u = raw.get('usage') or {}
    if not isinstance(u, dict):
        return {}
    return {k: u[k] for k in ['input_tokens', 'output_tokens', 'total_tokens', 'cost']
            if isinstance(u.get(k), (int, float)) and not isinstance(u[k], bool) and u[k] >= 0}


def eligible(a, raw, text, row):
    return (a.get('http') == 200 and a.get('terminal_event') in ['response.completed', 'json_object']
            and raw.get('status') == 'completed' and raw.get('model') == row['model']
            and bool(raw.get('id')) and bool(text.strip()))


def auxiliary_label(ans):
    a = bool(re.fullmatch(r'[\(\[]?a[\)\].:]?\s*[.!]?', ans, re.I))
    none = bool(re.fullmatch(r'none(?: of the above)?\s*[.!]?', ans, re.I))
    anone = bool(re.fullmatch(r'[\(\[]?a[\)\].:]?\s*[-:.)]?\s*none(?: of the above)?\s*[.!]?', ans, re.I))
    return 'label_only_A' if a else 'explicit_None' if none else 'A_with_None' if anone else None


class Audit:
    def __init__(self):
        self.errors = []
        self.checks = collections.Counter()
        self.observations = []

    def check(self, ok, name, detail=''):
        self.checks[name] += 1
        if not ok:
            self.errors.append(dict(check=name, detail=str(detail)))
        return ok

    def capture(self, root, rows, numeric=True):
        root = Path(root)
        plan = {r['key']: r for r in rows}
        intents, attempts = [], []
        folders = []
        for ap in sorted(root.rglob('attempts.jsonl')):
            aa = read_lines(ap)
            # Parent linkage can receive all waves; numeric roots must contain only this design.
            if not numeric:
                aa = [a for a in aa if a.get('key') in plan]
            if aa or numeric:
                folders.append(ap.parent)
                attempts.extend((a, ap.parent) for a in aa)
        for ip in sorted(root.rglob('intent.jsonl')):
            ii = read_lines(ip)
            if not numeric:
                ii = [a for a in ii if a.get('key') in plan]
            intents.extend(ii)
        im, am = {}, {}
        for i in intents:
            ident = (i.get('key'), i.get('attempt'))
            self.check(ident not in im, 'unique_intent', ident)
            self.check(type(i.get('attempt')) is int and 1 <= i['attempt'] <= 3, 'intent_attempt_number', ident)
            im[ident] = i
            r = plan.get(i.get('key'))
            self.check(r is not None, 'intent_planned_key', ident)
            if r:
                self.check(i.get('request_sha') == r['request_sha'], 'intent_request_hash', ident)
        bykey = collections.defaultdict(list)
        seen_ids, seen_terminals, finals = set(), set(), {}
        totals = collections.Counter()
        cost = decimal.Decimal(0)
        for a, folder in attempts:
            ident = (a.get('key'), a.get('attempt'))
            self.check(ident not in am, 'unique_attempt', ident)
            am[ident] = a
            self.check(ident in im, 'attempt_has_intent', ident)
            row = plan.get(a.get('key'))
            if not self.check(row is not None, 'attempt_planned_key', ident):
                continue
            bykey[a['key']].append(a)
            for k in ['case', 'model', 'arm', 'request_sha']:
                self.check(a.get(k) == row[k], 'attempt_' + k, ident)
            term = folder / 'terminal' / f"{a['key']}-{a['attempt']}.json.gz"
            t, text, ok = {}, '', False
            if term.exists():
                seen_terminals.add(term.resolve())
                b = gzip.decompress(term.read_bytes())
                t = json.loads(b)
                self.check(b == canonical(t), 'terminal_canonical_bytes', ident)
                self.check(digest(b) == a.get('terminal_sha'), 'terminal_hash', ident)
                text = output_text(t)
                self.check(text == a.get('text'), 'terminal_output_text', ident)
                self.check(digest(text.encode()) == a.get('output_sha'), 'output_hash', ident)
                for ak, tk in [('response_id', 'id'), ('returned_model', 'model'), ('incomplete_details', 'incomplete_details')]:
                    self.check(a.get(ak) == t.get(tk), 'terminal_' + tk, ident)
                self.check(a.get('status') == (t.get('status') or 'missing_status'), 'terminal_status', ident)
                self.check(t.get('model') == row['model'], 'terminal_requested_model', ident)
                rid = t.get('id')
                self.check(bool(rid) and rid not in seen_ids, 'unique_response_id', ident)
                seen_ids.add(rid)
                for k in ['max_output_tokens', 'temperature', 'store', 'tool_choice', 'tools']:
                    self.check(t.get(k) == row['payload'][k], 'terminal_parameter_' + k, ident)
                u = sanitized_usage(t)
                self.check(a.get('usage') == u, 'original_usage', ident)
                if all(k in u for k in ['input_tokens', 'output_tokens', 'total_tokens']):
                    self.check(u['input_tokens'] + u['output_tokens'] == u['total_tokens'], 'usage_token_sum', ident)
                if 'output_tokens' in u:
                    self.check(u['output_tokens'] <= row['payload']['max_output_tokens'], 'output_cap', ident)
                ok = eligible(a, t, text, row)
                if a.get('terminal_event') != {'completed': 'response.completed', 'incomplete': 'response.incomplete',
                                             'failed': 'response.failed', 'cancelled': 'response.cancelled'}.get(t.get('status')):
                    self.observations.append(dict(kind='event_status_pair', key=a['key'],
                                                  event=a.get('terminal_event'), status=t.get('status')))
            else:
                self.check(not a.get('terminal_sha') and not a.get('response_id') and not a.get('returned_model')
                           and not a.get('text') and not a.get('output_sha') and not a.get('usage'), 'no_terminal_no_derived_data', ident)
            self.check(a.get('eligible') is ok, 'independent_eligibility', ident)
            # Scoring uses only the independently recovered original response.
            a['_independent_eligible'], a['_independent_text'] = ok, text
            for k in ['input_tokens', 'output_tokens', 'total_tokens']:
                totals[k] += (a.get('usage') or {}).get(k, 0)
            cost += decimal.Decimal(str((a.get('usage') or {}).get('cost', 0) or 0))
        for key, aa in bykey.items():
            aa.sort(key=lambda a: a['attempt'])
            self.check([a['attempt'] for a in aa] == list(range(1, len(aa) + 1)), 'contiguous_attempts', key)
            self.check(len(aa) <= 3, 'maximum_three_attempts', key)
            for prior, nxt in zip(aa, aa[1:]):
                self.check(prior.get('http') == 429 and prior.get('status') == 'http_429', 'retry_only_429', key)
                if prior.get('end') and nxt.get('start'):
                    gap = (datetime.datetime.fromisoformat(nxt['start']) - datetime.datetime.fromisoformat(prior['end'])).total_seconds()
                    self.check(gap >= max(6 if numeric else 4, prior.get('retry_after_seconds', 0)) - .02,
                               'retry_after_cooldown', key)
            finals[key] = aa[-1]
        if numeric:
            for attempt in [1, 2, 3]:
                actual = [i['key'] for i in intents if i['attempt'] == attempt]
                expected = ([r['key'] for r in rows] if attempt == 1 else
                            [a['key'] for a, _ in attempts if a['attempt'] == attempt - 1 and a.get('http') == 429])
                self.check(actual == expected[:len(actual)], 'deterministic_dispatch_retry_order', attempt)
            disk = {p.resolve() for p in root.rglob('*.json.gz') if p.parent.name == 'terminal'}
            self.check(disk == seen_terminals, 'terminal_attempt_bijection')
        pending = sorted(set(im) - set(am))
        if pending:
            self.observations.append(dict(kind='intent_without_recorded_attempt_unknown', identities=pending))
        return finals, dict(planned=len(rows), unique_started=len({i['key'] for i in intents}),
                            recorded_unique=len(finals), attempts=len(attempts), terminal_objects=len(seen_terminals),
                            http_429=sum(a.get('http') == 429 for a, _ in attempts),
                            unattempted=len(plan.keys() - {i['key'] for i in intents}), pending_intents=len(pending),
                            eligible=sum(a['_independent_eligible'] for a in finals.values()),
                            status=dict(collections.Counter(a.get('status') for a in finals.values())),
                            **{k: totals[k] for k in ['input_tokens', 'output_tokens', 'total_tokens']},
                            provider_cost=float(cost), provider_cost_decimal=str(cost))


def score(cases, rows, finals):
    groups = {m: {a: collections.Counter(n=0) for a in ['correct', 'wrong']} for m in MODELS}
    outcomes = []
    for r in rows:
        a, c = finals.get(r['key'], {}), cases[r['case']]
        d = groups[r['model']][r['arm']]
        d['n'] += 1
        outcome = {k: r[k] for k in ['key', 'case', 'source_id', 'model', 'arm', 'request_sha', 'value']}
        outcome.update(status=a.get('status', 'unattempted'), response_id=a.get('response_id'),
                       eligible=bool(a.get('_independent_eligible')), says_option=None, factually_correct=None)
        if not a.get('_independent_eligible'):
            d['unknown'] += 1
        else:
            ans, extraction = final_answer(a['_independent_text'])
            v = number(ans, c['unit'])
            says, correct = int(v == number(r['value'], c['unit'])), int(v == number(c['gold'][0], c['unit']))
            d['says_option'] += says
            d['factually_correct'] += correct
            d['complete'] += 1
            label = auxiliary_label(ans)
            if label:
                d[label] += 1
            outcome.update(final_answer=ans, extraction=extraction, says_option=says, factually_correct=correct,
                           auxiliary_label=label, numeric_value=str(v) if v is not None else None)
        outcomes.append(outcome)
    output = {}
    for m, arms in groups.items():
        output[m] = {}
        for arm, d in arms.items():
            out = {k: d[k] for k in ['n', 'complete', 'unknown', 'says_option', 'factually_correct',
                                    'label_only_A', 'explicit_None', 'A_with_None']}
            out['says_option_bounds_pct'] = [100 * d['says_option'] / 24, 100 * (d['says_option'] + d['unknown']) / 24]
            out['factual_accuracy_bounds_pct'] = [100 * d['factually_correct'] / 24, 100 * (d['factually_correct'] + d['unknown']) / 24]
            output[m][arm] = out
    return output, outcomes


def main_rows(cases, selected):
    rows = []
    for i in selected:
        c = cases[i]
        for mi, m in enumerate(MODELS):
            for ai, arm in enumerate(MAIN_ARMS):
                p = payload(c, m, i, arm)
                rows.append(dict(key=f"{c['dataset']}-{c['id']}-m{mi}-a{ai}", case=i, source_id=c['id'],
                                 model=m, arm=arm, request_sha=digest(canonical(p)), payload=p))
    return rows


def audit(artifact_root, source_dir, main_roots=()):
    check = Audit()
    cp = source_path(source_dir)
    cases = json.loads(cp.read_bytes())
    check.check(len(cases) == 200 and digest(canonical(cases)) == CASES_SHA, 'frozen_200_case_identity')
    rows = make_plan(cases)
    selected = sorted({r['case'] for r in rows})
    finals, totals = check.capture(artifact_root, rows)
    results, outcomes = score(cases, rows, finals)
    reserve = sum((3 * ((decimal.Decimal(len(r['payload']['input'].encode()) + 1024) * RATES[r['model']][0]) +
                        decimal.Decimal(r['payload']['max_output_tokens']) * RATES[r['model']][1]) / 1000000 for r in rows), decimal.Decimal(0))
    summaries = []
    for sp in Path(artifact_root).rglob('summary.json'):
        s = json.loads(sp.read_bytes())
        if 'source_indices' not in s or 'maximum_reservation_including_retries' not in s:
            continue
        summaries.append(str(sp))
        for k in ['planned', 'terminal_objects', 'attempts', 'http_429', 'source_indices']:
            expected = selected if k == 'source_indices' else totals[k]
            check.check(s.get(k) == expected, 'summary_' + k, sp)
        check.check(abs(s.get('provider_cost', 0) - totals['provider_cost']) < 1e-9, 'summary_provider_cost', sp)
        check.check(abs(decimal.Decimal(str(s['maximum_reservation_including_retries'])) - reserve) < decimal.Decimal('1e-9'), 'summary_reservation', sp)
        for m in MODELS:
            for arm in ['correct', 'wrong']:
                # Original Counter serialization omits zero-valued absent fields.
                for k in ['n', 'complete', 'unknown', 'says_option', 'factually_correct']:
                    check.check(s['results'][m][arm].get(k, 0) == results[m][arm][k], 'summary_score_' + k, (m, arm))
    linkage, parent_coverage = None, None
    if main_roots:
        parent = main_rows(cases, selected)
        all_main = {}
        main_totals = []
        for root in main_roots:
            f, t = check.capture(root, parent, numeric=False)
            check.check(not (set(f) & set(all_main)), 'main_roots_no_overlapping_slots', root)
            all_main.update(f)
            main_totals.append(t)
        linkage = []
        for r in parent:
            a, c = all_main.get(r['key'], {}), cases[r['case']]
            ans = final_answer(a['_independent_text'])[0] if a.get('_independent_eligible') else None
            linkage.append(dict(source_index=r['case'], source_id=r['source_id'], model=r['model'], arm=r['arm'],
                                key=r['key'], request_sha=r['request_sha'], response_id=a.get('response_id'),
                                status=a.get('status', 'unattempted'), final_answer=ans,
                                factually_correct=int(number(ans, c['unit']) == number(c['gold'][0], c['unit'])) if ans is not None else None,
                                auxiliary_label=auxiliary_label(ans) if ans is not None else None))
        parent_coverage = dict(planned=384, recorded=len(all_main),
                               eligible=sum(a['_independent_eligible'] for a in all_main.values()),
                               unknown=384 - sum(a['_independent_eligible'] for a in all_main.values()))
    return dict(passed=not check.errors, execution_commit=EXECUTION_COMMIT,
                capture_complete=totals['recorded_unique'] == 192 and totals['pending_intents'] == 0,
                cases_canonical_sha256=digest(canonical(cases)), source_indices=selected,
                selected_source_ids=[dict(index=i, id=cases[i]['id']) for i in selected],
                manifest_sha256=digest(canonical([{k: v for k, v in r.items() if k != 'payload'} for r in rows])),
                maximum_reservation_including_retries=str(reserve), totals=totals, results=results,
                original_summary_paths=summaries, outcomes=outcomes, parent_linkage=linkage,
                parent_coverage=parent_coverage,
                checks=dict(check.checks), failures=check.errors, observations=check.observations,
                interpretation=['Wrong-arm says_option is the prespecified wrong numerical final-answer endpoint.',
                                'Label-only A and literal None are separate descriptive outcomes, never recoded as a number.',
                                'All rates use 24 planned items per model and arm; missing/incomplete/error/pending slots are bounded both ways.',
                                'The congruent arm displays the annotated gold value and measures uptake of that oracle control, not unaided model ability.',
                                'The same selected 24 source answers were available to analysts after deterministic selection; this was not answer-blind.',
                                'Primary four-arm same-ID comparison remains pending unless parent artifacts are supplied.'],
                limitations=['Frozen cases and their identity are verified; upstream source-corpus selection is not rerun.',
                             'Original terminal objects are checked, but raw SSE bytes are unavailable, so recorded stream hashes cannot be independently rehashed.',
                             'A missing original summary is reported by an empty original_summary_paths list; partial captures remain explicitly unknown.'])


class SelfTests(unittest.TestCase):
    def test_fixed_number_endpoint(self):
        self.assertEqual(number('**$1,234.50**', '$'), Fraction(2469, 2))
        self.assertEqual(number('7 apples.', 'apples'), 7)
        for s in ['A', 'A. 7', 'None', 'the answer is 7']:
            self.assertIsNone(number(s, ''))
        self.assertEqual(final_answer('<answer>1</answer><answer>2</answer>')[0], '2')
        self.assertEqual(auxiliary_label('A'), 'label_only_A')
        self.assertEqual(auxiliary_label('None'), 'explicit_None')

    def test_unattempted_is_unknown_with_full_bounds(self):
        cases = [dict(unit='', gold=['3'])]
        rows = [dict(key='k', case=0, source_id='x', model=m, arm=arm,
                     request_sha='h', value='4' if arm == 'wrong' else '3')
                for m in MODELS for arm in ['correct', 'wrong'] for _ in range(24)]
        results, _ = score(cases, rows, {})
        for m in MODELS:
            self.assertEqual(results[m]['wrong']['unknown'], 24)
            self.assertEqual(results[m]['wrong']['says_option_bounds_pct'], [0, 100])

    def fixture(self, root, mutations=None, two=False):
        c = dict(dataset='tabmwp', id='test', gold=['3'], unit='', question='q', context='c')
        rows = []
        intents, attempts = [], []
        (root / 'terminal').mkdir()
        for n in range(2 if two else 1):
            p = payload(c, MODELS[0], 151, value='4')
            row = dict(key=f'test{n}', case=151, source_id='test', model=MODELS[0], arm='wrong', value='4', request_sha=digest(canonical(p)), payload=p)
            rows.append(row)
            raw = dict(id=f'response{n}', model=MODELS[0], status='completed', output_text='<answer>4</answer>',
                       usage=dict(input_tokens=1, output_tokens=2, total_tokens=3, cost=.1),
                       **{k: p[k] for k in ['max_output_tokens', 'temperature', 'store', 'tool_choice', 'tools']})
            a = dict(key=row['key'], case=151, model=MODELS[0], arm='wrong', attempt=1, request_sha=row['request_sha'],
                     http=200, terminal_event='response.completed', eligible=True)
            if mutations:
                mutations(n, raw, a)
            b = canonical(raw)
            a.update(terminal_sha=digest(b), text=output_text(raw), output_sha=digest(output_text(raw).encode()),
                     returned_model=raw['model'], response_id=raw['id'], status=raw['status'], usage=sanitized_usage(raw))
            (root / 'terminal' / f"{row['key']}-1.json.gz").write_bytes(gzip.compress(b))
            intents.append(dict(key=row['key'], attempt=1, request_sha=row['request_sha']))
            attempts.append(a)
        (root / 'intent.jsonl').write_text(''.join(json.dumps(i) + '\n' for i in intents))
        (root / 'attempts.jsonl').write_text(''.join(json.dumps(a) + '\n' for a in attempts))
        return rows, attempts

    def test_original_incomplete_under_completed_sse_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows, _ = self.fixture(root, lambda n, raw, a: (raw.update(status='incomplete'), a.update(eligible=False)))
            check = Audit()
            f, _ = check.capture(root, rows)
            self.assertFalse(f['test0']['_independent_eligible'])
            self.assertFalse(check.errors)

    def test_wrong_request_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows, _ = self.fixture(root, lambda n, raw, a: a.update(request_sha='bad'))
            check = Audit()
            check.capture(root, rows)
            self.assertIn('attempt_request_sha', [e['check'] for e in check.errors])

    def test_duplicate_response_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows, _ = self.fixture(root, lambda n, raw, a: raw.update(id='duplicate'), two=True)
            check = Audit()
            check.capture(root, rows)
            self.assertIn('unique_response_id', [e['check'] for e in check.errors])

    def test_retry_after_non429_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows, attempts = self.fixture(root)
            a = dict(attempts[0], attempt=2)
            (root / 'terminal' / 'test0-2.json.gz').write_bytes((root / 'terminal' / 'test0-1.json.gz').read_bytes())
            with (root / 'attempts.jsonl').open('a') as f:
                f.write(json.dumps(a) + '\n')
            with (root / 'intent.jsonl').open('a') as f:
                f.write(json.dumps(dict(key='test0', attempt=2, request_sha=rows[0]['request_sha'])) + '\n')
            check = Audit()
            check.capture(root, rows)
            self.assertIn('retry_only_429', [e['check'] for e in check.errors])


def cli():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('artifact_root', nargs='?', type=Path)
    p.add_argument('source_code_dir', nargs='?', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--main-root', action='append', default=[], type=Path)
    p.add_argument('--self-test', action='store_true')
    args = p.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests)
        raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    if not args.artifact_root or not args.source_code_dir or not args.output:
        p.error('artifact_root, source_code_dir, and --output are required')
    result = audit(args.artifact_root, args.source_code_dir, args.main_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: result[k] for k in ['passed', 'totals', 'failures']}, indent=2))
    raise SystemExit(not result['passed'])


if __name__ == '__main__':
    cli()
