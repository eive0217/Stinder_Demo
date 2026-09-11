const csrf = document.querySelector('meta[name="csrf-token"]').content;
async function post(url, data={}) {
  const response = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(data)});
  const result = await response.json();
  if(!response.ok) { const error=new Error(result.error || '요청을 처리하지 못했습니다.'); error.status=response.status; error.state=result.status; throw error; }
  return result;
}
const quiz=document.querySelector('#quiz');
if(quiz) {
  let current=0, sending=false;
  const fields=[...quiz.querySelectorAll('fieldset')], next=document.querySelector('#next'), previous=document.querySelector('#previous'), error=document.querySelector('#quiz-error');
  function render() { fields.forEach((f,i)=>f.hidden=i!==current); document.querySelector('#question-count').textContent=`질문 ${current+1} / 10`; document.querySelector('#quiz-progress').value=current+1; previous.disabled=current===0; next.textContent=current===9?'내 투자 성향 분석하기 →':'다음 질문 →'; error.textContent=''; }
  previous.onclick=()=>{if(!sending && current>0){current--;render();}};
  next.onclick=async()=>{
    if(sending)return;
    if(!fields[current].querySelector('input:checked')){error.textContent='답변 하나를 선택해주세요.';return;}
    if(current<9){current++;render();return;}
    sending=true; next.disabled=true; previous.disabled=true;
    try {const answers=fields.map(f=>Number(f.querySelector('input:checked').value)); const result=await post('/api/start',{answers}); location.assign(result.url);}
    catch(e){error.textContent=e.message; sending=false;next.disabled=false;previous.disabled=false;}
  };
  quiz.onsubmit=e=>{e.preventDefault();next.click();};
}
const wait=ms=>new Promise(resolve=>setTimeout(resolve,ms));
if(document.querySelector('#analysis')) {
  (async()=>{
    async function stage(name){
      const deadline=Date.now()+110000;
      while(true){try{return await post('/api/'+name);}catch(e){if(e.status!==409 || !String(e.state).endsWith('_running') || Date.now()>deadline)throw e;await wait(1000);}}
    }
    const title=document.querySelector('#analysis-title'), bar=document.querySelector('#analysis-progress');
    try {
      await stage('profile');
      document.querySelector('#stage-profile').textContent='✓ 투자 성향 분석 완료';
      document.querySelector('#stage-profile').className='done';
      title.textContent='투자 성향 분석 완료';bar.value=50;
      await wait(400);
      title.textContent='주식 데이터를 비교하고 있습니다...';
      document.querySelector('#stage-portfolio').className='active';
      document.querySelector('#stage-portfolio').textContent='주식 데이터 비교 및 포트폴리오 구성 중';
      await stage('portfolio');
      title.textContent='맞춤 포트폴리오 생성 완료';
      document.querySelector('#stage-portfolio').textContent='✓ 맞춤 포트폴리오 생성 완료';
      document.querySelector('#stage-portfolio').className='done';bar.value=100;
      await wait(650); location.replace('/result');
    }catch(e){title.textContent='분석을 잠시 멈췄습니다';document.querySelector('#analysis-error').textContent=e.message;document.querySelector('.spinner').style.animation='none';}
  })();
}
const investment=document.querySelector('#investment');
if(investment){
  function calculate(){
    const total=Number(investment.value), cells=[...document.querySelectorAll('[data-allocation]')];
    if(investment.value==='' || !Number.isSafeInteger(total) || total<0 || total>1e12){document.querySelector('#amount-error').textContent='0~1조 원 사이의 정수를 입력해주세요.';cells.forEach(c=>c.textContent='—');return;}
    document.querySelector('#amount-error').textContent='';
    const raw=cells.map(c=>total*Number(c.dataset.allocation)/100), amounts=raw.map(Math.floor);
    let remainder=total-amounts.reduce((a,b)=>a+b,0);
    const order=raw.map((v,i)=>i).sort((a,b)=>(raw[b]-amounts[b])-(raw[a]-amounts[a]));
    for(let i=0;i<remainder;i++) amounts[order[i]]++;
    cells.forEach((c,i)=>c.textContent=amounts[i].toLocaleString('ko-KR')+'원');
  }
  investment.addEventListener('input',calculate);calculate();
}
