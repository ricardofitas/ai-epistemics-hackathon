# Advice analysis code audit

Completed 2026-11-13T06:07:23.521438+00:00. The audit passes after two analysis-only fixes. All 35 fabricated checks pass (29 analysis checks and 6 capture/collector checks).

The auditor reviewed the three named methods scripts, the advice grader schema, the original generic rubric, and existing software-verification receipts. No actual study response content, current rating files, packet, key, manifest, condition/model identities, source treatments, API artifacts, WSC/HANS response content, or credentials were inspected. No API calls or Git writes were made.

## Findings and corrections

1. **Positive adjudication could lose its mechanism.** A fabricated consensus first no/no with empty exhaustive mechanism lists could be promoted to yes and accepted. The helper now requires an explicit coordinator mechanism when the final positive overrides the common first label, and at least one final mechanism marked yes for every final primary yes. Uncertain flags retain their uncertainty.
2. **An output path could replace original evidence.** A fabricated raw aggregate was overwritten successfully using `--output responses.jsonl`. The helper now protects the known immutable/raw/source paths, API/journal/methods descendants, every existing custom source or output file except its designated derived summary, symlinks, and Python source/bytecode destinations. New custom analysis destinations remain allowed.

The collector and capture auditor were not modified. No case, rubric, label, source scope, sample, or substantive response requirement changed.

## Verification

The reproducible fixture is `verify_advice_code_audit.py`. It constructs only synthetic rows, requests, terminal events, journals and local-capture failures in temporary directories. It makes no API calls and uses no current study files.

The analysis checks cover the full 72-row join, 24 cells and 24 contrasts; within-cell bounds for a retained incomplete capture; independent primary and utility disagreement handling; final-positive mechanism adjudication; first-file/packet hash mismatches; validation before reading the key; missing captures; packet/key/capture mismatches; duplicate contexts; protected output destinations; safe custom output creation; and designated-summary refresh. A fabricated cell containing two primary no labels plus one unscorable has primary bounds [0, 1/3]; two utility yes labels plus one unscorable has utility bounds [2/3, 1].

The capture/collector checks retain all 72 planned entries: 70 complete, one provider terminal/status mismatch and one explicitly unverifiable local-capture failure. They verify untouched synthetic raw bytes, idempotent packet/key creation and rejection of a changed wire hash. These are fabricated fixture outcomes, not study results.

## Preservation and limits

The original summary helper and previous analysis verification receipt are preserved byte for byte in `superseded_before_code_audit/`, with SHA256 hashes in `preservation_receipt.json`. The current hashes and every fixture result are in `CODE_AUDIT.json` and `ADVICE_ANALYSIS_VERIFICATION.json`.

The helper checks first-rating bytes, packet bytes and the nonempty frozen-time declaration before reading key/enriched data. It does not enforce read-only permissions or independently prove timestamp/unblinding chronology. The external procedural receipt and Git publication must establish that ordering. This audit was completed while the auditor remained blinded to current responses and identities.

Rubric-based source warrant, exact evidence, governing qualifications, case-critical requirement IDs and substantive rationale remain review/adjudication judgments. The fixed-call uncertainty bounds remain descriptive and preserve incomplete/unresolved outcomes. This software audit supplies no population interval, causal efficacy claim, model ranking or external human validation. Existing custom outputs need a new filename; only the designated `analysis_summary.json` may be replaced.

## Exact analysis-helper diff

```diff
--- superseded_before_code_audit/summarize_advice.py
+++ summarize_advice.py
@@ -111,8 +111,10 @@
         if rid in mechanisms:
             m = mechanisms[rid]
             ff = flags({'mechanisms': m} if isinstance(m, list) else {'mechanism_flags': m})
-        elif label == 'yes' and (fa != fb or la != lb):
+        elif label == 'yes' and (fa != fb or la != lb or label != la):
             unresolved.append(rid+': positive mechanism')
+        if label == 'yes' and not any(v == 'yes' for v in ff.values()):
+            unresolved.append(rid+': no positive final mechanism')
         if not packet[rid]['capture_complete'] and (label != 'unscorable' or utility != 'unscorable'):
             raise ValueError('Adjudication cannot promote incomplete '+rid)
         if la != lb or ua != ub or fa != fb:
@@ -175,8 +177,21 @@
                'rows': joined}
     out = args.output or p/'analysis_summary.json'
     protected = {args.ratings_a.resolve(), args.ratings_b.resolve(), args.first_freeze.resolve(), args.adjudication.resolve()}
-    protected.update((p/name).resolve() for name in ['protocol.json', 'manifest.jsonl', 'review_packet.jsonl', 'review_key.jsonl', 'responses_enriched.jsonl', 'rubric.json'])
-    if out.resolve() in protected:
+    protected.update((p/name).resolve() for name in [
+        'protocol.json', 'manifest.jsonl', 'review_packet.jsonl', 'review_key.jsonl',
+        'responses_enriched.jsonl', 'responses.jsonl', 'run_metadata.json',
+        'integrity.json', 'rubric.json', 'casepack.json', 'review_casepack.json',
+        'mechanism_definitions.json'])
+    # Preserve existing files, including protocol-pinned source inputs with
+    # custom names/locations. Only the designated derived summary may be replaced.
+    default_output = (p/'analysis_summary.json').resolve()
+    output_path = out.resolve()
+    evidence_directories = [(p/name).resolve() for name in ['api_artifacts', 'stream_journals']]
+    evidence_directories.append(Path(__file__).resolve().parent)
+    if (out.is_symlink() or output_path in protected
+            or (out.exists() and output_path != default_output)
+            or any(output_path.is_relative_to(d) for d in evidence_directories)
+            or output_path.suffix in {'.py', '.pyc'}):
         raise ValueError('Refusing to overwrite original input')
     out.write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n')
     print(json.dumps({k:v for k,v in summary.items() if k in ['scope','attempted','capture_complete','primary_counts','utility_counts','by_case_arm']}))
```
