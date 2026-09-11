import copy
import json
import os
import random
import tempfile
import unittest
from unittest.mock import patch, MagicMock
os.environ['OPENAI_API_KEY']=''
from app import create_app
from ai.investor_analysis import analyze_investor
from ai.portfolio_recommendation import fallback_portfolio, fallback_options, validate_options, recommend_portfolio
from ai.openai_client import structured_call
from logic.questionnaire import fallback_profile, validate_answers
from logic.schemas import Portfolio, InvestorProfile, Stock
from logic.stock_matcher import load_stocks, validate_selection

class PrototypeTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.app=create_app({'TESTING':True,'SECRET_KEY':'test-only','DATABASE':self.directory.name+'/test.db'})
        self.client=self.app.test_client()
        self.client.get('/')
        with self.client.session_transaction() as s:self.headers={'X-CSRF-Token':s['csrf']}
        self.stocks=load_stocks()
        self.profile=fallback_profile([1]*10)
        self.portfolio=fallback_portfolio(self.profile,self.stocks)
    def tearDown(self):self.directory.cleanup()
    def post(self,path,data=None):return self.client.post(path,json=data or {},headers=self.headers)
    def test_demo_journey(self):
        self.assertIn('데모 분석 모드',self.client.get('/').text)
        self.assertEqual(self.client.get('/questionnaire').status_code,200)
        self.assertEqual(self.post('/api/start',{'answers':[1]*10}).status_code,200)
        self.assertEqual(self.client.get('/analyzing').status_code,200)
        self.assertEqual(self.post('/api/portfolio').status_code,409)
        self.assertEqual(self.post('/api/profile').json['source'],'fallback')
        self.assertEqual(self.post('/api/portfolio').json['source'],'fallback')
        result=self.client.get('/result')
        self.assertEqual(result.status_code,200)
        self.assertIn('실제 투자 조언이 아닙니다',result.text)
        self.assertEqual(result.text.count('data-allocation='),3)
        self.assertEqual(self.app.test_client().get('/result').status_code,302)
    def test_invalid_input_and_csrf(self):
        for answers in [[],[1]*9,[True]*10,['1']*10,[3]*10,None]:
            self.assertEqual(self.post('/api/start',{'answers':answers}).status_code,400)
        self.assertEqual(self.client.post('/api/start',json={'answers':[1]*10}).status_code,403)
    def test_schema_rejections(self):
        base=self.portfolio.model_dump()
        variants=[]
        for field,value in [('allocation',51),('allocation',14),('allocation',33.5),('allocation',True),('match_score',101),('match_score',-1),('match_score',float('nan'))]:
            b=copy.deepcopy(base);b['recommendations'][0][field]=value;variants.append(b)
        b=copy.deepcopy(base);b['recommendations'].pop();variants.append(b)
        b=copy.deepcopy(base);b['recommendations'][0]['allocation']-=1;variants.append(b)
        b=copy.deepcopy(base);del b['recommendations'][0]['reason'];variants.append(b)
        b=copy.deepcopy(base);b['recommendations'][1]['ticker']=b['recommendations'][0]['ticker'];variants.append(b)
        for b in variants:
            with self.assertRaises(ValueError):Portfolio.model_validate(b)
        for value in [-1,11,float('nan'),True]:
            b=self.profile.model_dump();b['risk_tolerance']=value
            with self.assertRaises(ValueError):InvestorProfile.model_validate(b)
    def test_unknown_ticker_and_risk(self):
        b=self.portfolio.model_dump();b['recommendations'][0]['ticker']='FAKE'
        with self.assertRaises(ValueError):validate_selection(Portfolio.model_validate(b),self.profile,self.stocks)
        b['recommendations'][0]['ticker']='TSLA'
        with self.assertRaises(ValueError):validate_selection(Portfolio.model_validate(b),self.profile,self.stocks)
    def test_fallback_profiles_and_constraints(self):
        rng=random.Random(42)
        for answers in [[0]*10,[1]*10,[2]*10]+[[rng.randrange(3) for _ in range(10)] for _ in range(80)]:
            p=fallback_profile(answers)
            result=fallback_portfolio(p,self.stocks)
            validate_selection(result,p,self.stocks)
            self.assertEqual(sum(r.allocation for r in result.recommendations),100)
            self.assertTrue(all(15<=r.allocation<=50 for r in result.recommendations))
    def test_provider_failures_fall_back(self):
        with patch('ai.investor_analysis.api_enabled',return_value=True),patch('ai.investor_analysis.structured_call',side_effect=ValueError('bad')) as call:
            self.assertEqual(analyze_investor([1]*10)[1],'fallback');self.assertEqual(call.call_count,1)
        bad=self.portfolio.model_copy(deep=True);bad.recommendations[0].ticker='FAKE'
        with patch('ai.portfolio_recommendation.api_enabled',return_value=True),patch('ai.portfolio_recommendation.structured_call',return_value=bad) as call:
            self.assertEqual(recommend_portfolio(self.profile,self.stocks)[1],'fallback');self.assertEqual(call.call_count,1)
    def test_exactly_two_sdk_calls_and_payloads(self):
        responses=[MagicMock(status='completed',output_parsed=self.profile),MagicMock(status='completed',output_parsed=fallback_options(self.profile,self.stocks))]
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-fake'}),patch('ai.openai_client.OpenAI') as factory:
            sdk=factory.return_value;sdk.responses.parse.side_effect=responses
            self.post('/api/start',{'answers':[1]*10})
            self.assertEqual(self.post('/api/profile').status_code,200)
            self.assertEqual(self.post('/api/profile').status_code,200)
            self.assertEqual(self.post('/api/portfolio').status_code,200)
            self.assertEqual(self.post('/api/portfolio').status_code,200)
            self.assertEqual(sdk.responses.parse.call_count,2)
            calls=sdk.responses.parse.call_args_list
            payload=json.loads(calls[0].kwargs['input'][1]['content'])
            self.assertEqual(len(payload['questions_and_answers']),10)
            payload=json.loads(calls[1].kwargs['input'][1]['content'])
            self.assertEqual(len(payload['STOCK DATA']),20)
            self.assertFalse(calls[0].kwargs['store'])
            self.assertEqual(factory.call_args.kwargs['max_retries'],0)
    def test_refusal_incomplete(self):
        with patch('ai.openai_client.get_client') as client:
            client.return_value.responses.parse.return_value=MagicMock(status='incomplete',output_parsed=None)
            with self.assertRaises(ValueError):structured_call('test',{},InvestorProfile)
    def test_three_options(self):
        from logic.schemas import PortfolioOptions
        for answers in ([0]*10,[1]*10,[2]*10):
            profile=fallback_profile(answers)
            options=fallback_options(profile,self.stocks)
            self.assertEqual(len(options.portfolios),3)
            validate_options(options,profile,self.stocks)
        bad=options.model_dump();bad['portfolios'][1]=bad['portfolios'][0]
        with self.assertRaises(ValueError):PortfolioOptions.model_validate(bad)
        bad=options.model_dump();bad['portfolios'].pop()
        with self.assertRaises(ValueError):PortfolioOptions.model_validate(bad)
        self.post('/api/start',{'answers':[1]*10})
        self.post('/api/profile');self.post('/api/portfolio')
        for i in range(3):
            page=self.client.get('/result?plan='+str(i))
            self.assertEqual(page.status_code,200)
            self.assertIn('추천안 '+['A','B','C'][i]+' · 종목과 비중',page.text)

    def test_stock_data_validation(self):
        b=self.stocks[0].copy();b['low_price_target']=b['high_price_target']+1
        with self.assertRaises(ValueError):Stock.model_validate(b)

if __name__=='__main__':unittest.main()
