# Quick Reference: BCI Tools API

## 1. Brain Wave Classifier
**File**: `core/tools/brain_wave_classifier.py`

```python
from core.tools import classify_brainwave_bands, classify_cognitive_state

# Classify frequency bands
bands = classify_brainwave_bands(eeg_signal, fs=250)
# Returns: {delta_power, theta_power, alpha_power, beta_power, gamma_power, percentages}

# Classify cognitive state
state = classify_cognitive_state(eeg_signal, fs=250)
# Returns: {predicted_state, state_scores, band_powers, ratios}
```

## 2. Motor Imagery CNN
**File**: `core/tools/motor_imagery_cnn.py`

```python
from core.tools import classify_motor_imagery, extract_motor_imagery_features

# Classify motor imagery
result = classify_motor_imagery(eeg_signal, fs=250)
# Returns: {predicted_imagery, class_probabilities, confidence, features}
# Imagery types: left_hand, right_hand, feet, tongue

# Extract features
features = extract_motor_imagery_features(eeg_signal, fs=250)
# Returns: {ch0_mu_power, ch0_beta_power, ...}
```

## 3. P300 Speller
**File**: `core/tools/p300_speller.py`

```python
from core.tools import create_speller_interface, classify_p300_response

# Create speller (6x6 character matrix by default)
speller = create_speller_interface(rows=6, cols=6)

# Run speller sequence
result = speller.speller_sequence(eeg_trials, trial_stimuli, fs=250)
# Returns: {selected_character, row, column, accuracy_estimate}

# Classify single P300 response
p300 = classify_p300_response(eeg_signal, fs=250)
# Returns: {contains_p300, confidence, snr, amplitude, latency_ms}
```

## 4. Neurofeedback Loop
**File**: `core/tools/neurofeedback_loop.py`

```python
from core.tools import create_neurofeedback_session

# Create session
nf = create_neurofeedback_session(
    target="relaxation",  # or "focus", "arousal", "calmness"
    modality="visual",    # or "auditory", "proprioceptive", "combined"
    fs=250
)

# Process EEG chunk
feedback = nf.process_eeg_chunk(eeg_chunk)
# Returns: {score, metrics, feedback, session_stats}

# Add callback for real-time feedback
nf.add_feedback_callback(my_callback_function)

# Get session report
report = nf.get_session_report()
# Returns: comprehensive session statistics
```

## 5. Hybrid BCI
**File**: `core/tools/hybrid_bci.py`

```python
from core.tools import create_hybrid_bci

# Create hybrid BCI
bci = create_hybrid_bci(
    paradigms=["motor_imagery", "p300", "ssvep"],
    fusion="weighted"  # or "voting", "averaged"
)

# Process through all paradigms
result = bci.process_multi_paradigm(eeg_signal, fs=250)
# Returns: {command, confidence, paradigm, details}

# Update paradigm performance (for adaptive fusion)
bci.update_paradigm_performance(BCIParadigm.MOTOR_IMAGERY, accuracy=0.85)

# Get performance report
report = bci.get_performance_report()
```

## 6. ASD Attention Analysis
**File**: `core/tools/asd_attention_analysis.py`

```python
from core.tools import create_asd_analyzer, analyze_asd_attention

# Create analyzer
analyzer = create_asd_analyzer(fs=250)

# Analyze attention profile
result = analyzer.analyze_attention_profile(
    eeg_signal,
    duration_seconds=10.0,
    context="neutral"  # or "social", "repetitive"
)
# Returns: {profile, metrics, asd_likelihood, recommendations}

# Get longitudinal analysis (across multiple recordings)
trend = analyzer.get_longitudinal_analysis()

# Quick analysis
quick = analyze_asd_attention(eeg_signal, context="social")
```

## Data Flow Example

```python
# 1. Preprocess EEG
from models import preprocess_eeg
preprocessed = preprocess_eeg(raw_eeg, fs=250)

# 2. Classify brain state
from core.tools import classify_cognitive_state
state = classify_cognitive_state(preprocessed, fs=250)

# 3. If focused, try motor imagery
if state["predicted_state"] == "focused":
    from core.tools import classify_motor_imagery
    mi = classify_motor_imagery(preprocessed, fs=250)
    
    # Use result in hybrid BCI
    from core.tools import create_hybrid_bci
    bci = create_hybrid_bci(["motor_imagery", "p300"])
    command = bci.process_multi_paradigm(preprocessed, fs=250)

# 4. Provide neurofeedback
from core.tools import create_neurofeedback_session
nf = create_neurofeedback_session(target="focus", modality="visual")
feedback = nf.process_eeg_chunk(preprocessed)
```

## Parameters Reference

### Common Parameters
- `eeg_signal`: np.ndarray - EEG time series (samples,) or (samples, channels)
- `fs`: float - Sampling frequency in Hz (typically 250)
- `duration_seconds`: float - Duration of analysis

### Frequency Bands
- **Delta**: 0.5-4 Hz
- **Theta**: 4-8 Hz
- **Alpha**: 8-12 Hz
- **Beta**: 12-30 Hz
- **Gamma**: 30-80+ Hz

### Cognitive States
- **alert**: High alertness
- **focused**: High concentration
- **relaxed**: Relaxed state
- **drowsy**: Low vigilance
- **stressed**: High stress

### Motor Imagery Classes
- **left_hand**: Left hand motor imagery
- **right_hand**: Right hand motor imagery
- **feet**: Feet motor imagery
- **tongue**: Tongue motor imagery

### Neurofeedback Targets
- **relaxation**: Increase alpha/theta, decrease beta
- **focus**: Increase beta, decrease theta
- **arousal**: Increase overall activity
- **calmness**: Increase alpha/theta ratio

### BCI Paradigms
- **motor_imagery**: Motor cortex activation
- **p300**: Event-related potentials
- **ssvep**: Steady-state visual evoked potentials
- **hybrid**: Multi-paradigm fusion

## Performance Tips

1. **Buffer Size**: Larger buffers (1-2s) for better frequency resolution
2. **Multi-channel**: Combine channels for robust classification
3. **Real-time**: Use callbacks for responsive feedback
4. **Adaptive**: Update paradigm weights based on performance
5. **Fallbacks**: All tools have heuristic fallbacks if ML unavailable

## Troubleshooting

**ImportError for PyTorch**: Motor Imagery CNN has fallback heuristic
**No P300 detected**: Check SNR threshold in detector
**Low confidence scores**: Increase buffer size or use multi-channel averaging
**Slow processing**: Reduce FFT resolution or use shorter windows
