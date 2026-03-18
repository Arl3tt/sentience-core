from policies.neuro_policy import neuro_policy

def test_neuro_policy_focus():
    # low alpha, high beta -> protect_flow
    features = {'alpha_power': [0.1, 0.12],
        'beta_power': [0.5, 0.55],
        'theta_power': [0.1, 0.09],
        'gamma_power': [0.05, 0.06],
        'spectral_entropy': [4.0]}
    ctx = {'latest_features': features}
    decision = neuro_policy(ctx)
    assert decision['action'] in ('protect_flow', 'neutral')

def test_neuro_policy_drowsy():
    features = {'alpha_power': [0.1, 0.1],
        'beta_power': [0.1, 0.1],
        'theta_power': [1.0, 0.9],
        'gamma_power': [0.01, 0.02],
        'spectral_entropy': [5.0]}
    ctx = {'latest_features': features}
    decision = neuro_policy(ctx)
    assert decision['action'] in ('cue_anti_drowsy', 'neutral')
