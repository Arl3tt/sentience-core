"""
Hybrid BCI Tool
Multi-modal Brain-Computer Interface combining multiple signal types and paradigms
Integrates EEG, motor imagery, P300, and neurofeedback for robust BCI
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import time
from collections import deque


class BCIParadigm(Enum):
    """BCI paradigm types"""
    MOTOR_IMAGERY = "motor_imagery"
    P300 = "p300"
    SSVEP = "ssvep"  # Steady-state visual evoked potential
    HYBRID = "hybrid"


class BCICommand:
    """Represents a BCI command output"""
    
    def __init__(
        self,
        command_type: str,
        confidence: float,
        paradigm: BCIParadigm,
        details: Dict[str, Any]
    ):
        self.command_type = command_type
        self.confidence = confidence
        self.paradigm = paradigm
        self.details = details
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command_type,
            "confidence": self.confidence,
            "paradigm": self.paradigm.value,
            "details": self.details,
            "timestamp": self.timestamp
        }


class HybridBCI:
    """Multi-modal BCI combining multiple signal processing paradigms"""
    
    def __init__(
        self,
        paradigms: List[BCIParadigm] = None,
        fusion_method: str = "voting"
    ):
        """
        Initialize Hybrid BCI.
        
        Args:
            paradigms: List of enabled paradigms
            fusion_method: How to fuse multiple paradigm outputs ("voting", "weighted", "averaged")
        """
        self.paradigms = paradigms or [
            BCIParadigm.MOTOR_IMAGERY,
            BCIParadigm.P300
        ]
        self.fusion_method = fusion_method
        
        # Command history
        self.command_history = deque(maxlen=1000)
        
        # Paradigm-specific weights for fusion
        self.paradigm_weights = {p: 1.0 / len(self.paradigms) for p in self.paradigms}
        
        # Performance tracking
        self.paradigm_performance = {p: 0.5 for p in self.paradigms}
        self.trials_per_paradigm = {p: 0 for p in self.paradigms}
    
    def process_multi_paradigm(
        self,
        eeg_signal: np.ndarray,
        fs: float = 250.0
    ) -> Dict[str, Any]:
        """
        Process EEG through multiple paradigms and fuse results.
        
        Args:
            eeg_signal: EEG data
            fs: Sampling frequency
        
        Returns:
            Fused BCI command
        """
        paradigm_outputs = []
        
        # Process through each enabled paradigm
        if BCIParadigm.MOTOR_IMAGERY in self.paradigms:
            mi_output = self._process_motor_imagery(eeg_signal, fs)
            paradigm_outputs.append(("motor_imagery", mi_output))
        
        if BCIParadigm.P300 in self.paradigms:
            p300_output = self._process_p300(eeg_signal, fs)
            paradigm_outputs.append(("p300", p300_output))
        
        if BCIParadigm.SSVEP in self.paradigms:
            ssvep_output = self._process_ssvep(eeg_signal, fs)
            paradigm_outputs.append(("ssvep", ssvep_output))
        
        # Fuse outputs
        fused_command = self._fuse_outputs(paradigm_outputs)
        
        # Store in history
        self.command_history.append(fused_command)
        
        return fused_command.to_dict()
    
    def _process_motor_imagery(
        self,
        eeg_signal: np.ndarray,
        fs: float
    ) -> BCICommand:
        """Process motor imagery paradigm"""
        from .motor_imagery_cnn import classify_motor_imagery
        
        try:
            result = classify_motor_imagery(eeg_signal, fs)
            return BCICommand(
                command_type=result.get("predicted_imagery", "unknown"),
                confidence=result.get("confidence", 0.5),
                paradigm=BCIParadigm.MOTOR_IMAGERY,
                details={
                    "class_probabilities": result.get("class_probabilities", {}),
                    "method": result.get("method", "neural")
                }
            )
        except Exception as e:
            return BCICommand(
                command_type="error",
                confidence=0.0,
                paradigm=BCIParadigm.MOTOR_IMAGERY,
                details={"error": str(e)}
            )
    
    def _process_p300(
        self,
        eeg_signal: np.ndarray,
        fs: float
    ) -> BCICommand:
        """Process P300 paradigm"""
        from .p300_speller import classify_p300_response
        
        try:
            result = classify_p300_response(eeg_signal, fs)
            command_type = "select" if result.get("contains_p300") else "idle"
            return BCICommand(
                command_type=command_type,
                confidence=result.get("confidence", 0.5),
                paradigm=BCIParadigm.P300,
                details={
                    "snr": result.get("snr", 0),
                    "amplitude": result.get("p300_amplitude", 0),
                    "latency_ms": result.get("p300_latency_ms", 0)
                }
            )
        except Exception as e:
            return BCICommand(
                command_type="error",
                confidence=0.0,
                paradigm=BCIParadigm.P300,
                details={"error": str(e)}
            )
    
    def _process_ssvep(
        self,
        eeg_signal: np.ndarray,
        fs: float
    ) -> BCICommand:
        """Process SSVEP (Steady-State Visual Evoked Potential) paradigm"""
        from scipy.signal import welch
        
        if eeg_signal.ndim == 2:
            eeg_signal = np.mean(eeg_signal, axis=1)
        
        # Standard SSVEP frequencies (6-15 Hz)
        ssvep_freqs = {
            "6Hz": 6.0,
            "8Hz": 8.0,
            "10Hz": 10.0,
            "12Hz": 12.0,
            "15Hz": 15.0
        }
        
        frequencies, psd = welch(eeg_signal, fs=fs, nperseg=min(512, len(eeg_signal)))
        
        max_power = 0
        detected_freq = None
        
        for freq_label, freq_val in ssvep_freqs.items():
            # Check for power at stimulation frequency and harmonics
            mask = (frequencies >= freq_val - 1) & (frequencies <= freq_val + 1)
            power = np.mean(psd[mask])
            
            if power > max_power:
                max_power = power
                detected_freq = freq_label
        
        confidence = min(1.0, max_power / 50.0)  # Normalize
        command = detected_freq if detected_freq and confidence > 0.3 else "idle"
        
        return BCICommand(
            command_type=command,
            confidence=float(confidence),
            paradigm=BCIParadigm.SSVEP,
            details={
                "detected_frequency": detected_freq,
                "power": float(max_power)
            }
        )
    
    def _fuse_outputs(
        self,
        paradigm_outputs: List[Tuple[str, BCICommand]]
    ) -> BCICommand:
        """
        Fuse outputs from multiple paradigms.
        
        Args:
            paradigm_outputs: List of (paradigm_name, BCICommand) tuples
        
        Returns:
            Fused BCICommand
        """
        if not paradigm_outputs:
            return BCICommand(
                command_type="idle",
                confidence=0.0,
                paradigm=BCIParadigm.HYBRID,
                details={"error": "No paradigm outputs"}
            )
        
        if self.fusion_method == "voting":
            return self._fuse_voting(paradigm_outputs)
        elif self.fusion_method == "weighted":
            return self._fuse_weighted(paradigm_outputs)
        else:  # averaged
            return self._fuse_averaged(paradigm_outputs)
    
    def _fuse_voting(
        self,
        paradigm_outputs: List[Tuple[str, BCICommand]]
    ) -> BCICommand:
        """Majority voting fusion"""
        commands = {}
        for name, cmd in paradigm_outputs:
            if cmd.command_type not in ("error", "idle"):
                commands[cmd.command_type] = commands.get(cmd.command_type, 0) + 1
        
        if not commands:
            return BCICommand(
                command_type="idle",
                confidence=0.0,
                paradigm=BCIParadigm.HYBRID,
                details={"fusion_method": "voting"}
            )
        
        best_command = max(commands.items(), key=lambda x: x[1])[0]
        votes = commands[best_command]
        confidence = votes / len(paradigm_outputs)
        
        return BCICommand(
            command_type=best_command,
            confidence=float(confidence),
            paradigm=BCIParadigm.HYBRID,
            details={
                "fusion_method": "voting",
                "votes": votes,
                "total_paradigms": len(paradigm_outputs)
            }
        )
    
    def _fuse_weighted(
        self,
        paradigm_outputs: List[Tuple[str, BCICommand]]
    ) -> BCICommand:
        """Weighted fusion based on paradigm performance"""
        weighted_scores = {}
        total_weight = 0
        
        for name, cmd in paradigm_outputs:
            if cmd.command_type not in ("error", "idle"):
                # Get paradigm enum
                try:
                    paradigm = BCIParadigm[name.upper()]
                    weight = self.paradigm_weights.get(paradigm, 0.5)
                except:
                    weight = 0.5
                
                score = cmd.confidence * weight
                weighted_scores[cmd.command_type] = weighted_scores.get(cmd.command_type, 0) + score
                total_weight += weight
        
        if not weighted_scores:
            return BCICommand(
                command_type="idle",
                confidence=0.0,
                paradigm=BCIParadigm.HYBRID,
                details={"fusion_method": "weighted"}
            )
        
        best_command = max(weighted_scores.items(), key=lambda x: x[1])[0]
        confidence = weighted_scores[best_command] / max(total_weight, 1e-6)
        
        return BCICommand(
            command_type=best_command,
            confidence=float(confidence),
            paradigm=BCIParadigm.HYBRID,
            details={
                "fusion_method": "weighted",
                "weighted_scores": weighted_scores
            }
        )
    
    def _fuse_averaged(
        self,
        paradigm_outputs: List[Tuple[str, BCICommand]]
    ) -> BCICommand:
        """Average fusion"""
        command_confidences = {}
        
        for name, cmd in paradigm_outputs:
            if cmd.command_type not in ("error", "idle"):
                if cmd.command_type not in command_confidences:
                    command_confidences[cmd.command_type] = []
                command_confidences[cmd.command_type].append(cmd.confidence)
        
        if not command_confidences:
            return BCICommand(
                command_type="idle",
                confidence=0.0,
                paradigm=BCIParadigm.HYBRID,
                details={"fusion_method": "averaged"}
            )
        
        avg_confidences = {
            cmd: np.mean(confs) for cmd, confs in command_confidences.items()
        }
        
        best_command = max(avg_confidences.items(), key=lambda x: x[1])[0]
        
        return BCICommand(
            command_type=best_command,
            confidence=float(avg_confidences[best_command]),
            paradigm=BCIParadigm.HYBRID,
            details={
                "fusion_method": "averaged",
                "avg_confidences": avg_confidences
            }
        )
    
    def update_paradigm_performance(
        self,
        paradigm: BCIParadigm,
        accuracy: float
    ) -> None:
        """
        Update performance metric for a paradigm.
        Influences fusion weights adaptively.
        """
        self.trials_per_paradigm[paradigm] += 1
        
        # Update performance with exponential moving average
        alpha = 0.1
        self.paradigm_performance[paradigm] = (
            (1 - alpha) * self.paradigm_performance[paradigm] +
            alpha * accuracy
        )
        
        # Update weights based on performance
        total_perf = sum(self.paradigm_performance.values())
        if total_perf > 0:
            for p in self.paradigms:
                self.paradigm_weights[p] = self.paradigm_performance[p] / total_perf
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get BCI performance report"""
        return {
            "fusion_method": self.fusion_method,
            "paradigm_performance": self.paradigm_performance,
            "paradigm_weights": self.paradigm_weights,
            "trials_per_paradigm": self.trials_per_paradigm,
            "total_commands": len(self.command_history),
            "recent_commands": [cmd.to_dict() for cmd in list(self.command_history)[-5:]]
        }


def create_hybrid_bci(
    paradigms: List[str] = None,
    fusion: str = "weighted"
) -> HybridBCI:
    """
    Create a new Hybrid BCI system.
    
    Args:
        paradigms: List of paradigm names ("motor_imagery", "p300", "ssvep")
        fusion: Fusion method ("voting", "weighted", "averaged")
    
    Returns:
        HybridBCI instance
    """
    if paradigms is None:
        paradigms = ["motor_imagery", "p300"]
    
    paradigm_map = {
        "motor_imagery": BCIParadigm.MOTOR_IMAGERY,
        "p300": BCIParadigm.P300,
        "ssvep": BCIParadigm.SSVEP
    }
    
    enabled_paradigms = [
        paradigm_map[p] for p in paradigms if p in paradigm_map
    ]
    
    return HybridBCI(paradigms=enabled_paradigms, fusion_method=fusion)
