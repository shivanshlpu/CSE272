import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import crypto from 'node:crypto';
import path from 'node:path';
export class WorkerClient {
  constructor(root) { this.root = root; this.child = null; this.pending = new Map(); }
  start() {
    const child = spawn(process.env.PYTHON_BIN || path.join(this.root,'.venv/bin/python'), ['-u','-m','ml.monitor_worker'], { cwd:this.root, env:{...process.env,HF_HUB_OFFLINE:'1',TOKENIZERS_PARALLELISM:'false'}, stdio:['pipe','pipe','pipe'] });
    this.child = child;
    createInterface({input:child.stdout}).on('line',line => {
      try {
        const message = JSON.parse(line), item = this.pending.get(message.id);
        if (!item) return; clearTimeout(item.timer); this.pending.delete(message.id);
        message.error ? item.reject(new Error(message.error)) : item.resolve(message.result);
      } catch { console.error('Malformed inference worker response'); }
    });
    child.stderr.on('data',chunk => process.stderr.write(chunk));
    const fail = () => {
      if (this.child !== child) return;
      this.child = null;
      for (const item of this.pending.values()) { clearTimeout(item.timer); item.reject(new Error('Analysis worker unavailable; retry shortly.')); }
      this.pending.clear();
    };
    child.on('error',fail); child.on('exit',fail); child.stdin.on('error',fail);
  }
  invoke(action,payload={}) {
    if (this.pending.size >= 12) return Promise.reject(new Error('Analysis queue is full. Retry shortly.'));
    if (!this.child) this.start();
    return new Promise((resolve,reject) => {
      const id=crypto.randomUUID(); const child=this.child;
      const timer=setTimeout(() => { child.kill(); },180000);
      this.pending.set(id,{resolve,reject,timer});
      child.stdin.write(JSON.stringify({id,action,payload})+'\n',error => { if(error)child.kill(); });
    });
  }
  close() { this.child?.kill(); }
}
