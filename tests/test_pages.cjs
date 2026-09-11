const assert=require('node:assert/strict');
require('../static/js/pages-data.js');require('../static/js/pages-logic.js');
const data=globalThis.DEMO_DATA,logic=globalThis.DemoLogic;
for(let i=0;i<243;i++){
 let n=i;const answers=Array.from({length:10},()=>{const a=n%3;n=Math.floor(n/3);return a;});
 const p=logic.profile(answers,data),result=logic.portfolio(p,data.stocks);
 assert.equal(result.recommendations.length,3);assert.equal(result.recommendations.reduce((s,r)=>s+r.allocation,0),100);
 logic.validate(result,p,data.stocks);
 for(const total of [0,1,2,99,1000000,1000000000000])assert.equal(logic.amounts(total,result.recommendations.map(r=>r.allocation)).reduce((a,b)=>a+b,0),total);
}
for(const a of [[],Array(10).fill(true),Array(10).fill(3)])assert.throws(()=>logic.profile(a,data));
for(const a of [-1,1.5,Infinity,NaN,1000000000001])assert.throws(()=>logic.amounts(a,[40,35,25]));
const p=logic.profile(Array(10).fill(1),data),result=logic.portfolio(p,data.stocks);result.recommendations[0].ticker='FAKE';assert.throws(()=>logic.validate(result,p,data.stocks));
const fs=require('node:fs'),path=require('node:path'),html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
assert(!html.includes('{{'));assert(!html.includes('/api/'));assert(!html.includes('href="/'));
for(const match of html.matchAll(/(?:src|href)="(\.\/[^\"]+)"/g))assert(fs.existsSync(path.resolve(__dirname,'..',match[1])));
console.log('PASS: 243 portfolios, integer amount totals, invalid inputs, and static asset paths');
