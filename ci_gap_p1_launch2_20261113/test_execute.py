"""Offline one-shot guards and catalogue filtering; no network/model calls."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('ci_execute', Path(__file__).with_name('execute.py'))
ci = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ci)


class GuardTests(unittest.TestCase):
    def env(self, **extra):
        return {'GITHUB_REPOSITORY': ci.REPO, 'GITHUB_REF': 'refs/heads/' + ci.BRANCH,
                'GITHUB_EVENT_NAME': 'push', 'GITHUB_RUN_ATTEMPT': '1',
                'GITHUB_RUN_ID': '100', 'GITHUB_SHA': 'a' * 40,
                'GH_TOKEN': 'offline-fixture-token', **extra}

    def direct(self, **extra):
        return io.BytesIO(json.dumps({'id': 100, 'head_sha': 'a' * 40,
            'head_branch': ci.BRANCH, 'event': 'push', 'path': ci.WORKFLOW,
            'run_attempt': 1, **extra}).encode())

    def response(self, ids):
        return io.BytesIO(json.dumps({'workflow_runs': [
            {'id': i, 'path': ci.WORKFLOW} for i in ids]}).encode())

    def test_single_current_run_passes_direct_and_listing(self):
        with patch.dict(os.environ, self.env(), clear=True), patch.object(
                ci.urllib.request, 'urlopen', side_effect=[self.direct(), self.response([100])]) as call:
            ci.history_guard()
        self.assertEqual(call.call_count, 2)
        self.assertTrue(call.call_args_list[0].args[0].full_url.endswith('/actions/runs/100'))
        self.assertIn('branch=ricardo%2Fepistemics-gap-p1-launch2-20261113', call.call_args_list[1].args[0].full_url)

    def test_current_missing_from_listing_requires_valid_direct_metadata(self):
        with patch.dict(os.environ, self.env(), clear=True), patch.object(
                ci.urllib.request, 'urlopen', side_effect=[self.direct(), self.response([])]) as call:
            ci.history_guard()
        self.assertEqual(call.call_count, 2)

    def test_prior_run_is_rejected_even_when_current_is_not_listed(self):
        for ids in ([100, 99], [99]):
            with self.subTest(ids=ids), patch.dict(os.environ, self.env(), clear=True), patch.object(
                    ci.urllib.request, 'urlopen', side_effect=[self.direct(), self.response(ids)]):
                with self.assertRaisesRegex(RuntimeError, 'Prior matching'):
                    ci.history_guard()

    def test_direct_identity_mismatches_stop_before_history(self):
        cases = ({'id':99}, {'head_sha':'b'*40}, {'head_branch':'another-branch'},
                 {'event':'workflow_dispatch'}, {'path':'.github/workflows/other.yml'},
                 {'run_attempt':2})
        for wrong in cases:
            with self.subTest(wrong=wrong), patch.dict(os.environ, self.env(), clear=True), patch.object(
                    ci.urllib.request, 'urlopen', return_value=self.direct(**wrong)) as call:
                with self.assertRaisesRegex(RuntimeError, 'Direct current run'):
                    ci.history_guard()
            self.assertEqual(call.call_count, 1)

    def test_rerun_is_rejected_without_network(self):
        with patch.dict(os.environ, self.env(GITHUB_RUN_ATTEMPT='2'), clear=True), patch.object(
                ci.urllib.request, 'urlopen') as call:
            with self.assertRaisesRegex(RuntimeError, 'Rerun forbidden'):
                ci.history_guard()
        call.assert_not_called()

    def test_direct_metadata_unavailable_stops_without_history_retry(self):
        with patch.dict(os.environ, self.env(), clear=True), patch.object(
                ci.urllib.request, 'urlopen', side_effect=OSError('offline fixture')) as call:
            with self.assertRaisesRegex(RuntimeError, 'Direct Actions run metadata unavailable'):
                ci.history_guard()
        self.assertEqual(call.call_count, 1)

    def test_listing_unavailable_still_fails_after_valid_direct_metadata(self):
        with patch.dict(os.environ, self.env(), clear=True), patch.object(
                ci.urllib.request, 'urlopen', side_effect=[self.direct(), OSError('offline fixture')]) as call:
            with self.assertRaisesRegex(RuntimeError, 'Actions history unavailable'):
                ci.history_guard()
        self.assertEqual(call.call_count, 2)

    def test_paginated_history_rejects_prior_on_second_page(self):
        unrelated=io.BytesIO(json.dumps({'workflow_runs':[{'id':i,'path':'.github/workflows/unrelated.yml'} for i in range(200,300)]}).encode())
        with patch.dict(os.environ, self.env(), clear=True), patch.object(
                ci.urllib.request, 'urlopen', side_effect=[self.direct(), unrelated, self.response([99])]) as call:
            with self.assertRaisesRegex(RuntimeError, 'Prior matching'):
                ci.history_guard()
        self.assertEqual(call.call_count, 3)
        self.assertIn('page=2',call.call_args_list[2].args[0].full_url)

    def test_invalid_environment_head_sha_stops_without_network(self):
        with patch.dict(os.environ, self.env(GITHUB_SHA='invalid'), clear=True), patch.object(
                ci.urllib.request, 'urlopen') as call:
            with self.assertRaisesRegex(RuntimeError, 'Invalid execution head SHA'):
                ci.history_guard()
        call.assert_not_called()

    def test_guard_failure_occurs_before_catalogue_receipt_or_inference(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(ci,'STUDY',Path(directory)), \
                patch.dict(os.environ, {'ADAPTION_API_KEY':'offline-fixture-key'}, clear=True), \
                patch.object(ci,'check_plan',return_value='d'*64), \
                patch.object(ci,'history_guard',side_effect=RuntimeError('fixture guard failure')), \
                patch.object(ci,'catalog_check') as catalog, patch.object(ci.subprocess,'run') as run:
            with self.assertRaisesRegex(RuntimeError,'fixture guard failure'):
                ci.execute()
            self.assertEqual(list(Path(directory).iterdir()),[])
        catalog.assert_not_called();run.assert_not_called()

    def test_catalogue_is_metadata_only_and_filtered(self):
        payload = {'data': [{'id': m, 'display_name': m, 'unexpected': 'drop-this'}
                            for m in sorted(ci.MODELS)]}
        class Opener:
            def open(self, request, timeout):
                return io.BytesIO(json.dumps(payload).encode())
        with tempfile.TemporaryDirectory() as directory, patch.object(ci, 'STUDY', Path(directory)), \
                patch.dict(os.environ, {'ADAPTION_API_KEY': 'offline-fixture-key'}, clear=True), \
                patch.object(ci.urllib.request, 'build_opener', return_value=Opener()):
            ci.catalog_check()
            saved = json.loads((Path(directory) / 'provider_catalog.json').read_text())
        self.assertEqual(saved['model_inference_calls'], 0)
        self.assertTrue(all(set(row) == {'id', 'display_name'} for row in saved['data']))

    def execution_context(self, directory):
        return {'ADAPTION_API_KEY': 'offline-fixture-key', 'GITHUB_SHA': 'a' * 40,
                'GITHUB_RUN_ID': '100', 'GITHUB_RUN_ATTEMPT': '1'}

    def test_failed_admission_stops_before_study(self):
        pins = {'source_freeze_commit': 'b' * 40, 'protocol.json': 'c' * 64}
        with tempfile.TemporaryDirectory() as directory, patch.object(ci, 'STUDY', Path(directory)), \
                patch.dict(os.environ, self.execution_context(directory), clear=True), \
                patch.object(ci, 'check_plan', return_value='d' * 64), \
                patch.object(ci, 'history_guard'), patch.object(ci, 'catalog_check'), \
                patch.object(ci, 'load', return_value=pins), \
                patch.object(ci.subprocess, 'check_output', return_value='2026-11-13T00:00:00Z\n'), \
                patch.object(ci.subprocess, 'run', side_effect=[None, subprocess.CalledProcessError(1, 'gate')]) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                ci.execute()
            calls = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(calls), 2)
        self.assertTrue(calls[0][2].endswith('/admission'))
        self.assertTrue(calls[1][1].endswith('/gate_admission.py'))

    def test_passing_admission_runs_study_once(self):
        pins = {'source_freeze_commit': 'b' * 40, 'protocol.json': 'c' * 64}
        with tempfile.TemporaryDirectory() as directory, patch.object(ci, 'STUDY', Path(directory)), \
                patch.dict(os.environ, self.execution_context(directory), clear=True), \
                patch.object(ci, 'check_plan', return_value='d' * 64), \
                patch.object(ci, 'history_guard'), patch.object(ci, 'catalog_check'), \
                patch.object(ci, 'load', return_value=pins), \
                patch.object(ci.subprocess, 'check_output', return_value='2026-11-13T00:00:00Z\n'), \
                patch.object(ci.subprocess, 'run', return_value=None) as run:
            ci.execute()
            calls = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[2][2], directory)

    def test_missing_provider_key_stops_before_history_or_inference(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch.object(ci, 'check_plan', return_value='d' * 64), \
                patch.object(ci, 'history_guard') as history, \
                patch.object(ci.subprocess, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'Missing ADAPTION_API_KEY'):
                ci.execute()
        history.assert_not_called()
        run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
