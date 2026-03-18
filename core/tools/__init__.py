"""
Core Tools Package
Comprehensive toolkit for EEG analysis and BCI applications
"""

from .brain_wave_classifier import (
    classify_brainwave_bands,
    classify_cognitive_state,
    classify_multi_channel
)

from .motor_imagery_cnn import (
    MotorImageryNet,
    classify_motor_imagery,
    extract_motor_imagery_features,
    train_motor_imagery_model
)

from .p300_speller import (
    P300Speller,
    extract_p300_features,
    classify_p300_response,
    create_speller_interface
)

from .bigp3bci import (
    download_bigp3_dataset,
    load_bigp3_record,
    preprocess_bigp3,
    get_bigp3_metadata,
    create_bigp3_interface,
)

from .neurofeedback_loop import (
    NeurofeedbackEngine,
    FeedbackTarget,
    FeedbackModality,
    create_neurofeedback_session
)

from .hybrid_bci import (
    HybridBCI,
    BCIParadigm,
    BCICommand,
    create_hybrid_bci
)

from .asd_attention_analysis import (
    ASDAttentionAnalyzer,
    AttentionProfile,
    create_asd_analyzer,
    analyze_asd_attention
)

__all__ = [
# Brain Wave Classifier
"classify_brainwave_bands",
"classify_cognitive_state",
"classify_multi_channel",

# Motor Imagery CNN
"MotorImageryNet",
"classify_motor_imagery",
"extract_motor_imagery_features",
"train_motor_imagery_model",

# P300 Speller
"P300Speller",
"extract_p300_features",
"classify_p300_response",
"create_speller_interface",
# bigP3BCI Dataset
"download_bigp3_dataset",
"load_bigp3_record",
"preprocess_bigp3",
"get_bigp3_metadata",
"create_bigp3_interface",

# Neurofeedback Loop
"NeurofeedbackEngine",
"FeedbackTarget",
"FeedbackModality",
"create_neurofeedback_session",

# Hybrid BCI
"HybridBCI",
"BCIParadigm",
"BCICommand",
"create_hybrid_bci",

# ASD Attention Analysis
"ASDAttentionAnalyzer",
"AttentionProfile",
"create_asd_analyzer",
"analyze_asd_attention",
]
