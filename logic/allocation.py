from logic.stock_matcher import effective_risk, match_score

def allocate(profile, stocks):
    strength = [max(1,match_score(profile,s))/(1+effective_risk(s)*(10-profile.risk_tolerance+profile.loss_sensitivity)/100) for s in stocks]
    # Start at the minimum; allocate remaining integer points with a hard ceiling.
    weights = [15,15,15]
    for _ in range(55):
        index = max((i for i in range(3) if weights[i]<50),key=lambda i:strength[i]/(weights[i]+1))
        weights[index] += 1
    return weights
