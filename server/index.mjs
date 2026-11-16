import express from 'express';
import crypto from 'node:crypto';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { WorkerClient } from './worker-client.mjs';
import { YouTube, videoId } from './youtube.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
if (existsSync(path.join(root,'.env'))) process.loadEnvFile(path.join(root,'.env'));
const host=process.env.HOST || '127.0.0.1';const token=process.env.MONITOR_API_TOKEN || '';
if (!['127.0.0.1','localhost','::1'].includes(host) && token.length < 24) throw new Error('Set a MONITOR_API_TOKEN of at least 24 characters before exposing the service.');
const budget=Number(process.env.YOUTUBE_DAILY_BUDGET || 1000);
if (!Number.isInteger(budget) || budget < 1 || budget > 10000) throw new Error('Invalid daily request budget');
const app=express();app.disable('x-powered-by');app.use(express.json({limit:'512kb'}));
app.use((_req,res,next)=>{res.set('X-Content-Type-Options','nosniff');res.set('Referrer-Policy','no-referrer');res.set('X-Frame-Options','DENY');next();});
const worker=new WorkerClient(root);const invoke=(a,p)=>worker.invoke(a,p);
const youtube=new YouTube({key:process.env.YOUTUBE_API_KEY,reserve:units=>invoke('quota',{units,budget})});
const locks=new Set(),retryAfter=new Map();let stopping=false;
const rates=new Map();
app.use('/api',(req,res,next)=>{
  res.set('Cache-Control','no-store');
  res.set('Access-Control-Allow-Origin','*');
  res.set('Access-Control-Allow-Methods','GET, POST, PATCH, DELETE, OPTIONS');
  res.set('Access-Control-Allow-Headers','Content-Type, Authorization');
  if (req.method==='OPTIONS') return res.sendStatus(204);
  if (req.path==='/health') return next();
  if (token) {
    const provided=req.headers.authorization?.replace(/^Bearer /,'') || '';
    const a=Buffer.from(provided),b=Buffer.from(token);
    if(a.length!==b.length || !crypto.timingSafeEqual(a,b))return res.status(401).json({error:'Enter your monitoring access token.'});
  }
  const publicPaths=['/health','/analyze','/predict','/scout'];
  const isPublicApi=publicPaths.includes(req.path);
  const origin=req.headers.origin;
  if(!isPublicApi && origin && origin!==`http://${req.headers.host}` && origin!==`https://${req.headers.host}` && origin!==process.env.APP_ORIGIN)return res.status(403).json({error:'Origin is not allowed'});
  if(!['GET','HEAD','OPTIONS'].includes(req.method)){
    if(!req.is('application/json'))return res.status(415).json({error:'Use application/json'});
    const key=req.ip,now=Date.now();let r=rates.get(key);
    if(!r || now-r.start>60000){r={start:now,count:0};rates.set(key,r);}r.count++;
    if(r.count>60)return res.status(429).json({error:'Too many requests; wait one minute.'});
  }
  next();
});
const wrap=fn=>(req,res,next)=>Promise.resolve(fn(req,res)).catch(next);
async function monitor(id){const m=await invoke('get',{id});if(!m){const e=new Error('Monitor not found');e.status=404;throw e;}return m;}
function validate(p){
  if(typeof p?.name!=='string'||p.name.trim().length<3||p.name.length>100)throw new Error('Monitor name must contain 3–100 characters.');
  if(typeof p.target!=='string'||p.target.trim().length<10||p.target.length>500)throw new Error('State a clear target claim in 10–500 characters.');
  if(!Array.isArray(p.videos)||p.videos.length<1||p.videos.length>5)throw new Error('Choose 1–5 YouTube videos.');
  const interval=Number(p.interval_seconds || 300);if(!Number.isInteger(interval)||interval<60||interval>86400)throw new Error('Collection interval must be 60–86400 seconds.');
  return {name:p.name.trim(),target:p.target.trim(),videos:[...new Set(p.videos.map(videoId))],interval_seconds:interval};
}
async function collect(id){
  if(locks.has(id))return {queued:false,status:'already_running'};
  locks.add(id);let run;
  try {
    const m=await monitor(id);run=(await invoke('start',{id})).id;
    const details={videos:[],cursors:{...m.coverage.cursors},top_level_only:true,processed:0,scope:'Selected videos; newest comments plus bounded historical backfill. Replies are not collected.'};
    for(const v of m.videos){
      try {
        const batch=await youtube.collect(v,details.cursors[v]);
        for(let i=0;i<batch.posts.length;i+=64)await invoke('ingest',{id,posts:batch.posts.slice(i,i+64)});
        details.processed+=batch.posts.length;details.cursors[v]=batch.cursor;
        details.videos.push({id:v,count:batch.posts.length,pages:batch.pages,backlog:batch.backlog,status:'success'});
      }catch(e){
        if(e.code==='invalidPageToken')details.cursors[v]=null;
        details.videos.push({id:v,status:'error',error:e.message});
      }
    }
    const errors=details.videos.filter(v=>v.status==='error');
    if(errors.length)details.error=errors.map(v=>`${v.id}: ${v.error}`).join(' ');
    const status=errors.length===m.videos.length?'failed':errors.length?'partial':'success';
    await invoke('finish',{id,run,status,details});
    if(errors.length)retryAfter.set(id,Date.now()+Math.max(m.interval_seconds*1000,300000));else retryAfter.delete(id);
    return {status,...details};
  }catch(e){if(run)await invoke('finish',{id,run,status:'failed',details:{error:e.message}}).catch(()=>{});retryAfter.set(id,Date.now()+300000);throw e;}
  finally{locks.delete(id);}
}
app.get('/api/health',(_req,res)=>res.json({status:'ok',service:'Bhav monitoring',requires_token:Boolean(token)}));
app.get('/api/ready',wrap(async(_req,res)=>{const s=await invoke('status');const ready=s.model_ready&&Boolean(process.env.YOUTUBE_API_KEY);res.status(ready?200:503).json({ready,models_ready:s.model_ready,youtube_configured:Boolean(process.env.YOUTUBE_API_KEY)});}));
app.get('/api/status',wrap(async(_req,res)=>res.json({...await invoke('status'),youtube_configured:Boolean(process.env.YOUTUBE_API_KEY),quota_budget:budget,collecting:[...locks],retention_days:29,deployment:'Single-instance service; persistent SQLite and serialized analysis worker.'})));
app.get('/api/models',(_req,res)=>{const result={};for(const [key,file] of [['sentiment','metrics.json'],['stance','stance_metrics.json']]){try{result[key]=JSON.parse(readFileSync(path.join(root,'artifacts',file),'utf8'));}catch{result[key]=null;}}res.json(result);});
app.get('/api/monitors',wrap(async(_req,res)=>res.json(await invoke('list'))));
app.post('/api/monitors',wrap(async(req,res)=>{if((await invoke('list')).length>=20)return res.status(400).json({error:'Maximum 20 monitors per instance.'});let config;try{config=validate(req.body);}catch(e){return res.status(400).json({error:e.message});}res.status(201).json(await invoke('create',config));}));
app.patch('/api/monitors/:id',wrap(async(req,res)=>{await monitor(req.params.id);if(typeof req.body.enabled!=='boolean')return res.status(400).json({error:'enabled must be true or false'});res.json(await invoke('toggle',{id:req.params.id,enabled:req.body.enabled}));}));
app.delete('/api/monitors/:id',wrap(async(req,res)=>{await monitor(req.params.id);if(locks.has(req.params.id))return res.status(409).json({error:'Wait for the current collection to finish.'});retryAfter.delete(req.params.id);res.json(await invoke('delete',{id:req.params.id}));}));
app.post('/api/monitors/:id/collect',wrap(async(req,res)=>{await monitor(req.params.id);if(!process.env.YOUTUBE_API_KEY)return res.status(503).json({error:'YouTube is not connected. Set YOUTUBE_API_KEY in the server environment and restart.'});if(locks.has(req.params.id))return res.status(409).json({error:'Collection is already running.'});collect(req.params.id).catch(e=>console.error('Collection failed:',e.message));res.status(202).json({status:'collecting'});}));
app.get('/api/monitors/:id/analysis',wrap(async(req,res)=>{await monitor(req.params.id);res.json(await invoke('analysis',{id:req.params.id}));}));
app.post('/api/monitors/:id/review',wrap(async(req,res)=>{await monitor(req.params.id);if(!['Agree','Disagree','No clear stance',null].includes(req.body.label)||typeof req.body.post_id!=='string')return res.status(400).json({error:'Invalid review label or comment ID'});res.json(await invoke('review',{id:req.params.id,post_id:req.body.post_id,label:req.body.label}));}));
app.get('/api/youtube/search',wrap(async(req,res)=>{const q=String(req.query.q||'').trim();if(q.length<3||q.length>200)return res.status(400).json({error:'Search query must contain 3–200 characters'});res.json(await youtube.search(q));}));
app.post(['/api/analyze','/api/predict'],wrap(async(req,res)=>{
  let {target,texts,text}=req.body||{};
  if(!texts && typeof text==='string') texts=[text];
  if(typeof target!=='string'||target.trim().length<10||target.length>500||!Array.isArray(texts)||texts.length<1||texts.length>50||texts.some(t=>typeof t!=='string'||!t.trim()||t.length>5000))
    return res.status(400).json({error:'Provide a target claim and 1–50 comments of at most 5000 characters.'});
  res.json(await invoke('predict',{target:target.trim(),texts:texts.map(t=>t.trim())}));
}));
app.post('/api/scout',wrap(async(req,res)=>{
  const {topic,claim}=req.body||{};
  if(!topic||typeof topic!=='string'||topic.trim().length<2)return res.status(400).json({error:'Provide a topic or keyword to scout.'});
  if(!process.env.YOUTUBE_API_KEY)return res.status(503).json({error:'YouTube is not connected. Set YOUTUBE_API_KEY on server.'});
  const cleanTopic=topic.trim();
  const targetClaim=(claim&&typeof claim==='string'&&claim.trim().length>=10)?claim.trim():`Public sentiment regarding ${cleanTopic} is favorable and positive.`;
  const videos=await youtube.search(cleanTopic);
  if(!videos.length)return res.status(404).json({error:`No recent videos found for "${cleanTopic}"`});
  const allComments=[];
  for(const v of videos.slice(0,2)){
    try{
      const batch=await youtube.collect(v.id,null,1);
      for(const p of batch.posts){if(!allComments.some(x=>x.id===p.id))allComments.push(p);}
    }catch(e){console.warn(`Scout error for ${v.id}:`,e.message);}
  }
  if(!allComments.length)return res.json({topic:cleanTopic,claim:targetClaim,total_comments:0,message:'No public comments available for these videos.',videos:videos.slice(0,3)});
  const sample=allComments.slice(0,25);
  const prediction=await invoke('predict',{target:targetClaim,texts:sample.map(c=>c.text)});
  let agree=0,disagree=0,neutralStance=0,positive=0,negative=0,neutralSent=0;
  const scored=sample.map((c,i)=>{
    const p=prediction.predictions[i];
    if(p.stance.label==='Agree')agree++;else if(p.stance.label==='Disagree')disagree++;else neutralStance++;
    if(p.sentiment.label==='Positive')positive++;else if(p.sentiment.label==='Negative')negative++;else neutralSent++;
    return {id:c.id,text:c.text,likes:c.likes,url:c.url,sentiment:p.sentiment,stance:p.stance};
  });
  const total=scored.length;
  res.json({
    topic:cleanTopic,
    target_claim:targetClaim,
    total_comments:total,
    sentiment:{positive,negative,neutral:neutralSent,positive_pct:Number((positive/total*100).toFixed(1)),negative_pct:Number((negative/total*100).toFixed(1)),neutral_pct:Number((neutralSent/total*100).toFixed(1))},
    stance:{agree,disagree,neutral:neutralStance,agree_pct:Number((agree/total*100).toFixed(1)),disagree_pct:Number((disagree/total*100).toFixed(1)),neutral_pct:Number((neutralStance/total*100).toFixed(1))},
    verdict:disagree>agree?'Public Friction & Discontent Detected':agree>disagree?'Strong Public Approval & Agreement':'Mixed / Observational Reception',
    videos:videos.slice(0,3),
    sample_comments:scored.slice(0,8)
  });
}));
app.use('/api',(_req,res)=>res.status(404).json({error:'Unknown API route'}));
app.use(express.static(path.join(root,'frontend/dist')));app.get('*',(_req,res)=>res.sendFile(path.join(root,'frontend/dist/index.html')));
app.use((error,_req,res,_next)=>res.status(error.status|| (error instanceof SyntaxError?400:503)).json({error:error.message||'Request failed'}));
const server=app.listen(Number(process.env.PORT||3001),host,()=>console.log(`Bhav monitoring: http://${host}:${server.address().port}`));
let ticking=false;
const scheduler=setInterval(async()=>{
  if(ticking||stopping)return;ticking=true;
  try {
    await invoke('prune');
    for(const [key,r] of rates)if(Date.now()-r.start>60000)rates.delete(key);
    if(!process.env.YOUTUBE_API_KEY)return;
    for(const m of await invoke('list')){
      if(!m.enabled||locks.has(m.id)||(retryAfter.get(m.id)||0)>Date.now())continue;
      if(!m.last_attempt||Date.now()-Date.parse(m.last_attempt)>=m.interval_seconds*1000)await collect(m.id);
    }
  }catch(e){console.error('Scheduler:',e.message);}finally{ticking=false;}
},15000);scheduler.unref();
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{stopping=true;clearInterval(scheduler);server.close(()=>{worker.close();process.exit(0);});setTimeout(()=>{worker.close();process.exit(0);},10000).unref();});
