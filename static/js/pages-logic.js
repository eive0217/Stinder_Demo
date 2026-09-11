/* Browser-only equivalent of the Python demo rules. No network or API calls. */
(function(root){
  const effectiveRisk=s=>.5*s.risk_score+.3*s.volatility+.2*s.max_drawdown;
  const riskLimit=p=>Math.min(9,Math.max(3.5,3.5+.5*p.risk_tolerance-.15*p.loss_sensitivity));
  const round=x=>Math.round((x+Number.EPSILON)*10)/10;
  function profile(answers,data){
    if(!Array.isArray(answers)||answers.length!==10||answers.some(a=>!Number.isInteger(a)||a<0||a>2))throw Error('10개 질문에 모두 답해주세요.');
    const p={};
    Object.keys(data.scores).forEach((key,i)=>{
      const n=data.questions.reduce((sum,q,j)=>sum+(i===3?2-answers[j]:answers[j])*q.weights[i],0);
      p[key]=round(n/(2*data.questions.reduce((sum,q)=>sum+q.weights[i],0))*10);
    });
    const r=p.risk_tolerance,g=p.growth_preference,l=p.loss_sensitivity;
    p.investor_type=r<3.5||l>7?'steady_planner':r>=8&&g>=7?'bold_explorer':g>=6&&r>=5?'growth_seeker':'balanced_builder';
    p.summary={steady_planner:'예측 가능한 선택과 손실을 줄이는 방향을 선호하는 답변이 나타났습니다. 안정성을 중심으로 종목을 비교합니다.',balanced_builder:'성장 가능성과 안정성을 함께 살피는 답변이 나타났습니다. 서로 다른 위험 특성을 조합합니다.',growth_seeker:'새로운 가능성과 성장을 중요하게 보는 답변이 나타났습니다. 변동성과 손실 위험도 함께 고려합니다.',bold_explorer:'불확실성을 감수하며 새로운 기회를 선택하는 답변이 나타났습니다. 적극적인 성향에도 종목별 비중 제한을 적용합니다.'}[p.investor_type];
    return p;
  }
  function match(p,s){return round(Math.min(100,Math.max(0,10*(.35*(10-Math.abs(p.risk_tolerance-effectiveRisk(s)))+.30*(10-Math.abs(p.growth_preference-s.growth_score))+.20*(10-Math.abs(p.loss_sensitivity-s.stability_score))+.10*(10-Math.abs(p.time_horizon-(s.growth_score*.6+s.stability_score*.4)))+.05*s.analyst_confidence))));}
  function allowed(p,group){return group.every(s=>effectiveRisk(s)<=riskLimit(p))&&group.filter(s=>effectiveRisk(s)>=7).length<=1&&new Set(group.map(s=>s.sector)).size>=2;}
  function portfolio(p,stocks){
    let selected=null,best=-Infinity;
    for(let a=0;a<stocks.length-2;a++)for(let b=a+1;b<stocks.length-1;b++)for(let c=b+1;c<stocks.length;c++){
      const group=[stocks[a],stocks[b],stocks[c]];if(!allowed(p,group))continue;
      const risks=group.map(effectiveRisk),score=group.reduce((sum,s)=>sum+match(p,s),0)+2*new Set(group.map(s=>s.sector)).size+Math.max(...risks)-Math.min(...risks);
      if(score>best){best=score;selected=group;}
    }
    if(!selected)throw Error('위험도 제한을 만족하는 종목 조합이 없습니다.');
    const strength=selected.map(s=>Math.max(1,match(p,s))/(1+effectiveRisk(s)*(10-p.risk_tolerance+p.loss_sensitivity)/100)),weights=[15,15,15];
    for(let n=0;n<55;n++){let index=-1;for(let i=0;i<3;i++)if(weights[i]<50&&(index<0||strength[i]/(weights[i]+1)>strength[index]/(weights[index]+1)))index=i;weights[index]++;}
    const result={portfolio_summary:'설문 성향과 종목의 위험·성장·안정성을 비교해 세 종목을 조합했습니다. 변동성과 최대 낙폭 위험을 반영하고, 최소 두 업종에 나누어 비중을 배정했습니다. 가상 데이터에 기반한 교육용 예시입니다.',recommendations:selected.map((s,i)=>({ticker:s.ticker,allocation:weights[i],match_score:match(p,s),reason:`성장 선호도 ${p.growth_preference}점과 종목 성장 점수 ${s.growth_score}점, 손실 민감도 ${p.loss_sensitivity}점을 함께 비교했습니다. 변동성 ${s.volatility}점과 최대 낙폭 위험 ${s.max_drawdown}점을 반영해 비중을 ${weights[i]}%로 정했습니다.`}))};
    validate(result,p,stocks);return result;
  }
  function validate(result,p,stocks){
    const r=result.recommendations,catalog=new Map(stocks.map(s=>[s.ticker,s]));
    if(!Array.isArray(r)||r.length!==3||new Set(r.map(x=>x.ticker)).size!==3||r.some(x=>!catalog.has(x.ticker)||!Number.isInteger(x.allocation)||x.allocation<15||x.allocation>50||!Number.isFinite(x.match_score)||x.match_score<0||x.match_score>100||typeof x.reason!=='string'||!x.reason.trim())||r.reduce((sum,x)=>sum+x.allocation,0)!==100||!allowed(p,r.map(x=>catalog.get(x.ticker))))throw Error('포트폴리오 검증에 실패했습니다.');
    return result;
  }
  function amounts(total,weights){
    if(!Number.isSafeInteger(total)||total<0||total>1e12)throw Error('0~1조 원 사이의 정수를 입력해주세요.');
    const raw=weights.map(w=>total*w/100),rounded=raw.map(Math.floor),order=raw.map((_,i)=>i).sort((a,b)=>(raw[b]-rounded[b])-(raw[a]-rounded[a]));
    const remaining=total-rounded.reduce((a,b)=>a+b,0);for(let i=0;i<remaining;i++)rounded[order[i]]++;return rounded;
  }
  root.DemoLogic={profile,portfolio,validate,amounts};
})(globalThis);
