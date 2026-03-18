from core.tools.asd_attention_analysis import ASDAttentionAnalyzer, create_asd_analyzer

def test_analyzer_init():
    analyzer = ASDAttentionAnalyzer(fs=250.0)
    assert analyzer.fs == 250.0
    assert analyzer.baseline_metrics is None
    assert analyzer.reference_data is not None
    assert "typical_alpha_beta_ratio" in analyzer.reference_data

def test_band_power_extraction(sample_signal):
    analyzer = ASDAttentionAnalyzer()
    powers = analyzer._extract_band_powers(sample_signal)
    assert isinstance(powers, dict)
    # should have at least theta, alpha, beta bands
    assert any(k in powers for k in ["theta", "alpha", "beta"])

def test_attention_stability(sample_signal):
    analyzer = ASDAttentionAnalyzer()
    stability = analyzer._analyze_attention_stability(sample_signal)
    assert isinstance(stability, float)
    assert 0 <= stability <= 1

def test_detect_repetitive_patterns(sample_signal):
    analyzer = ASDAttentionAnalyzer()
    rep_score = analyzer._detect_repetitive_patterns(sample_signal)
    assert isinstance(rep_score, float)
    assert 0 <= rep_score <= 1

def test_attention_profile(sample_signal):
    analyzer = ASDAttentionAnalyzer()
    profile = analyzer.analyze_attention_profile(sample_signal, duration_seconds=1.0, context="neutral")
    assert isinstance(profile, dict)
    # profile contains asd_likelihood, context, alpha_beta_ratio, etc.
    assert any(k in profile for k in ["asd_likelihood", "alpha_beta_ratio", "context"])

def test_multichannel_profile(sample_multichannel):
    analyzer = ASDAttentionAnalyzer()
    profile = analyzer.analyze_attention_profile(sample_multichannel)
    assert isinstance(profile, dict)

def test_factory_function():
    asd = create_asd_analyzer()
    assert asd is not None
    assert hasattr(asd, "analyze_attention_profile")
