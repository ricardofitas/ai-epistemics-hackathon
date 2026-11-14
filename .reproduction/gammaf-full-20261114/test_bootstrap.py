"""No-network regression tests for the source acquisition boundary."""
import importlib.util,io,json,pathlib,tempfile,time,unittest
P=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('reproduction',P/'run_reproduction.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Reply(io.BytesIO):
    status=200
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
class Fake:
    def __init__(self,data,status=200):self.data=data;self.status=status;self.calls=0
    def open(self,*args,**kwargs):
        self.calls+=1;r=Reply(self.data);r.status=self.status;return r
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=pathlib.Path(self.tmp.name)/'cache/a.json'
        self.data=b'{"items": []}';self.e={'bytes':len(self.data),'blob':m.blob_hash(self.data)}
    def tearDown(self):self.tmp.cleanup()
    def test_verified_install(self):
        op=Fake(self.data);r=m.acquire(self.e,self.path,'https://raw.githubusercontent.com/x',opener=op)
        self.assertEqual(r['status'],'downloaded_verified');self.assertEqual(self.path.read_bytes(),self.data);self.assertEqual(op.calls,1)
    def test_existing_verified_no_second_request(self):
        self.path.parent.mkdir();self.path.write_bytes(self.data);op=Fake(b'bad')
        self.assertEqual(m.acquire(self.e,self.path,'https://raw.githubusercontent.com/x',opener=op)['status'],'already_verified');self.assertEqual(op.calls,0)
    def test_wrong_hash_never_installs(self):
        op=Fake(self.data);e={**self.e,'blob':'0'*40}
        with self.assertRaises(ValueError):m.acquire(e,self.path,'https://raw.githubusercontent.com/x',opener=op)
        self.assertFalse(self.path.exists());self.assertEqual(op.calls,1)
    def test_excess_size_never_installs(self):
        with self.assertRaises(ValueError):m.acquire(self.e,self.path,'https://raw.githubusercontent.com/x',opener=Fake(self.data+b' '))
        self.assertFalse(self.path.exists())
    def test_truncated_never_installs(self):
        with self.assertRaises(ValueError):m.acquire(self.e,self.path,'https://raw.githubusercontent.com/x',opener=Fake(self.data[:-1]))
        self.assertFalse(self.path.exists())
    def test_schema_invalid_never_installs(self):
        d=b'{"other": []}';e={'bytes':len(d),'blob':m.blob_hash(d)}
        with self.assertRaises(ValueError):m.acquire(e,self.path,'https://raw.githubusercontent.com/x',opener=Fake(d))
        self.assertFalse(self.path.exists())
    def test_non200_never_installs(self):
        with self.assertRaises(ValueError):m.acquire(self.e,self.path,'https://raw.githubusercontent.com/x',opener=Fake(self.data,302))
        self.assertFalse(self.path.exists())
    def test_deadline_no_install(self):
        with self.assertRaises(TimeoutError):m.acquire(self.e,self.path,'https://raw.githubusercontent.com/x',opener=Fake(self.data),deadline=time.monotonic()-1)
        self.assertFalse(self.path.exists())
    def test_existing_contradiction_stops_without_request(self):
        self.path.parent.mkdir();self.path.write_bytes(b'bad');op=Fake(self.data)
        with self.assertRaises(ValueError):m.acquire(self.e,self.path,'https://raw.githubusercontent.com/x',opener=op)
        self.assertEqual(op.calls,0);self.assertEqual(self.path.read_bytes(),b'bad')
if __name__=='__main__':unittest.main()
