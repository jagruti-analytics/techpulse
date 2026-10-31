/* Intelligent feeds extension: safe rendering and fallbacks */
(()=>{
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const safe=v=>{try{const u=new URL(v);return ['http:','https:'].includes(u.protocol)?u.href:'#'}catch{return '#'}};
 const day=v=>{const d=new Date(v);return Number.isNaN(+d)?'Date unavailable':d.toLocaleDateString('en-US',{month:'short',day:'numeric'})};
 const block=(id,items,empty,tag='news')=>{const el=document.getElementById(id);if(!el)return;if(!items?.length){el.innerHTML=`<div class="section-empty">${esc(empty)}</div>`;return}el.innerHTML=items.slice(0,6).map(a=>tag==='repo'?`<article class="repo-card"><div class="insight-meta"><span class="signal">${esc(a.language||'Open source')}</span><span class="repo-stars">★ ${Number(a.stars||0).toLocaleString()} stars</span></div><h3>${esc(a.name)}</h3><p>${esc(a.description||'Open-source project on GitHub')}</p><div class="insight-meta">Created ${esc(day(a.created_at))}</div><a href="${esc(safe(a.url))}" target="_blank" rel="noopener noreferrer">View repository ↗</a></article>`:`<article class="insight-card"><div class="insight-meta"><span class="signal">${esc(a.category||'Tech')}</span><span>${esc(a.source||'Publisher')}</span><span>• ${esc(day(a.published))}</span></div><h3>${esc(a.title)}</h3><p>${esc(a.summary||'Read the original story for details.')}</p><a href="${esc(safe(a.url))}" target="_blank" rel="noopener noreferrer">Read original ↗</a></article>`).join('')};
 async function getJson(file){const r=await fetch(file+'?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(r.status);return r.json()}
 async function start(){let data=null;try{data=await getJson('./data/insights.json')}catch{}let items=[];if(!data){try{const old=await getJson('./data/articles.json');items=old.articles||[]}catch{}}
 const releaseRe=/\b(releas(?:ed|es|ing)?|launch(?:es|ed)?|update(?:s|d)?|upgrade(?:s|d)?|version|new feature|general availability|rollout|changelog|preview|introduc(?:es|ed|ing)|now available)\b/i;
 const aiRe=/\b(ai|artificial intelligence|llm|language model|agent|reasoning|deepmind|openai|claude|gemini|gpt|transformer|machine learning)\b/i;
 const trend=data?.trending||items.slice(0,6), ai=data?.ai_breakthroughs||items.filter(a=>a.category==='AI'&&aiRe.test(a.title)).slice(0,6), releases=data?.technology_releases||items.filter(a=>releaseRe.test(a.title)).slice(0,6);
 block('trendingStories',trend,'Trending signals appear after the next successful feed refresh.');block('aiBreakthroughs',ai,'No AI breakthrough headlines are available in the current feed.');block('technologyReleases',releases,'No new technology releases were detected in the current feed.');
 let repos=data?.github_projects||[];if(!repos.length){try{const p=await getJson('./data/github-trending.json');repos=p.repositories||[]}catch{}}block('githubTrending',repos,'GitHub projects are unavailable right now. The next scheduled refresh will try again.','repo');
 const el=document.getElementById('trendCount');if(el)el.textContent=trend.length?`${trend.length} highlights`:'';
 }start();
})();
