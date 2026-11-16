import test from 'node:test';
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
test('HTTP access controls, persistent monitor CRUD and honest disconnected state',{timeout:60000},async()=>{
 const directory=await mkdtemp(path.join(tmpdir(),'bhav-api-test-'));
 const token='isolated-test-token-not-a-real-credential';
 const child=spawn(process.execPath,['server/index.mjs'],{cwd:root,env:{...process.env,HOST:'127.0.0.1',PORT:'0',MONITOR_API_TOKEN:token,MONITOR_DB:path.join(directory,'test.sqlite'),YOUTUBE_API_KEY:'',PYTHON_BIN:path.join(root,'.venv/bin/python')},stdio:['ignore','pipe','pipe']});
 try{
  const base=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(new Error('Test server startup timeout')),10000);child.stdout.on('data',c=>{const m=c.toString().match(/http:\/\/127.0.0.1:\d+/);if(m){clearTimeout(timer);resolve(m[0]);}});child.once('error',reject);});
  const req=async(url,method='GET',body,extra={})=>fetch(base+url,{method,headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json',...extra},...(body!==undefined?{body:JSON.stringify(body)}:{})});
  assert.equal((await fetch(base+'/api/monitors')).status,401);
  assert.equal((await fetch(base+'/api/health')).status,200);
  assert.equal((await req('/api/ready')).status,503);
  assert.equal((await req('/api/monitors','POST',{}, {Origin:'https://untrusted.example'})).status,403);
  assert.equal((await req('/api/monitors','POST',{name:'bad'})).status,400);
  const created=await req('/api/monitors','POST',{name:'Isolated API test',target:'This is a defined test claim.',videos:['https://youtu.be/CswOUBuokjo'],interval_seconds:300});assert.equal(created.status,201);
  const m=await created.json();assert.deepEqual(m.videos,['CswOUBuokjo']);
  const result=await (await req(`/api/monitors/${m.id}/analysis`)).json();assert.equal(result.count,0);assert.equal(result.records.length,0);assert.deepEqual(result.timeline,[]);
  assert.equal((await req(`/api/monitors/${m.id}/collect`,'POST',{})).status,503);
  assert.equal((await req('/api/analyze','POST',{target:'tiny',texts:['x']})).status,400);
  assert.equal((await req('/api/simulate','POST',{})).status,404);
  const paused=await (await req(`/api/monitors/${m.id}`,'PATCH',{enabled:false})).json();assert.equal(paused.enabled,false);
  assert.equal((await req(`/api/monitors/${m.id}`,'DELETE',{})).status,200);
  assert.equal((await req(`/api/monitors/${m.id}/analysis`)).status,404);
 }finally{child.kill('SIGTERM');await new Promise(resolve=>child.once('exit',resolve));await rm(directory,{recursive:true,force:true});}
});
