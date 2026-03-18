import numpy as np
from core.tools.hybrid_bci import HybridBCI, BCIParadigm, BCICommand, create_hybrid_bci


def test_hybrid_bci_init():
    bci = HybridBCI(paradigms=[BCIParadigm.MOTOR_IMAGERY, BCIParadigm.P300])
    assert bci.fusion_method == "voting"
    assert len(bci.paradigms) == 2


def test_bci_command_to_dict():
    cmd = BCICommand(
        command_type="left",
        confidence=0.85,
        paradigm=BCIParadigm.MOTOR_IMAGERY,
        details={"direction": "left"}
    )
    d = cmd.to_dict()
    assert d["command"] == "left"
    assert d["confidence"] == 0.85
    assert d["paradigm"] == "motor_imagery"


def test_process_motor_imagery(sample_multichannel):
    bci = HybridBCI(paradigms=[BCIParadigm.MOTOR_IMAGERY])
    mi_out = bci._process_motor_imagery(sample_multichannel, fs=250.0)
    # returns BCICommand object
    assert hasattr(mi_out, "command_type") or isinstance(mi_out, dict)


def test_process_p300(sample_epoch):
    bci = HybridBCI(paradigms=[BCIParadigm.P300])
    p3_out = bci._process_p300(sample_epoch, fs=250.0)
    # returns BCICommand object
    assert hasattr(p3_out, "command_type") or isinstance(p3_out, dict)


def test_multi_paradigm_processing(sample_multichannel):
    bci = HybridBCI(paradigms=[BCIParadigm.MOTOR_IMAGERY, BCIParadigm.P300])
    result = bci.process_multi_paradigm(sample_multichannel, fs=250.0)
    # returns dict with command, confidence, details, paradigm, timestamp
    assert isinstance(result, dict)
    assert any(k in result for k in ["command", "confidence", "details"])


def test_factory_function():
    bci = create_hybrid_bci()
    assert bci is not None
    assert hasattr(bci, "process_multi_paradigm")


def test_paradigm_weights(sample_multichannel):
    bci = HybridBCI(paradigms=[BCIParadigm.MOTOR_IMAGERY, BCIParadigm.P300])
    # ensure weights sum to 1.0
    weight_sum = sum(bci.paradigm_weights.values())
    assert abs(weight_sum - 1.0) < 0.01
