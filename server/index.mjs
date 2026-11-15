import express from 'express';
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import crypto from 'node:crypto';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const app = express();
app.disable('x-powered-by');
app.use(express.json({ limit: '256kb' }));

let worker = null;
const pending = new Map();
const inMemoryLiveFeed = [];

const SIMULATION_POOL = [
  { text: "UPI transaction timed out but amount deducted from account! Please resolve @Paytm @HDFC_Bank", author: "rahul_v", lang: "en", followers: 3200, likes: 85, replies: 12, source: "Twitter / X" },
  { text: "Zomato delivery reached in 12 mins piping hot, superb service as always! ❤️", author: "priya_foodie", lang: "en", followers: 8500, likes: 210, replies: 18, source: "Instagram" },
  { text: "Wah kya baat hai 5G bol kar 2G speed bhi nahi aa rahi shabaash!", author: "amit_sharma", lang: "hi-en", followers: 1400, likes: 64, replies: 9, source: "Twitter / X" },
  { text: "IRCTC refund ticket cancel hone ke 2 ghante me account me aa gaya, badhiya update!", author: "desi_traveler", lang: "hi-en", followers: 6200, likes: 142, replies: 11, source: "Reddit" },
  { text: "यह सेवा अत्यंत तेज और विश्वसनीय है। कस्टमर केयर टीम ने तुरंत सहायता प्रदान की।", author: "vikram_aditya", lang: "hi", followers: 4100, likes: 98, replies: 5, source: "Koo / Web" },
  { text: "Bhai delivery guy ne order cancel kar diya bina call kiye! Bahut hi ghatiya experience hai.", author: "anand_k", lang: "hi-en", followers: 980, likes: 35, replies: 7, source: "Consumer Forum" },
  { text: "Fastest customer support ever, ticket resolved within 10 minutes. Kudos team!", author: "shreya_tech", lang: "en", followers: 12400, likes: 320, replies: 24, source: "Twitter / X" },
  { text: "रेलवे स्टेशन पर वाईफाई और स्वच्छता में बहुत सुधार हुआ है, धन्यवाद रेल मंत्रालय।", author: "rajesh_kumar", lang: "hi", followers: 2300, likes: 76, replies: 8, source: "X Public" },
  { text: "FREE GIFT! Click bit.ly/free-voucher to win 10,000 cash prize instantly hurry limited offer!!!", author: "promo_bot99", lang: "en", followers: 4, likes: 650, replies: 0, source: "Spam Ring", is_bot: true }
];

let simIndex = 0;

function startWorker() {
  worker = spawn(process.env.PYTHON_BIN || path.join(root, '.venv/bin/python'), ['-u', '-m', 'ml.worker'], {
    cwd: root,
    env: { ...process.env, HF_HUB_OFFLINE: '1', TOKENIZERS_PARALLELISM: 'false' },
    stdio: ['pipe', 'pipe', 'pipe']
  });

  createInterface({ input: worker.stdout }).on('line', (line) => {
    try {
      const message = JSON.parse(line);
      const item = pending.get(message.id);
      if (item) {
        clearTimeout(item.timer);
        pending.delete(message.id);
        message.error ? item.reject(new Error(message.error)) : item.resolve(message.result);
      }
    } catch {
      console.error('Invalid worker response');
    }
  });

  worker.stderr.on('data', (data) => process.stderr.write(data));

  const fail = () => {
    worker = null;
    for (const item of pending.values()) {
      clearTimeout(item.timer);
      item.reject(new Error('Python worker stopped'));
    }
    pending.clear();
  };

  worker.on('exit', fail);
  worker.on('error', fail);
}

function invoke(action, payload) {
  if (pending.size >= 8) return Promise.reject(new Error('Inference queue full; retry shortly'));
  if (!worker) startWorker();
  return new Promise((resolve, reject) => {
    const id = crypto.randomUUID();
    const timer = setTimeout(() => {
      pending.delete(id);
      reject(new Error('Inference timed out'));
      worker?.kill();
    }, 180000);
    pending.set(id, { resolve, reject, timer });
    worker.stdin.write(JSON.stringify({ id, action, payload }) + '\n');
  });
}

// ---------------- API ROUTES ----------------

app.get('/api/health', (_req, res) =>
  res.json({
    status: existsSync(path.join(root, 'artifacts/metrics.json')) ? 'ready' : 'training',
    architecture: 'React → Express Ingestion Gateway → Local PyTorch Hybrid Engine',
    queue: pending.size,
    live_feed_count: inMemoryLiveFeed.length
  })
);

app.get('/api/model', (_req, res) => {
  try {
    res.json(JSON.parse(readFileSync(path.join(root, 'artifacts/metrics.json'), 'utf8')));
  } catch {
    res.status(503).json({ error: 'Training artifacts are not ready. Run python -m ml.train.' });
  }
});

// Explore dataset + in-memory live stream
app.get('/api/explore', async (req, res) => {
  try {
    const lang = String(req.query.lang || 'all');
    if (!['all', 'en', 'hi', 'hi-en'].includes(lang)) return res.status(400).json({ error: 'Invalid language' });
    const query = String(req.query.query || '').slice(0, 200);
    const data = await invoke('explore', { lang, query });
    
    // Prepend relevant in-memory live posts
    const matchingLive = inMemoryLiveFeed.filter((p) => {
      if (lang !== 'all' && p.lang !== lang) return false;
      if (query && !p.text.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });

    if (matchingLive.length > 0) {
      data.records = [...matchingLive, ...data.records];
      data.shown = data.records.length;
      data.matched += matchingLive.length;
    }
    
    res.json(data);
  } catch (e) {
    res.status(503).json({ error: e.message });
  }
});

// Real-time text prediction
app.post('/api/predict', async (req, res) => {
  const texts = req.body?.texts;
  if (!Array.isArray(texts) || texts.length < 1 || texts.length > 100 || texts.some((t) => typeof t !== 'string' || !t.trim() || t.length > 5000)) {
    return res.status(400).json({ error: 'Provide 1–100 nonempty texts of at most 5,000 characters each.' });
  }
  try {
    res.json(await invoke('predict', { texts }));
  } catch (e) {
    res.status(503).json({ error: e.message });
  }
});

// Production Ingestion Endpoint: external crawlers, webhooks, or frontend push
app.post('/api/ingest', async (req, res) => {
  try {
    const body = req.body;
    let postsToIngest = [];
    if (Array.isArray(body?.posts)) {
      postsToIngest = body.posts;
    } else if (body?.text && typeof body.text === 'string') {
      postsToIngest = [body];
    } else {
      return res.status(400).json({ error: 'Provide a valid post object {text, author, lang} or posts array.' });
    }

    const outcome = await invoke('ingest', { posts: postsToIngest });
    const enriched = outcome.ingested_posts || [];
    for (const p of enriched) {
      inMemoryLiveFeed.unshift(p);
    }
    if (inMemoryLiveFeed.length > 200) inMemoryLiveFeed.length = 200;

    res.json({
      success: true,
      message: `${enriched.length} post(s) ingested and analyzed successfully.`,
      count: enriched.length,
      posts: enriched
    });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Live Feed fetch endpoint
app.get('/api/feed', (_req, res) => {
  res.json({
    count: inMemoryLiveFeed.length,
    posts: inMemoryLiveFeed
  });
});

// Simulate incoming live social media stream
app.post('/api/simulate', async (_req, res) => {
  try {
    const candidate = { ...SIMULATION_POOL[simIndex % SIMULATION_POOL.length] };
    simIndex++;
    candidate.likes = Math.floor(candidate.likes * (0.85 + Math.random() * 0.3));
    const outcome = await invoke('ingest', { posts: [candidate] });
    const enriched = outcome.ingested_posts?.[0];
    if (enriched) {
      inMemoryLiveFeed.unshift(enriched);
      if (inMemoryLiveFeed.length > 200) inMemoryLiveFeed.length = 200;
    }
    res.json({ success: true, post: enriched, total_live: inMemoryLiveFeed.length });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Random unseen sample prompt generator for Tester
app.get('/api/random-sample', async (req, res) => {
  try {
    const lang = String(req.query.lang || 'all');
    res.json(await invoke('random_sample', { lang }));
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.use('/api', (_req, res) => res.status(404).json({ error: 'Unknown API route' }));
app.use(express.static(path.join(root, 'frontend/dist')));
app.get('*', (_req, res) => res.sendFile(path.join(root, 'frontend/dist/index.html')));
app.use((err, _req, res, _next) => res.status(400).json({ error: 'Invalid request body' }));

const server = app.listen(Number(process.env.PORT || 3001), '127.0.0.1', () =>
  console.log('Bhav running at http://127.0.0.1:' + server.address().port)
);

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => {
    worker?.kill();
    server.close(() => process.exit(0));
  });
}
