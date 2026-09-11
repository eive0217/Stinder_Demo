from ai.openai_client import structured_call, api_enabled, RECOVERABLE, report_fallback
from logic.schemas import InvestorProfile
from logic.questionnaire import answered_questions, fallback_profile
SYSTEM_PROMPT = """당신은 교육용 투자 성향 설문 해석기입니다. 모든 질문, 선택지 및 답변에만 근거하여 네 점수를 0~10으로 분석하고 지정된 네 타입 중 하나를 선택하세요. 위험 감수, 성장 선호, 장기 투자, 손실 민감도를 독립적으로 해석하세요. 질문에 포함되지 않은 재정 상태, 소득, 자산, 나이, 직업, 성별, 부채, 가족 상황을 절대 추측하지 마세요. 가상 상황의 선택을 사용자의 실제 상황으로 간주하지 마세요. summary는 한국어 2~3문장으로 작성하고 진단, 수익 보장, 실제 투자 조언을 하지 마세요."""

def analyze_investor(answers):
    payload = answered_questions(answers)
    if api_enabled():
        try:
            return structured_call(SYSTEM_PROMPT,{'questions_and_answers':payload},InvestorProfile),'ai'
        except RECOVERABLE as exc:
            report_fallback('investor',exc)
    return fallback_profile(answers),'fallback'
