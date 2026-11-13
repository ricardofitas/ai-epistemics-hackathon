"""Read-only authenticated availability check, without model inference."""
import datetime as dt
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None

root=Path(__file__).resolve().parent
key=os.environ.get('ADAPTION_API_KEY')
result={'utc':dt.datetime.now(dt.timezone.utc).isoformat(),'model_inference_requests':0,
        'check':'authenticated hosted-model catalogue only','secret_present':bool(key)}
if key:
    request=urllib.request.Request('https://api.prod.adaptionlabs.ai/api/v1/models?type=hosted',headers={'Authorization':'Bearer '+key})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=45) as response:
            result['http_status']=response.status;data=json.load(response)
        available={r.get('id') for r in data.get('data',[]) if isinstance(r,dict)}
        result['required_models']={m:m in available for m in ['gemma-4-31b-it','qwen3.8-27b']}
    except urllib.error.HTTPError as error:result['http_status']=error.code
    except Exception as error:result['error_type']=type(error).__name__
(root/'ADAPTION_LIVE_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
