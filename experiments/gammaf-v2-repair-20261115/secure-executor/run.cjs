'use strict';
const fs=require('node:fs'),path=require('node:path');
const {spawn}=require('node:child_process');
const {openEnvelope}=require('./sealed.cjs');
async function main(){
 const root=path.resolve(__dirname,'..');
 const config=JSON.parse(fs.readFileSync(path.join(root,'executor-config.json'),'utf8'));
 const own=JSON.parse(fs.readFileSync(path.join(root,'credential-public.json'),'utf8'));
 const runId=process.env.GITHUB_RUN_ID,repo=process.env.GITHUB_REPOSITORY;
 if(repo!=='rfitas-lab/rfdl-lab-os'||config.study!=='gammaf-v2-full-options-20261115')throw new Error('Unexpected executor');
 const privatePath=path.join(process.env.RUNNER_TEMP,'gammaf-ephemeral-'+runId+'.pem');
 const jobStart=Number(process.env.EXECUTOR_JOB_STARTED_EPOCH_MS);
 if(!Number.isFinite(jobStart)||jobStart<=0)throw new Error('Missing job start bound');
 const cutoff=Math.min(Date.parse(own.context.deadline_utc),jobStart+21600000-300000);
 const deliveryPath='experiments/gammaf-v2-repair-20261115/credential-delivery/'+runId+'.sealed.json';
 const api='https://api.github.com/repos/'+repo+'/contents/'+deliveryPath+'?ref='+encodeURIComponent(process.env.GITHUB_REF_NAME);
 let envelope=null;
 const waitUntil=Math.min(Date.now()+20*60*1000,cutoff);
 console.log(JSON.stringify({credential_exchange:'waiting_for_encrypted_delivery',run_id:runId,delivery_path:deliveryPath,provider_calls:0}));
 while(Date.now()<waitUntil){
  const response=await fetch(api,{headers:{Authorization:'Bearer '+process.env.GITHUB_TOKEN,Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'},signal:AbortSignal.timeout(20000)});
  if(response.status===200){const item=await response.json();envelope=JSON.parse(Buffer.from(item.content,'base64').toString('utf8'));break;}
  if(response.status!==404)throw new Error('Credential delivery read failed, HTTP '+response.status);
  await new Promise(resolve=>setTimeout(resolve,3000));
 }
 if(!envelope)throw new Error('No encrypted credential delivery before handshake deadline');
 if(Date.now()>=cutoff)throw new Error('Inference cutoff reached');
 const plain=openEnvelope(envelope,fs.readFileSync(privatePath,'utf8'),own.public_spki_b64url,own.context);
 fs.unlinkSync(privatePath);
 const key=plain.toString('utf8');
 if(!/^pt_live_[A-Za-z0-9_-]+$/.test(key))throw new Error('Invalid Adaption credential shape');
 console.log('::add-mask::'+key);
 const capture=path.join(root,'capture');fs.mkdirSync(capture,{recursive:true});
 const receipt={protocol:'rfdl-gammaf-sealed-v1',context:own.context,delivery_path:deliveryPath,plaintext_persisted:false,credential_configured_as_repository_secret:false,authenticated_decryption:true,effective_cutoff_utc:new Date(cutoff).toISOString(),started_utc:new Date().toISOString()};
 fs.writeFileSync(path.join(capture,'credential_delivery_receipt.json'),JSON.stringify(receipt,null,2)+'\n');
 const command=config.inference_command;
 if(!Array.isArray(command)||!command.length||command.some(x=>typeof x!=='string'))throw new Error('Invalid inference command');
 const env={...process.env,ADAPTION_API_KEY:key,PYTHONUNBUFFERED:'1'};delete env.GITHUB_TOKEN;delete env.GH_TOKEN;
 const child=spawn(command[0],command.slice(1),{env,cwd:root,stdio:'inherit',detached:true});
 plain.fill(0);
 let stopping=false;
 const groupKill=signal=>{try{process.kill(-child.pid,signal);}catch(error){if(error.code!=='ESRCH')throw error;}};
 const timer=setInterval(()=>{if(Date.now()>=cutoff&&!stopping){stopping=true;console.error('Inference execution bound reached; requesting checkpoint and stop.');groupKill('SIGINT');setTimeout(()=>groupKill('SIGTERM'),25000).unref();setTimeout(()=>groupKill('SIGKILL'),35000).unref();}},1000);
 const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',(status,signal)=>resolve(status===null?1:status));});
 clearInterval(timer);
 receipt.finished_utc=new Date().toISOString();receipt.exit_code=code;receipt.cutoff_requested=stopping;
 fs.writeFileSync(path.join(capture,'executor_receipt.json'),JSON.stringify(receipt,null,2)+'\n');
 process.exitCode=code;
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
