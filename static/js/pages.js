const data=globalThis.DEMO_DATA,logic=globalThis.DemoLogic;
const fields=[...document.querySelectorAll('#quiz fieldset')],next=document.querySelector('#next'),previous=document.querySelector('#previous'),error=document.querySelector('#quiz-error');
let current=0,busy=false,run=0,result=null;
const escapeHTML=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function show(page){
  ['home','test','analyzing','result'].forEach(p=>document.querySelector('#view-'+p).hidden=p!==page);
  window.scrollTo(0,0);
}
function question(){fields.forEach((f,i)=>f.hidden=i!==current);document.querySelector('#question-count').textContent=`질문 ${current+1} / 10`;document.querySelector('#quiz-progress').value=current+1;previous.disabled=current===0;next.disabled=false;next.textContent=current===9?'내 투자 성향 분석하기 →':'다음 질문 →';error.textContent='';}
function route(){
  let page=location.hash.slice(1)||'home';
  if(!['home','test','analyzing','result'].includes(page)||page==='result'&&!result||page==='analyzing'&&!busy){page='home';history.replaceState(null,'','#home');}
  if(page!=='analyzing'&&busy){run++;busy=false;}
  if(page==='test')question();show(page);
}
window.addEventListener('hashchange',route);
previous.onclick=()=>{if(!busy&&current>0){current--;question();}};
next.onclick=()=>{
  if(busy)return;
  if(!fields[current].querySelector('input:checked')){error.textContent='답변 하나를 선택해주세요.';return;}
  if(current<9){current++;question();return;}
  analyze();
};
document.querySelector('#quiz').onsubmit=e=>{e.preventDefault();next.click();};
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function analyze(){
  busy=true;next.disabled=true;const token=++run;
  location.hash='analyzing';show('analyzing');
  const title=document.querySelector('#analysis-title'),bar=document.querySelector('#analysis-progress'),first=document.querySelector('#stage-profile'),second=document.querySelector('#stage-portfolio');
  document.querySelector('#analysis-error').textContent='';title.textContent='투자 성향을 분석하고 있습니다...';first.textContent='투자 성향 분석 중';first.className='active';second.textContent='주식 데이터 비교 및 포트폴리오 구성 대기';second.className='';bar.value=15;
  try{
    const answers=fields.map(f=>{const input=f.querySelector('input:checked');return input?Number(input.value):null;});
    const p=logic.profile(answers,data);await wait(650);if(token!==run)return;
    first.textContent='✓ 투자 성향 분석 완료';first.className='done';bar.value=50;title.textContent='주식 데이터를 비교하고 있습니다...';second.className='active';second.textContent='주식 데이터 비교 및 포트폴리오 구성 중';
    const portfolio=logic.portfolio(p,data.stocks);await wait(650);if(token!==run)return;
    result={profile:p,portfolio};renderResult();bar.value=100;title.textContent='맞춤 포트폴리오 생성 완료';second.textContent='✓ 맞춤 포트폴리오 생성 완료';second.className='done';
    await wait(400);if(token!==run)return;busy=false;location.hash='result';
  }catch(e){busy=false;document.querySelector('#analysis-error').textContent=e.message;title.textContent='분석을 완료하지 못했습니다';next.disabled=false;}
}
function renderResult(){
  const p=result.profile,pf=result.portfolio,rows=pf.recommendations,esc=escapeHTML;
  const scores=Object.entries(data.scores).map(([k,label])=>`<div class="row"><span>${esc(label)}</span><b>${p[k]} <small>/ 10</small></b></div><progress max="10" value="${p[k]}" aria-label="${esc(label)}"></progress>`).join('');
  const cards=rows.map((r,i)=>{
    const s=data.stocks.find(s=>s.ticker===r.ticker);
    const metrics=[['예상 상승 여력',`${s.expected_upside>=0?'+':''}${s.expected_upside}%`],['애널리스트 신뢰도',`${s.analyst_confidence}/10`],['위험 수준',`${s.risk_score>=7?'높음':s.risk_score>=4?'중간':'낮음'} · ${s.risk_score}`],['변동성',`${s.volatility}/10`],['최대 낙폭 위험',`${s.max_drawdown}/10`],['애널리스트 의견',s.analyst_consensus],['평균 목표가',`$${s.average_price_target}`],['최저 ~ 최고 목표가',`$${s.low_price_target} ~ $${s.high_price_target}`]];
    return `<article class="card stock-card"><div class="row"><span class="ticker color-${i+1}">${esc(r.ticker)}</span><span class="muted small">매칭 ${r.match_score}점</span></div><h3>${esc(s.company_name)}</h3><p class="muted small">${esc(s.sector)}</p><div class="weight">${r.allocation}<small>% 추천 비중</small></div><dl>${metrics.map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl><div class="reason"><h4>왜 이 종목이 나와 잘 맞을까요?</h4><p>${esc(r.reason)}</p></div></article>`;
  }).join('');
  document.querySelector('#view-result').innerHTML=`<div class="row result-heading"><div><span class="eyebrow">나의 투자 성향</span><h1>나를 이해하면,<br>조합이 달라집니다.</h1></div><a class="secondary" href="#test">다시 테스트하기 ↗</a></div><div class="result-grid"><section class="profile card"><span class="pill">규칙 기반 성향 분석</span><h2>${esc(data.types[p.investor_type])}</h2><p>${esc(p.summary)}</p><div class="scores">${scores}</div></section><section class="card"><div class="row"><span class="eyebrow">모델 포트폴리오</span><span class="pill">규칙 기반 추천</span></div><h2>세 종목, 하나의 균형</h2><p class="muted">가상 종목 데이터 기반 · 총 비중 100%</p><div class="allocation-bar" role="img" aria-label="${esc(rows.map(r=>`${r.ticker} ${r.allocation}%`).join(', '))}">${rows.map(r=>`<div style="width:${r.allocation}%">${r.allocation}%</div>`).join('')}</div><div class="legend">${rows.map((r,i)=>`<span><i class="color-${i+1}"></i>${esc(r.ticker)} <b>${r.allocation}%</b></span>`).join('')}</div><div class="amount-box"><label for="investment">투자 예정 금액</label><div class="amount-input"><input id="investment" type="number" min="0" max="1000000000000" step="1" value="1000000" inputmode="numeric"><span>원</span></div><p id="amount-error" class="error" role="alert"></p><div class="amounts">${rows.map(r=>`<div><span>${esc(r.ticker)}</span><strong data-allocation="${r.allocation}"></strong></div>`).join('')}</div><p class="small muted">비중에 따른 예산 예시이며 실제 주문 수량은 아닙니다.</p></div></section></div><div class="section-heading"><h2>나와 잘 맞는 세 종목</h2><span class="muted small">모든 수치와 애널리스트 의견은 가상 예시</span></div><section class="stock-grid">${cards}</section><section class="card explanation"><span class="eyebrow">포트폴리오 해설</span><h2>이 포트폴리오는 왜 이렇게 구성되었나요?</h2><p>${esc(pf.portfolio_summary)}</p><p class="small muted">변동성과 최대 낙폭 위험은 실제 백분율이 아닌 0~10의 가상 위험 지표입니다. 매칭 점수는 수익 확률이 아닙니다.</p></section>`;
  document.querySelector('#investment').addEventListener('input',calculate);calculate();
}
function calculate(){
  const input=document.querySelector('#investment'),cells=[...document.querySelectorAll('[data-allocation]')];
  try{if(input.value==='')throw Error('투자 예정 금액을 입력해주세요.');const values=logic.amounts(Number(input.value),result.portfolio.recommendations.map(r=>r.allocation));cells.forEach((c,i)=>c.textContent=values[i].toLocaleString('ko-KR')+'원');document.querySelector('#amount-error').textContent='';}
  catch(e){document.querySelector('#amount-error').textContent=e.message;cells.forEach(c=>c.textContent='—');}
}
route();
