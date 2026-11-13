"""Offline actual-SSE fixtures for the fixed prospective gap pipeline."""
import argparse
import contextlib
import datetime as dt
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import shutil

import capture_math
import gate_admission
import prepare_manifest
import analyze_gap
from scoring import numeric,parse_answers,score_answer

ROOT=Path(__file__).resolve().parent
RUNNER=ROOT.parents[2]/'scripts/run_adaption_stream_pilot.py'
spec=importlib.util.spec_from_file_location('gap_fixture_frozen_runner',RUNNER)
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class Result(io.BytesIO):
    status=200
    headers={'Content-Type':'text/event-stream'}

class Opener:
    def __init__(self,text,status='completed',malformed=False):
        response={'id':'offline_fixture','status':status,'output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':text}]}]}
        frames=[]
        if malformed:frames.append('event: response.output_text.delta\ndata: {oops}\n\n')
        frames.append('event: response.completed\ndata: '+json.dumps({'type':'response.completed','response':response})+'\n\n')
        self.data=''.join(frames).encode()
    def open(self,request,timeout):return Result(self.data)


def synthetic():
    return {'source_validation_status':'accepted_source_reviewed','families':[
        {'source_family_id':f'SYNTHETIC-{slot}','selection_slot':slot,'analysis_role':'replication',
         'batch_block':(slot-1)//3+1,'source_validation_status':'accepted',
         'variants':[{'variant':v,'question':f'Synthetic {v} problem {slot}: what is 1+1?','gold_answer':'2'} for v in prepare_manifest.VARIANTS]}
        for slot in range(1,31)]}


def fixture_args(p):
    inputs={
      'selected_data':synthetic(),'source_manifest':{'offline_fixture':True},
      'source_disposition':{'offline_fixture':True},'selection_plan':{'offline_fixture':True}}
    paths={}
    for key,value in inputs.items():
        path=p/(key+'.json');path.write_text(json.dumps(value));paths[key]=path
    for key,filename in (('primary_spec','primary_spec.json'),('prospective_design','prospective_design.md')):
        path=p/filename;origin=ROOT/filename if (ROOT/filename).is_file() else ROOT.parent/filename
        shutil.copyfile(origin,path);paths[key]=path
    return argparse.Namespace(**paths,runner=RUNNER,output_dir=p/'cohort')


def prepare_fixture(p):
    args=fixture_args(p)
    with contextlib.redirect_stdout(io.StringIO()):prepare_manifest.prepare(args)
    for name in json.loads((args.output_dir/'protocol.json').read_text())['implementation_sha256']:
        shutil.copyfile(ROOT/name,args.output_dir/name)
    return args


def admission_fixture(p,malformed=False):
    args=prepare_fixture(p);admission=args.output_dir/'admission'
    for n in ('api_artifacts','stream_journals'):(admission/n).mkdir()
    rows,_=runner.load_manifest(admission)
    for i,row in enumerate(rows):
        # Deliberately wrong arithmetic, which must not block admission.
        text=json.dumps({key:'999' for key in row['item_ids']})
        if malformed and i==0:text='{"wrong_id":"999"}'
        runner.run_trial(row,'OFFLINE-TEST-CREDENTIAL',1,admission/'api_artifacts',admission/'stream_journals',opener=Opener(text))
    return argparse.Namespace(directory=args.output_dir,runner=RUNNER,freeze_commit='1'*40,
        freeze_time='2020-01-01T00:00:00Z',freeze_protocol_sha256=prepare_manifest.sha(args.output_dir/'protocol.json'))


def captured_fixture(p,mode='all_correct'):
    args=admission_fixture(p)
    with contextlib.redirect_stdout(io.StringIO()):gate_admission.run(args)
    cohort=args.directory
    for n in ('api_artifacts','stream_journals'):(cohort/n).mkdir()
    rows,manifest_hash=runner.load_manifest(cohort);records=[];invalid_done=False
    for row in rows:
        answer='2'
        if mode=='positive_with_unknown' and row['requested_model']==prepare_manifest.MODELS[0] and row['variant'] in ('p1_i0','p1_i1'):answer='3'
        if mode=='threshold_boundary' and row['requested_model']==prepare_manifest.MODELS[0] and row['variant'] in ('p1_i0','p1_i1') and row['batch_block']==1:answer='3'
        text=json.dumps({key:answer for key in row['item_ids']})
        if mode=='positive_with_unknown' and not invalid_done and row['requested_model']==prepare_manifest.MODELS[1] and row['variant']=='p1_i0':
            text='Result: '+text;invalid_done=True
        records.append(runner.run_trial(row,'OFFLINE-TEST-CREDENTIAL',1,cohort/'api_artifacts',cohort/'stream_journals',opener=Opener(text)))
    (cohort/'responses.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    (cohort/'run_metadata.json').write_text(json.dumps({'manifest_sha256':manifest_hash,'requested':80,'attempts_per_trial':1,'retries':0}))
    with contextlib.redirect_stdout(io.StringIO()):capture_math.run(args)
    return args

class NumericAndJSON(unittest.TestCase):
    def test_exact_codec_and_unknowns(self):
        self.assertEqual(numeric('$1,000.00'),numeric('1e3'));self.assertEqual(numeric('.5'),numeric('1/2'))
        self.assertNotEqual(numeric('0.333'),numeric('1/3'))
        for value in ('40%','1,23','1+2','NaN','2 meters','1e999999',None,2,'1/0'):
            self.assertEqual(score_answer(value,'2')['score_upper'],1);self.assertFalse(score_answer(value,'2')['format_valid'])
        self.assertEqual(score_answer('ABSTAIN','2')['score_upper'],0)
    def test_entire_json_keyset(self):
        self.assertEqual(parse_answers('```json\n{"X":"3","Y":"4"}\n```',['X','Y']),{'X':'3','Y':'4'})
        for text in ('{"X":"3","X":"4"}','{"X":"3"}','{"X":"3","Y":"4","Z":"5"}','Result: {"X":"3","Y":"4"}','{"X":NaN,"Y":"4"}'):
            with self.assertRaises(ValueError):parse_answers(text,['X','Y'])

class CaptureReplay(unittest.TestCase):
    def capture(self,p,status='completed',malformed=False):
        for name in ('api_artifacts','stream_journals'):(p/name).mkdir()
        row={'trial_id':'fixture','request_payload':{'model':'fixture','input':'synthetic'}}
        runner.run_trial(row,'OFFLINE-TEST-CREDENTIAL',1,p/'api_artifacts',p/'stream_journals',opener=Opener('{"X":"3"}',status,malformed))
        return row
    def test_strict_completed_terminal(self):
        for status,malformed,expected in (('completed',False,True),('incomplete',False,False),('completed',True,False)):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);row=self.capture(p,status,malformed)
                _,_,report=capture_math.verify_one(row,p,runner,dt.datetime(2020,1,1,tzinfo=dt.timezone.utc))
                self.assertEqual(report['capture_complete'],expected)
    def test_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);row=self.capture(p);artifact=p/'api_artifacts/fixture.json'
            value=json.loads(artifact.read_text());value['output_text']='tampered';artifact.write_text(json.dumps(value))
            _,_,report=capture_math.verify_one(row,p,runner,dt.datetime(2020,1,1,tzinfo=dt.timezone.utc))
            self.assertIn('output_text_sha256_mismatch',report['integrity_problems'])

class Pipeline(unittest.TestCase):
    def test_allocation_question_only_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=prepare_fixture(Path(tmp));rows,_=runner.load_manifest(args.output_dir)
            self.assertEqual(len(rows),80);self.assertEqual(len({i for r in rows for i in r['item_ids']}),120)
            self.assertEqual({r['trial_id'] for r in rows},{f'GR-{i:03d}' for i in range(1,81)})
            blocks={}
            for r in rows:
                self.assertEqual(r['analysis_role'],'replication');self.assertEqual(len(set(r['family_ids'])),3)
                blocks.setdefault(r['batch_block'],r['family_ids']);self.assertEqual(blocks[r['batch_block']],r['family_ids'])
                self.assertNotIn('gold_answer',r['request_payload']['input']);self.assertNotIn('SYNTHETIC-',r['request_payload']['input'])
            self.assertEqual(len(blocks),10)
            with self.assertRaises(FileExistsError):prepare_manifest.prepare(args)
    def test_format_gate_accepts_wrong_math_rejects_bad_keys(self):
        for bad in (False,True):
            with tempfile.TemporaryDirectory() as tmp:
                args=admission_fixture(Path(tmp),bad)
                with contextlib.redirect_stdout(io.StringIO()):
                    if bad:
                        with self.assertRaises(SystemExit):gate_admission.run(args)
                    else:gate_admission.run(args)
                gate=json.loads((args.directory/'admission/GATE.json').read_text())
                self.assertEqual(gate['gate_passed'],not bad);self.assertFalse(gate['arithmetic_correctness_checked'])
    def test_full80sse_primary_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=captured_fixture(Path(tmp));p=args.directory
            integrity=json.loads((p/'capture_integrity.json').read_text())
            self.assertEqual(integrity['strict_complete_requests'],80);self.assertEqual(integrity['known_item_scores'],240);self.assertEqual(integrity['global_issues'],[])
            with contextlib.redirect_stdout(io.StringIO()):summary=analyze_gap.analyze(p)
            self.assertEqual(summary['primary']['lower_fraction'],'0');self.assertEqual(summary['primary']['upper_fraction'],'0')
            self.assertFalse(summary['primary']['meaningful_replication']);self.assertTrue(summary['primary']['nonpositive_identified'])
            self.assertEqual(summary['bootstrap']['family']['unit_count'],30);self.assertEqual(summary['bootstrap']['batch_block']['unit_count'],10)
    def test_full80sse_primary_unknown_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=captured_fixture(Path(tmp),'positive_with_unknown')
            with contextlib.redirect_stdout(io.StringIO()):summary=analyze_gap.analyze(args.directory)
            self.assertEqual(summary['capture']['unknown_scores'],3);self.assertEqual(summary['capture']['known_scores'],237)
            self.assertEqual(summary['primary']['lower_fraction'],'19/20');self.assertEqual(summary['primary']['upper_fraction'],'1')
            self.assertTrue(summary['primary']['meaningful_replication']);self.assertTrue(summary['primary']['positive_identified'])
            self.assertIsNone(summary['bootstrap']['family']['point_interval95'])
            with self.assertRaisesRegex(ValueError,'no overwrite'):analyze_gap.analyze(args.directory)
    def test_pending_or_missing_inputs_fail_before_generated_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=fixture_args(Path(tmp));source=json.loads(args.selected_data.read_text());source['source_validation_status']='pending';args.selected_data.write_text(json.dumps(source))
            with self.assertRaises(ValueError):prepare_manifest.prepare(args)
            self.assertFalse((args.output_dir/'manifest.jsonl').exists())
            source['source_validation_status']='accepted_source_reviewed';args.selected_data.write_text(json.dumps(source));args.source_manifest=Path(tmp)/'absent.json'
            with self.assertRaises(FileNotFoundError):prepare_manifest.prepare(args)
            self.assertFalse((args.output_dir/'manifest.jsonl').exists())

if __name__=='__main__':unittest.main()
