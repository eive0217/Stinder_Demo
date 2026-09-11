from logic.schemas import InvestorProfile
TYPE_NAMES = {'steady_planner':'안정형 설계자','balanced_builder':'균형형 투자자','growth_seeker':'성장 추구형','bold_explorer':'적극적 탐험가'}
SCORE_NAMES = {'risk_tolerance':'위험 감수 성향','growth_preference':'성장 선호도','time_horizon':'장기 투자 성향','loss_sensitivity':'손실 민감도'}
QUESTIONS = [{'id': 1, 'text': '친구와 여행을 간다면 어떤 쪽이 더 끌리나요?', 'options': ['일정과 숙소가 모두 확정된 편안한 여행', '계획은 있지만 즉흥적인 선택도 가능한 여행', '변수는 많지만 특별한 경험을 할 수 있는 여행'], 'weights': [1, 0.5, 0, 0.5]}, {'id': 2, 'text': '두 가지 이상의 보상 중 하나를 고를 수 있다면?', 'options': ['무조건 5만 원', '50% 확률로 12만 원', '20% 확률로 30만 원'], 'weights': [1, 0.5, 0, 1]}, {'id': 3, 'text': '사고 싶은 10만 원짜리 물건이 6개월 뒤 7만 원이 된다면?', 'options': ['지금 산다', '조금 고민한다', '6개월 기다린다'], 'weights': [0, 0, 1, 0]}, {'id': 4, 'text': '게임에서 아이템 강화에 실패하면 아이템이 사라질 수도 있다면?', 'options': ['안전한 단계에서 멈춘다', '성공 확률을 보고 몇 번 더 시도한다', '성공하면 강해지므로 계속 도전한다'], 'weights': [1, 0.5, 0, 1]}, {'id': 5, 'text': '새로운 프로젝트를 고를 때 어떤 쪽이 더 끌리나요?', 'options': ['결과가 예측 가능하고 안정적인 프로젝트', '안정성과 가능성이 적당히 섞인 프로젝트', '실패할 수 있지만 성공하면 크게 주목받는 프로젝트'], 'weights': [0.5, 1, 0.5, 0.5]}, {'id': 6, 'text': '100만 원을 받았는데 당장 쓸 필요는 없다면?', 'options': ['언제든 사용할 수 있는 곳에 둔다', '일부는 보관하고 일부는 장기적으로 묶는다', '오래 기다려도 더 큰 보상을 기대하는 곳에 둔다'], 'weights': [0.5, 0.5, 1, 0]}, {'id': 7, 'text': '내가 선택한 것이 20% 정도 손해를 봤다면?', 'options': ['더 큰 손실이 걱정되어 바로 정리한다', '상황을 다시 확인한 후 결정한다', '장기적인 가능성이 있다면 계속 기다린다'], 'weights': [0.5, 0, 1, 1]}, {'id': 8, 'text': '새로운 기술 제품이 출시되었을 때 나는?', 'options': ['충분히 검증된 후 구매한다', '후기와 평가를 본 뒤 구매한다', '새로운 기술이면 초기부터 사용한다'], 'weights': [0.5, 1, 0, 0.5]}, {'id': 9, 'text': '직업을 고른다면 어떤 쪽이 더 끌리나요?', 'options': ['연봉은 일정하지만 매우 안정적인 직업', '안정성과 성과 보상이 적당히 섞인 직업', '수입 변동은 크지만 성공하면 많이 벌 수 있는 직업'], 'weights': [1, 1, 0.5, 0.5]}, {'id': 10, 'text': '계획대로 일이 진행되지 않을 때 나는?', 'options': ['최대한 원래 계획으로 돌아가려고 한다', '상황을 보고 유연하게 수정한다', '예상 밖의 변화도 새로운 기회라고 생각한다'], 'weights': [0.5, 0.5, 0, 1]}]

def validate_answers(answers):
    if not isinstance(answers, list) or len(answers) != 10:
        raise ValueError('10개 질문에 모두 답해주세요.')
    if any(type(a) is not int or a not in (0,1,2) for a in answers):
        raise ValueError('올바른 선택지를 골라주세요.')
    return answers

def answered_questions(answers):
    return [{'question':q['text'], 'options':q['options'], 'answer':q['options'][a]} for q,a in zip(QUESTIONS, validate_answers(answers))]

def fallback_profile(answers):
    validate_answers(answers)
    scores = {}
    for i,key in enumerate(SCORE_NAMES):
        numerator = sum((2-a if i == 3 else a)*q['weights'][i] for q,a in zip(QUESTIONS,answers))
        scores[key] = round(numerator / (2*sum(q['weights'][i] for q in QUESTIONS))*10,1)
    r,g,l = scores['risk_tolerance'], scores['growth_preference'], scores['loss_sensitivity']
    kind = 'steady_planner' if r < 3.5 or l > 7 else 'bold_explorer' if r >= 8 and g >= 7 else 'growth_seeker' if g >= 6 and r >= 5 else 'balanced_builder'
    summary = {'steady_planner':'예측 가능한 선택과 손실을 줄이는 방향을 선호하는 답변이 나타났습니다. 안정성을 중심으로 종목을 비교합니다.', 'balanced_builder':'성장 가능성과 안정성을 함께 살피는 답변이 나타났습니다. 서로 다른 위험 특성을 조합합니다.', 'growth_seeker':'새로운 가능성과 성장을 중요하게 보는 답변이 나타났습니다. 변동성과 손실 위험도 함께 고려합니다.', 'bold_explorer':'불확실성을 감수하며 새로운 기회를 선택하는 답변이 나타났습니다. 적극적인 성향에도 종목별 비중 제한을 적용합니다.'}[kind]
    return InvestorProfile(**scores,investor_type=kind,summary=summary)
