"""Bundle the measured trial, immutable captures and minimal scoring sources."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent


def main():
    result = json.loads((ROOT / 'RESULTS.json').read_text())
    assert result['recorded_requests'] == result['planned_requests'] == 200
    assert json.loads((ROOT / 'CAPTURE_VERIFICATION.json').read_text())['checked_trials'] == 200
    pairs = []
    names = ['EXECUTION_PROTOCOL.json', 'NEXT_EXPERIMENT.json', 'LAUNCH_RECEIPT.json',
             'ANALYSIS_SPECIFICATION.json', 'RELATED_WORK.json', 'requirements.txt',
             'fresh_panel.jsonl.gz', 'planned_requests.jsonl.gz',
             'run_adaption_stream_pilot.py', 'execute_paired.py', 'workflow.yml',
             'analyze_paired.py', 'verify_capture.py', 'build_report.py', 'bundle_results.py',
             'RESULTS.json', 'ROW_ANALYSIS.json', 'CAPTURE_VERIFICATION.json',
             'RESULTADOS.md', 'RESEARCH_STATUS.json', 'PROVENANCE.json', 'PORTABLE_REPLAY_VERIFICATION.json']
    for name in names:
        path = ROOT / name
        assert path.is_file(), path
        pairs.append((path, 'oneeval_paired_20261114/' + name))
    for path in sorted((ROOT / 'capture').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            pairs.append((path, 'oneeval_paired_20261114/capture/' + path.relative_to(ROOT / 'capture').as_posix()))
    for name in ['audit_contracts.py', 'analyze_model_smoke.py', 'GALLERY_SELECTED.json', 'upstream/dataflow_eval_tool.py']:
        pairs.append((WORKSPACE / 'default_contract_audit_20261113' / name, 'default_contract_audit_20261113/' + name))
    reference = WORKSPACE / 'oneeval_alias_evidence_20261113'
    sources = [reference / name for name in ['reproduce_alias.py', 'UPSTREAM_SOURCES.json', 'LICENSE', 'word2number/LICENSE.txt']]
    sources += sorted((reference / 'one_eval').rglob('*.py'))
    sources += sorted((reference / 'word2number').rglob('*.py'))
    for path in sources:
        pairs.append((path, 'oneeval_alias_evidence_20261113/' + path.relative_to(reference).as_posix()))
    for name in ['winogrande__validation.jsonl.gz', 'DATASET_DISPOSITIONS.json']:
        pairs.append((WORKSPACE / 'default_contract_source_capture_20261113/capture' / name,
                      'default_contract_source_capture_20261113/capture/' + name))
    for name in ['prompt_collision_results.json', 'public_exposure_search.json']:
        pairs.append((WORKSPACE / 'oneeval_followup_20261113' / name, 'oneeval_followup_20261113/' + name))
    assert len({name for _, name in pairs}) == len(pairs)
    index = {name: {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path, name in pairs}
    archive = WORKSPACE / 'OneEval_ensaio_emparelhado_200_resultados_20261114.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=7) as bundle:
        for path, name in pairs:
            bundle.write(path, name)
        bundle.writestr('BUNDLE_INDEX.json', json.dumps(index, indent=2) + '\n')
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
    delivery = dict(path=str(archive), bytes=archive.stat().st_size,
                    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), files=len(pairs) + 1)
    (ROOT / 'DELIVERY.json').write_text(json.dumps(delivery, indent=2) + '\n')
    print(json.dumps(delivery))


if __name__ == '__main__':
    main()
