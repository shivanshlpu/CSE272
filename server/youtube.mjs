// Official YouTube Data API; never scrape, simulate, or invent engagement.
export class ProviderError extends Error {
  constructor(message, code = 'provider_error') { super(message); this.code = code; }
}
export function videoId(value) {
  if (typeof value !== 'string') throw new ProviderError('Invalid video link');
  let id = value.trim();
  if (!/^[\w-]{11}$/.test(id)) {
    let u; try { u = new URL(id); } catch { throw new ProviderError('Use a YouTube URL or 11-character video ID'); }
    if (!['https:', 'http:'].includes(u.protocol)) throw new ProviderError('Invalid URL protocol');
    if (u.hostname === 'youtu.be') id = u.pathname.slice(1).split('/')[0];
    else if (['youtube.com','www.youtube.com','m.youtube.com'].includes(u.hostname)) id = u.searchParams.get('v') || u.pathname.split('/')[2];
    else throw new ProviderError('Only YouTube video links are supported');
  }
  if (!/^[\w-]{11}$/.test(id || '')) throw new ProviderError('Invalid YouTube video ID');
  return id;
}
export class YouTube {
  constructor({ key, reserve, fetcher = fetch, sleep = ms => new Promise(r => setTimeout(r, ms)) }) {
    this.key = key; this.reserve = reserve; this.fetcher = fetcher; this.sleep = sleep;
  }
  async request(resource, params, cost = 1) {
    if (!this.key) throw new ProviderError('Set YOUTUBE_API_KEY on the server to collect public comments.', 'not_configured');
    for (let attempt = 0; attempt < 3; attempt++) {
      await this.reserve(cost);
      const url = new URL(`https://www.googleapis.com/youtube/v3/${resource}`);
      for (const [k,v] of Object.entries({ ...params, key: this.key })) if (v) url.searchParams.set(k, v);
      let response;
      try { response = await this.fetcher(url, { signal: AbortSignal.timeout(20000) }); }
      catch {
        if (attempt < 2) { await this.sleep(500 * 2 ** attempt); continue; }
        throw new ProviderError('YouTube request timed out or could not connect.', 'network');
      }
      let body; try { body = await response.json(); } catch { throw new ProviderError('Invalid YouTube response'); }
      if (response.ok) return body;
      const code = body.error?.errors?.[0]?.reason || `http_${response.status}`;
      if ((response.status === 429 || response.status >= 500) && attempt < 2) { await this.sleep(500 * 2 ** attempt); continue; }
      const messages = { commentsDisabled: 'Comments are disabled for this video.', quotaExceeded: 'YouTube project quota exhausted.', keyInvalid: 'YouTube API key is invalid.', accessNotConfigured: 'Enable YouTube Data API v3 for this API key.', videoNotFound: 'Video is unavailable or was removed.' };
      throw new ProviderError(messages[code] || `YouTube rejected the request (${code}).`, code);
    }
  }
  async search(query) {
    const body = await this.request('search', { part:'snippet', q:query, type:'video', maxResults:'10', order:'relevance' }, 100);
    return (body.items || []).map(x => ({ id:x.id.videoId, title:x.snippet.title, channel:x.snippet.channelTitle, published_at:x.snippet.publishedAt, url:`https://www.youtube.com/watch?v=${x.id.videoId}` }));
  }
  async collect(id, cursor = null, maxPages = 3) {
    const posts = new Map(); let next = null; let pages = 0;
    // Always refresh newest comments, then continue the persisted historical cursor.
    for (let page = 0; page < maxPages; page++) {
      const body = await this.request('commentThreads', { part:'snippet', videoId:id, maxResults:'100', order:'time', textFormat:'plainText', pageToken:page === 0 ? null : next });
      pages++;
      for (const thread of body.items || []) {
        const comment = thread.snippet?.topLevelComment; const s = comment?.snippet;
        if (!comment?.id || !s?.textDisplay || !Number.isFinite(Date.parse(s.publishedAt))) continue;
        posts.set(comment.id, { id:comment.id, video_id:id, text:s.textDisplay, published_at:new Date(s.publishedAt).toISOString(), updated_at:new Date(s.updatedAt || s.publishedAt).toISOString(), likes:Number(s.likeCount || 0), url:`https://www.youtube.com/watch?v=${id}&lc=${encodeURIComponent(comment.id)}` });
      }
      next = page === 0 && cursor ? cursor : body.nextPageToken || null;
      if (!next) break;
    }
    return { posts:[...posts.values()], cursor:next, pages, backlog:Boolean(next) };
  }
}
