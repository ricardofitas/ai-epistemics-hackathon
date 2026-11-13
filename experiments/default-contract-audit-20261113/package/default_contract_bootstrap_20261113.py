"""Expand byte-verified research captures; never call a model or overwrite edits."""
import hashlib
from pathlib import Path, PurePosixPath
import zipfile

ROOT=Path(__file__).resolve().parent
CAPTURES=[
 ('default_contract_source_capture_20261113.zip','default_contract_source_capture_20261113','a43b28ce6c9219c7c2155d979b2df2a54645e636f1ef1384256522c238a90a39'),
 ('default_contract_model_capture_20261113.zip','default_contract_model_capture_20261113','2a9abd3fd0c5f9108dd4c3812fba5d64c168b6e414d34e3b41191df869ba13df'),
 ('default_contract_locked_support_v2_20261113.zip','default_contract_locked_support_v2_20261113','945d064d442df8166bd4731ed03d478cb354c525792bf8c8441f922c61256dd8'),
 ('default_contract_supported_replay_20261113.zip','default_contract_supported_replay_20261113','915f447b389feaad1561d1f5417b076be0c7ab633b844994d6208b36cd1442f3')
]
for filename,directory,pin in CAPTURES:
    source=ROOT/filename
    assert hashlib.sha256(source.read_bytes()).hexdigest()==pin,filename
    destination=ROOT/directory
    destination.mkdir(exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            name=PurePosixPath(member.filename)
            assert not name.is_absolute() and '..' not in name.parts
            target=destination/name
            assert target.resolve().is_relative_to(destination.resolve())
            if member.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            data=archive.read(member)
            if target.exists():assert target.read_bytes()==data,('existing file differs',target)
            else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    print(filename,'verified and available')
