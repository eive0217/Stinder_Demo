import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import ValidationError
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
logger = logging.getLogger(__name__)
DEMO_NOTICE = 'OpenAI API 키가 설정되지 않아 데모 분석 모드로 실행합니다.'

def api_enabled():
    return bool(os.getenv('OPENAI_API_KEY','').strip())

def get_client():
    if not api_enabled():
        return None
    return OpenAI(api_key=os.environ['OPENAI_API_KEY'].strip(),timeout=45.0,max_retries=0)

def structured_call(system, payload, schema):
    client = get_client()
    if client is None:
        raise ValueError('API key unavailable')
    with client:
        response = client.responses.parse(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),
            input=[{'role':'system','content':system},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}],
            text_format=schema, max_output_tokens=7000, store=False)
    if response.status != 'completed' or response.output_parsed is None:
        raise ValueError('응답 거부 또는 불완전한 JSON')
    return schema.model_validate(response.output_parsed.model_dump())

RECOVERABLE = (OpenAIError, ValidationError, ValueError)

def report_fallback(stage, exc):
    # Never log prompts, answers, credentials, or provider exception text.
    logger.warning('%s fallback: %s',stage,type(exc).__name__)
