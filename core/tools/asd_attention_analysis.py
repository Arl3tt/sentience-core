"""
ASD Attention Analysis Tool

Analyzes EEG patterns related to Autism Spectrum Disorder attention characteristics.
Includes attention anomaly detection, social attention processing, and executive function metrics.
"""

import numpy as np
from typing import Dict, Any, List
from collections import deque
from dataclasses import dataclass


@dataclass
class AttentionProfile:
    """ASD-relevant attention profile"""
    attention_span: float  # Duration of sustained attention (seconds)
    attention_variability: float  # Consistency of attention (lower is more consistent)
    social_attention_score: float  # Response to social stimuli (0-1)
    repetitive_pattern_score: float  # Presence of repetitive patterns (0-1)
    executive_function_score: float  # Executive function capability (0-1)
    stimulus_sensitivity: float  # Sensitivity to sensory stimuli (0-1)


class ASDAttentionAnalyzer:
    """Analyzer for ASD-related attention patterns in EEG"""

    def __init__(self, fs: float = 250.0):
        """
        Initialize ASD attention analyzer.

        Args:
            fs: Sampling frequency in Hz
        """
        self.fs = fs
        self.analysis_history = deque(maxlen=100)
        self.baseline_metrics = None
        self.reference_data = self._initialize_reference_data()

    @staticmethod
    def _initialize_reference_data() -> Dict[str, Any]:
        """Initialize normative reference data for comparison"""
        return {
            "typical_alpha_beta_ratio": 1.2,
            "typical_theta_beta_ratio": 0.8,
            "typical_attention_stability": 0.7,
            "asd_alpha_beta_ratio_range": (0.4, 0.8),
            "asd_theta_beta_ratio_range": (1.2, 2.0),
            "repetition_detection_threshold": 0.6
        }

    def analyze_attention_profile(
        self,
        eeg_signal: np.ndarray,
        duration_seconds: float = 1.0,
        context: str = "neutral"
    ) -> Dict[str, Any]:
        """
        Analyze overall attention profile for ASD indicators.

        Args:
            eeg_signal: EEG time series data
            duration_seconds: Duration of recording in seconds
            context: Context of recording ("neutral", "social", "repetitive")

        Returns:
            Detailed attention profile analysis
        """
        if eeg_signal.ndim == 2:
            eeg_signal = np.mean(eeg_signal, axis=1)

        # Extract metrics
        band_powers = self._extract_band_powers(eeg_signal)
        stability = self._analyze_attention_stability(eeg_signal)
        repetition_score = self._detect_repetitive_patterns(eeg_signal)
        stimulus_sensitivity = self._analyze_stimulus_sensitivity(eeg_signal)

        # Compute ASD likelihood indicators
        alpha_beta_ratio = band_powers.get("alpha", 1) / (band_powers.get("beta", 1) + 1e-6)
        theta_beta_ratio = band_powers.get("theta", 1) / (band_powers.get("beta", 1) + 1e-6)

        # Social attention (based on mu rhythm suppression - typical in social context)
        social_attention = self._analyze_social_attention(eeg_signal, context)

        # Executive function (based on frontal activity)
        executive_function = self._analyze_executive_function(eeg_signal)

        # Create profile
        profile = AttentionProfile(
            attention_span=duration_seconds * stability,
            attention_variability=1.0 - stability,
            social_attention_score=social_attention,
            repetitive_pattern_score=repetition_score,
            executive_function_score=executive_function,
            stimulus_sensitivity=stimulus_sensitivity
        )

        # Compute ASD likelihood
        asd_likelihood = self._compute_asd_likelihood(
            alpha_beta_ratio,
            theta_beta_ratio,
            repetition_score,
            social_attention,
            executive_function
        )

        result = {
            "profile": {
                "attention_span": profile.attention_span,
                "attention_variability": profile.attention_variability,
                "social_attention_score": profile.social_attention_score,
                "repetitive_pattern_score": profile.repetitive_pattern_score,
                "executive_function_score": profile.executive_function_score,
                "stimulus_sensitivity": profile.stimulus_sensitivity
            },
            "metrics": {
                "alpha_beta_ratio": float(alpha_beta_ratio),
                "theta_beta_ratio": float(theta_beta_ratio),
                "attention_stability": stability,
                "band_powers": band_powers
            },
            "asd_likelihood": {
                "score": asd_likelihood,
                "interpretation": self._interpret_asd_score(asd_likelihood)
            },
            "context": context,
            "recommendations": self._generate_recommendations(profile, asd_likelihood)
        }

        self.analysis_history.append(result)
        return result

    def _extract_band_powers(self, eeg_signal: np.ndarray) -> Dict[str, float]:
        """Extract frequency band powers"""
        from scipy.signal import welch

        frequencies, psd = welch(eeg_signal, fs=self.fs, nperseg=min(512, len(eeg_signal)))

        bands = {
            "delta": (0.5, 4),
            "theta": (4, 8),
            "alpha": (8, 12),
            "beta": (12, 30),
            "gamma": (30, 80)
        }

        band_powers = {}
        for band_name, (low, high) in bands.items():
            mask = (frequencies >= low) & (frequencies < high)
            power = np.mean(psd[mask])
            band_powers[band_name] = float(power)

        return band_powers

    def _analyze_attention_stability(self, eeg_signal: np.ndarray) -> float:
        """
        Analyze consistency/stability of attention.
        Compute from coefficient of variation of frequency bands over time.
        """
        from scipy.signal import welch

        # Split signal into windows
        window_size = int(self.fs * 1.0)  # 1-second windows
        if len(eeg_signal) < window_size:
            return 0.5

        alpha_powers = []
        beta_powers = []

        for i in range(0, len(eeg_signal) - window_size, window_size // 2):
            window = eeg_signal[i:i+window_size]
            frequencies, psd = welch(window, fs=self.fs)

            alpha_mask = (frequencies >= 8) & (frequencies < 12)
            beta_mask = (frequencies >= 12) & (frequencies < 30)

            alpha_powers.append(np.mean(psd[alpha_mask]))
            beta_powers.append(np.mean(psd[beta_mask]))

        # Compute coefficient of variation
        alpha_cv = np.std(alpha_powers) / (np.mean(alpha_powers) + 1e-6)
        beta_cv = np.std(beta_powers) / (np.mean(beta_powers) + 1e-6)

        # Lower CV indicates more stable attention
        stability = 1.0 / (1.0 + (alpha_cv + beta_cv) / 2)
        return float(np.clip(stability, 0, 1))

    def _detect_repetitive_patterns(self, eeg_signal: np.ndarray) -> float:
        """Detect repetitive or stereotyped patterns in EEG"""
        # Check for self-similarity (characteristic of repetitive patterns)
        if len(eeg_signal) < 1000:
            return 0.0

        # Divide signal into halves and compute correlation
        mid = len(eeg_signal) // 2
        signal1 = eeg_signal[:mid]
        signal2 = eeg_signal[mid:]

        # Normalize signals
        signal1 = (signal1 - np.mean(signal1)) / (np.std(signal1) + 1e-6)
        signal2 = (signal2 - np.mean(signal2)) / (np.std(signal2) + 1e-6)

        # Cross-correlation
        correlation = np.corrcoef(signal1[:min(len(signal1), len(signal2))],
                                  signal2[:min(len(signal1), len(signal2))])[0, 1]

        # Higher correlation indicates more repetitive patterns
        repetition_score = max(0, correlation)
        return float(repetition_score)

    def _analyze_stimulus_sensitivity(self, eeg_signal: np.ndarray) -> float:
        """Analyze sensitivity to sensory stimuli"""
        from scipy.signal import welch

        # Higher gamma power typically indicates increased sensory processing
        frequencies, psd = welch(eeg_signal, fs=self.fs)

        gamma_mask = (frequencies >= 30) & (frequencies < 80)
        gamma_power = np.mean(psd[gamma_mask])

        # Normalize and clip
        sensitivity = min(1.0, gamma_power / 10.0)
        return float(sensitivity)

    def _analyze_social_attention(self, eeg_signal: np.ndarray, context: str) -> float:
        """
        Analyze social attention through mu rhythm suppression.
        Mu rhythm (8-12 Hz) typically suppresses during social interaction in typical individuals.
        Reduced suppression in ASD.
        """
        from scipy.signal import welch

        frequencies, psd = welch(eeg_signal, fs=self.fs)

        mu_mask = (frequencies >= 8) & (frequencies < 12)
        mu_power = np.mean(psd[mu_mask])

        # Baseline expectation
        baseline_mu = 1.0

        # Compute suppression ratio
        suppression = 1.0 - (mu_power / (baseline_mu + 1e-6))

        if context == "social":
            # In social context, typical individuals show ~40-60% suppression
            # ASD individuals show less suppression
            social_attention = max(0, suppression)
        else:
            # In non-social context, use baseline
            social_attention = 0.5

        return float(np.clip(social_attention, 0, 1))

    def _analyze_executive_function(self, eeg_signal: np.ndarray) -> float:
        """
        Analyze executive function based on frontal theta-beta ratio.
        Higher theta-beta ratio in frontal areas associated with lower executive function.
        """
        from scipy.signal import welch

        frequencies, psd = welch(eeg_signal, fs=self.fs)

        theta_mask = (frequencies >= 4) & (frequencies < 8)
        beta_mask = (frequencies >= 12) & (frequencies < 30)

        theta_power = np.mean(psd[theta_mask])
        beta_power = np.mean(psd[beta_mask])

        theta_beta_ratio = theta_power / (beta_power + 1e-6)

        # Normalize: typical ~0.8, ASD-associated ~1.5+
        # Lower ratio = better executive function
        executive_function = 1.0 / (1.0 + theta_beta_ratio)

        return float(np.clip(executive_function, 0, 1))

    def _compute_asd_likelihood(
        self,
        alpha_beta_ratio: float,
        theta_beta_ratio: float,
        repetition_score: float,
        social_attention: float,
        executive_function: float
    ) -> float:
        """
        Compute likelihood of ASD-related attention patterns.
        This is a heuristic scoring system, not a diagnostic tool.
        """
        asd_indicators = 0
        total_weight = 5

        # Check alpha-beta ratio (ASD: typically lower than typical)
        if 0.4 <= alpha_beta_ratio <= 0.8:
            asd_indicators += 1.0
        elif alpha_beta_ratio < 0.4:
            asd_indicators += 0.8

        # Check theta-beta ratio (ASD: typically higher)
        if 1.2 <= theta_beta_ratio <= 2.0:
            asd_indicators += 1.0
        elif theta_beta_ratio > 2.0:
            asd_indicators += 0.8

        # Repetitive patterns (ASD: higher)
        if repetition_score > 0.6:
            asd_indicators += 1.0
        elif repetition_score > 0.4:
            asd_indicators += 0.5

        # Reduced social attention (ASD: lower suppression)
        if social_attention < 0.3:
            asd_indicators += 1.0
        elif social_attention < 0.5:
            asd_indicators += 0.5

        # Lower executive function (ASD: may show variations)
        if executive_function < 0.4:
            asd_indicators += 1.0
        elif executive_function < 0.6:
            asd_indicators += 0.5

        asd_likelihood = asd_indicators / total_weight
        return float(np.clip(asd_likelihood, 0, 1))

    @staticmethod
    def _interpret_asd_score(score: float) -> str:
        """Interpret ASD likelihood score"""
        if score < 0.3:
            return "Low likelihood of ASD-related attention patterns"
        elif score < 0.5:
            return "Moderate atypical attention patterns detected"
        elif score < 0.7:
            return "Notable ASD-associated attention characteristics observed"
        else:
            return "Strong indicators of ASD-related attention patterns"

    def _generate_recommendations(
        self,
        profile: AttentionProfile,
        asd_likelihood: float
    ) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        if profile.attention_variability > 0.5:
            recommendations.append("Consider structured attention training or behavioral interventions")

        if profile.social_attention_score < 0.4:
            recommendations.append("Focused social attention exercises may be beneficial")

        if profile.repetitive_pattern_score > 0.6:
            recommendations.append("Monitor for stereotyped or repetitive behaviors")

        if profile.stimulus_sensitivity > 0.7:
            recommendations.append("Consider sensory processing support and environmental modifications")

        if profile.executive_function_score < 0.5:
            recommendations.append("Executive function training and organizational strategies recommended")

        if asd_likelihood > 0.6:
            recommendations.append("Comprehensive neurodevelopmental assessment recommended")

        return recommendations

    def get_longitudinal_analysis(self) -> Dict[str, Any]:
        """Analyze trends over multiple recordings"""
        if len(self.analysis_history) < 2:
            return {"status": "insufficient_data"}

        histories = list(self.analysis_history)

        # Extract trends
        asd_scores = [h["asd_likelihood"]["score"] for h in histories]
        social_scores = [h["profile"]["social_attention_score"] for h in histories]
        repetition_scores = [h["profile"]["repetitive_pattern_score"] for h in histories]

        return {
            "num_recordings": len(histories),
            "asd_score_trend": {
                "values": asd_scores,
                "mean": float(np.mean(asd_scores)),
                "std": float(np.std(asd_scores)),
                "trend": "increasing" if asd_scores[-1] > asd_scores[0] else "decreasing"
            },
            "social_attention_trend": {
                "values": social_scores,
                "mean": float(np.mean(social_scores)),
                "std": float(np.std(social_scores))
            },
            "repetitive_patterns_trend": {
                "values": repetition_scores,
                "mean": float(np.mean(repetition_scores)),
                "std": float(np.std(repetition_scores))
            }
        }


def create_asd_analyzer(fs: float = 250.0) -> ASDAttentionAnalyzer:
    """
    Create a new ASD attention analyzer.

    Args:
        fs: Sampling frequency in Hz

    Returns:
        ASDAttentionAnalyzer instance
    """
    return ASDAttentionAnalyzer(fs=fs)


def analyze_asd_attention(
    eeg_signal: np.ndarray,
    duration_seconds: float = 1.0,
    context: str = "neutral",
    fs: float = 250.0
) -> Dict[str, Any]:
    """
    Perform ASD attention analysis on EEG data.

    Args:
        eeg_signal: EEG data
        duration_seconds: Duration of recording
        context: Recording context
        fs: Sampling frequency

    Returns:
        Analysis results
    """
    analyzer = ASDAttentionAnalyzer(fs=fs)
    return analyzer.analyze_attention_profile(eeg_signal, duration_seconds, context)
