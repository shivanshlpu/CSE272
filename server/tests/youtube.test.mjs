import test from 'node:test';
import assert from 'node:assert/strict';
import {YouTube,videoId} from '../youtube.mjs';
const response=(body,status=200)=>({ok:status<400,status,json:async()=>body});
const item=(id,text='Comment')=>({snippet:{topLevelComment:{id,snippet:{textDisplay:text,publishedAt:'2026-11-15T12:00:00Z',updatedAt:'2026-11-15T13:00:00Z',likeCount:7}}}});
test('accepts YouTube video URLs and rejects foreign or malformed links',()=>{
 assert.equal(videoId('https://youtu.be/CswOUBuokjo?t=20'),'CswOUBuokjo');
 assert.equal(videoId('https://www.youtube.com/watch?v=CswOUBuokjo'),'CswOUBuokjo');
 assert.throws(()=>videoId('https://evil.test/watch?v=CswOUBuokjo'));
 assert.throws(()=>videoId('javascript:alert(1)'));
});
test('pagination refreshes newest, resumes persisted backfill and deduplicates IDs',async()=>{
 const tokens=[];let units=0;
 const client=new YouTube({key:'fixture-only',reserve:async n=>units+=n,fetcher:async url=>{
  tokens.push(url.searchParams.get('pageToken'));
  if(tokens.length===1)return response({items:[item('a')],nextPageToken:'new-page'});
  if(tokens.length===2)return response({items:[item('a'),item('b')],nextPageToken:'older'});
  return response({items:[item('c')],nextPageToken:'oldest'});
 }});
 const result=await client.collect('CswOUBuokjo','saved');
 assert.deepEqual(tokens,[null,'saved','older']);assert.equal(result.posts.length,3);assert.equal(result.cursor,'oldest');assert.equal(result.backlog,true);assert.equal(units,3);
 assert.equal(result.posts[0].likes,7);assert.equal(result.posts[0].published_at,'2026-11-15T12:00:00.000Z');
 assert.ok(!('followers' in result.posts[0]));
});
test('retries transient failures and counts every attempt',async()=>{
 let calls=0,units=0;
 const client=new YouTube({key:'fixture-only',reserve:async n=>units+=n,sleep:async()=>{},fetcher:async()=>++calls<3?response({error:{}},503):response({items:[]})});
 await client.collect('CswOUBuokjo');assert.equal(calls,3);assert.equal(units,3);
});
test('commentsDisabled is surfaced without retry or credential disclosure',async()=>{
 let calls=0;const client=new YouTube({key:'private-test-token',reserve:async()=>{},fetcher:async()=>{calls++;return response({error:{errors:[{reason:'commentsDisabled'}]}},403);}});
 await assert.rejects(()=>client.collect('CswOUBuokjo'),e=>e.code==='commentsDisabled'&&!e.message.includes('private-test-token'));assert.equal(calls,1);
});
test('missing credential never makes a request',async()=>{
 const client=new YouTube({key:'',reserve:()=>assert.fail('quota should not be reserved'),fetcher:()=>assert.fail('should not call provider')});
 await assert.rejects(()=>client.collect('CswOUBuokjo'),e=>e.code==='not_configured');
});
test('search reserves the official 100-unit request cost',async()=>{
 let units=0;const client=new YouTube({key:'fixture-only',reserve:async n=>units+=n,fetcher:async()=>response({items:[]})});
 await client.search('transport policy');assert.equal(units,100);
});
