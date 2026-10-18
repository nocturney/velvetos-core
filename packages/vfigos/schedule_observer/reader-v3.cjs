'use strict';

/**
 * Velvet Factory Meta Business Suite | read-only Scheduled inspector.
 * Allowed: read visible DOM text/visible table rows, click "Scheduled" tab, scroll list.
 * Forbidden: private endpoints, credentials/cookies/storage, publication, editing, ad actions.
 */
const fs = require('node:fs');
const path = require('node:path');
const puppeteer = require('puppeteer-core');

const profileDir = 'D:/Velvet/State/MetaPlannerReader/chrome-profile';
const outDir = 'D:/Velvet/Artifacts/MetaPlannerReader';
const sourceUrl = 'https://business.facebook.com/latest/posts/scheduled_posts?asset_id=1347173051801983&business_id=1762458094689506';
const statusPath = path.join(outDir,'status-v3.json');
const snapPath = path.join(outDir,'scheduled-v3-snapshot.json');
const screenshotPath = path.join(outDir,'scheduled-v3-screen.png');
let browser, exited=false, isScanning=false, observations=0;
const ONCE = process.argv.includes('--once');
const HEADLESS = process.argv.includes('--headless');
fs.mkdirSync(outDir,{recursive:true});
function wait(ms){return new Promise(r=>setTimeout(r,ms))}
function write(file,value){fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n',{encoding:'utf8'})}
function iso(){return new Date().toISOString()}
function status(phase,fields={}){write(statusPath,{schema:'velvet.meta_planner_reader.status.v3',timestamp:iso(),phase,mode:'UI_ONLY_READ',observations,...fields})}
const errMsg=e=>String(e?.message||e||'unknown').split(/\r?\n/)[0].replace(/https?:\/\/\S+/g,'[URL]').slice(0,240);
function unique(list){return [...new Set(list)]}
async function gather(page) {
 return page.evaluate(()=>{
  const visible=(el)=>{
    try {
      const r=el.getBoundingClientRect(), s=getComputedStyle(el);
      return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';
    } catch{return false}
  };
  const norm=t=>(t||'').replace(/\u200b/g,'').replace(/[ \t]+/g,' ').trim();
  const rows=[...document.querySelectorAll('tr,[role="row"],[data-testid*="row"]')]
    .filter(visible)
    .map(el=>norm(el.innerText).slice(0,1600))
    .filter(s=>s&&s.length>8).slice(0,300);
  const tabs=[...document.querySelectorAll('[role="tab"]')]
    .filter(visible).map(el=>({text:norm(el.innerText||el.getAttribute('aria-label')),selected:el.getAttribute('aria-selected')}));
  const scrollables=[...document.querySelectorAll('*')].filter(el=>{
    if(!visible(el))return false;
    const h=el.clientHeight,w=el.clientWidth;
    if(h<110||h>1400||w<380||el.scrollHeight-h<55)return false;
    const overflow=getComputedStyle(el).overflowY;
    return /auto|scroll/.test(overflow) || el.scrollHeight > h+120;
  }).map((el,i)=>{
    const text=norm(el.innerText||'');
    return {candidate:i,tag:el.tagName,clientHeight:el.clientHeight,scrollHeight:el.scrollHeight,
     scrollTop:el.scrollTop,overflowY:getComputedStyle(el).overflowY,
     likelyTable:/Date scheduled|Status|תאריך תזמון|Scheduled/i.test(text.slice(0,2000)),
     visibleRowCount:el.querySelectorAll('tr,[role="row"]').length};
  }).slice(0,50);
  const content=(document.body?.innerText||'').slice(0,60000);
  return {url:location.href,title:document.title,bodyText:content,rows,tabs,scrollables};
 });
}
async function scrollTable(page) {
 return page.evaluate(()=>{
   const visible=el=>{try{const r=el.getBoundingClientRect();return r.width>0&&r.height>0}catch{return false}};
   const options=[...document.querySelectorAll('*')].filter(el=>{
     if(!visible(el))return false;
     if(el.clientHeight<110||el.clientHeight>1400||el.clientWidth<380)return false;
     if(el.scrollHeight-el.clientHeight<55)return false;
     const overflow=getComputedStyle(el).overflowY;
     return /auto|scroll/.test(overflow) || el.scrollHeight>el.clientHeight+120;
   });
   const ranked=options.map(el=>{
     const text=(el.innerText||'').slice(0,2000);
     let score=0;
     if(/Date scheduled|תאריך תזמון/i.test(text)) score+=100;
     if(/Title[\s\S]{0,100}Date scheduled|Scheduled/i.test(text)) score+=35;
     if(el.querySelector('tr,[role="row"]'))score+=70;
     if(el.clientHeight<800)score+=20;
     if(el.scrollHeight-el.clientHeight>300)score+=10;
     if(el===document.body||el===document.documentElement)score-=80;
     return {el,score};
   }).sort((a,b)=>b.score-a.score);
   if(!ranked.length)return {scrolled:false,reason:'NO_SCROLLABLE_CONTAINER'};
   const el=ranked[0].el;
   const before=el.scrollTop, max=el.scrollHeight-el.clientHeight;
   const delta=Math.max(200, Math.round(el.clientHeight*.8));
   el.scrollTop=Math.min(max,before+delta);
   return {scrolled:el.scrollTop>before,previous:before,current:el.scrollTop,max,delta,
       selectedScore:ranked[0].score,tag:el.tagName,clientHeight:el.clientHeight,
       scrollHeight:el.scrollHeight};
 });
}
async function scan(page){
 if(isScanning)return;
 isScanning=true;
 try {
  const url=page.url();
  if(/\/business\/loginpage|\/login\//.test(url)){
    status('WAITING_FOR_LOGIN',{page_url:url.slice(0,280)});
    return;
  }
  if(!url.includes('/latest/posts')){
    status('WAITING_FOR_CONTENT_PAGE',{page_url:url.slice(0,280)});
    return;
  }
  await wait(1600);
  const tab=await page.evaluate(()=>{
    const el=[...document.querySelectorAll('[role="tab"]')].find(e=>/^Scheduled$/i.test((e.innerText||'').trim()));
    if(!el)return {found:false};
    if(el.getAttribute('aria-selected')==='true')return {found:true,clicked:false};
    el.click();return {found:true,clicked:true};
  });
  if(tab.clicked)await wait(2200);
  let allRows=[], scans=[], seen=new Set(), lastScroll=null, stall=0;
  for(let step=0;step<32;step++){
    const info=await gather(page);
    if(!/^https:\/\/business\.facebook\.com\/latest\/posts/.test(info.url))break;
    const relevant=info.rows.filter(s=>s.length>10&&!/^\s*(Title|Privacy|Status|Date scheduled)\s*$/i.test(s));
    for(const s of relevant){
      if(!seen.has(s)){seen.add(s);allRows.push(s)}
    }
    scans.push({step,at:iso(),rowCount:info.rows.length,tabInfo:info.tabs,
        scrollableCount:info.scrollables.length,bodyText:info.bodyText.slice(0,42000),
        rows:info.rows,scrollState:lastScroll});
    if(step===0){
      try{await page.screenshot({path:screenshotPath,type:'png',captureBeyondViewport:false})}catch{}
    }
    const next=await scrollTable(page);
    lastScroll=next;
    if(!next.scrolled){
      if(step===0)await wait(1700);
      else break;
    } else await wait(900);
    if(step>0 && scans[step].rowCount===0)stall++;
    else stall=0;
    if(stall>=4)break;
  }
  observations=allRows.length;
  const out={schema:'velvet.meta_planner_reader.scheduled.v3',source:'meta_business_suite_visible_ui',
    observed_at:iso(),account_expected:'velvets_cloud',page_url:page.url(),
    scheduled_selected:scans.some(p=>p.tabInfo.some(t=>t.text==='Scheduled'&&t.selected==='true')),
    first_screenshot:screenshotPath,unique_rows:allRows,scans,restrictions:
    ['No cookies','No tokens','No private GraphQL','No network responses','No publishing','No editing','No ad actions']};
  write(snapPath,out);
  status('SCAN_COMPLETE',{rows:allRows.length,steps:scans.length,selected:out.scheduled_selected,
    snapshot_path:snapPath,message:'Read-only scheduled list captured from Meta UI'});
 } catch(e){status('SCAN_ERROR',{error:errMsg(e)})}
 finally{isScanning=false}
}
async function stop(){if(exited)return;exited=true;try{await browser?.close()}catch{}status('STOPPED');process.exit(0)}
async function main(){
 status('STARTING');
 browser=await puppeteer.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',
   headless:HEADLESS,pipe:true,userDataDir:profileDir,defaultViewport:null,
   args:['--no-first-run','--no-default-browser-check','--window-size=1480,920'],timeout:60000});
 browser.on('disconnected',()=>{if(!exited){exited=true;status('BROWSER_CLOSED');process.exit(0)}});
 let page=(await browser.pages())[0];if(!page)page=await browser.newPage();
 try{await page.goto(sourceUrl,{waitUntil:'domcontentloaded',timeout:60000})}
 catch(e){status('NAVIGATION_WAITING',{error:errMsg(e)})}
 await scan(page);
 if (ONCE) { exited=true; try { await browser.close(); } catch {} process.exit(0); }
 setInterval(async()=>{if(!isScanning&&browser){const p=(await browser.pages()).find(x=>/business\.facebook\.com\/latest\/posts/.test(x.url()));if(p&&p.url()!==page.url())page=p}},10000);
 setTimeout(stop,20*60*1000);
}
process.on('unhandledRejection',e=>{try{status('UNHANDLED_REJECTION',{error:errMsg(e)})}catch{}});
main().catch(e=>{status('LAUNCH_FAILED',{error:errMsg(e)});process.exitCode=1});
