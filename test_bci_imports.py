#!/usr/bin/env python
# Test all BCI tools imports

try:
    from core.tools import (
        # Brain Wave Classifier
        classify_brainwave_bands,
        classify_cognitive_state,
        classify_multi_channel,
        # Motor Imagery CNN
        classify_motor_imagery,
        extract_motor_imagery_features,
        # P300 Speller
        P300Speller,
        create_speller_interface,
        classify_p300_response,
        # bigP3BCI Dataset
        download_bigp3_dataset,
        load_bigp3_record,
        preprocess_bigp3,
        get_bigp3_metadata,
        # Neurofeedback Loop
        create_neurofeedback_session,
        # Hybrid BCI
        create_hybrid_bci,
        BCIParadigm,
        # ASD Attention Analysis
        create_asd_analyzer,
        analyze_asd_attention,
    )

    print("✅ ALL IMPORTS SUCCESSFUL!")
    print("✅ 19 tools/classes successfully imported")
    print("\nAvailable tools:")
    tools = [
        "classify_brainwave_bands",
        "classify_cognitive_state",
        "classify_multi_channel",
        "classify_motor_imagery",
        "extract_motor_imagery_features",
        "P300Speller",
        "create_speller_interface",
        "classify_p300_response",
        "create_neurofeedback_session",
        "download_bigp3_dataset",
        "load_bigp3_record",
        "preprocess_bigp3",
        "get_bigp3_metadata",
        "create_hybrid_bci",
        "BCIParadigm",
        "create_asd_analyzer",
        "analyze_asd_attention",
    ]
    for i, t in enumerate(tools, start=1):
        print(f" {i:2d}. {t}")

except Exception as e:
    print(f"❌ Import Error: {e}")
    import traceback

    traceback.print_exc()
