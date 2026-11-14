"""Verify the archived research evidence without provider or judge requests."""

import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parent
ARCHIVES = (
    ("factorial_actual/mixeval-factorial-43615821403.zip", "factorial",
     "7f464eba93330fb19742b850aa4349eeb1804a8b45eaf4664e375b2af2ee8d6d"),
    ("native_validation/zero_initial/native_zero_initial.zip", "fixture",
     "40daaed0a78e59a451785df9391589295f5acae80d68e0d8756826b66fc00359"),
    ("native_validation/real_actual/oneeval-native-live-43620987144.zip", "real",
     "d898dfd28a0d20708b2731a7fbd899d42aadddb5d0a1b2d1617a7c73c3eb47c8"),
    ("native_validation/rescore_actual/oneeval-native-offline-rescore-43621794887.zip", "rescore",
     "63c982408b442dd5771f52a63cdfa492d5446c0e652eab7471d0b4ac0d0b49db"),
)


def main():
    workspace = Path(tempfile.mkdtemp(prefix="epistemics-reproduction-"))
    print(f"Verification outputs are saved in {workspace}", flush=True)
    for relative_path, name, expected in ARCHIVES:
        archive = ROOT / relative_path
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected
        destination = workspace / name
        destination.mkdir()
        with zipfile.ZipFile(archive) as zipped:
            for entry in zipped.infolist():
                assert (destination / entry.filename).resolve().is_relative_to(destination)
            zipped.extractall(destination)

    ranking = workspace / "ranking_analysis"
    shutil.copytree(ROOT / "ranking_analysis", ranking)
    commands = [
        [str(ROOT / "factorial_final_verification/verify.py"), str(workspace / "factorial"),
         "--output", str(ranking / "PRIMARY_VERIFICATION.json")],
        [str(ranking / "analyze_ranking.py")],
        [str(ranking / "verify_ranking.py")],
        [str(ROOT / "native_validation/verify_actual.py"), str(workspace / "fixture"),
         "--mode", "fixture", "--archive", str(ROOT / ARCHIVES[1][0]),
         "--expected-archive-sha", ARCHIVES[1][2],
         "--output", str(workspace / "FIXTURE_VERIFICATION.json")],
        [str(ROOT / "native_validation/verify_actual.py"), str(workspace / "real"),
         "--mode", "real", "--archive", str(ROOT / ARCHIVES[2][0]),
         "--expected-archive-sha", ARCHIVES[2][2],
         "--expected-protocol-sha", "f71f0e21f5f014de0707ff3790b7e2e3c14e4cdb84781cfd9052e1c749622864",
         "--expected-protocol-commit", "c31c0619ec0fb7a70332be33a43f43e6dda2ca4f",
         "--output", str(workspace / "REAL_VERIFICATION.json")],
        [str(ROOT / "native_validation/verify_rescore.py"), str(workspace / "rescore"),
         str(workspace / "real"), "--archive", str(ROOT / ARCHIVES[3][0]),
         "--source-archive", str(ROOT / ARCHIVES[2][0]),
         "--output", str(workspace / "RESCORE_VERIFICATION.json")],
    ]
    for command in commands:
        subprocess.run([sys.executable, *command], check=True)
    print("PASS. Original archives remain unchanged. No model or judge calls were made.")


if __name__ == "__main__":
    main()
