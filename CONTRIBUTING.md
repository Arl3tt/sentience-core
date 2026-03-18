# Contributing to Sentience Core

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the Sentience Core project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Code Quality](#code-quality)
7. [Commit Guidelines](#commit-guidelines)
8. [Submitting Pull Requests](#submitting-pull-requests)
9. [Documentation](#documentation)
10. [Performance Guidelines](#performance-guidelines)

---

## Code of Conduct

We are committed to providing a welcoming and harassment-free environment for everyone. Contributors are expected to:

- Be respectful and inclusive
- Welcome constructive feedback
- Focus on code and ideas, not individuals
- Report inappropriate behavior to maintainers

---

## Getting Started

### Prerequisites

- Python 3.13+
- Git
- A GitHub account
- Familiarity with Python and basic BCI concepts (for BCI-related contributions)

### Fork & Clone

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR-USERNAME/sentience-core.git
cd sentience-core

# Add upstream remote
git remote add upstream https://github.com/Arl3tt/sentience-core.git
```

---

## Development Setup

### Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If available
```

### IDE Setup

**Recommended**: VS Code with extensions:
- Python
- Pylance
- GitLens
- Pytest Explorer

**Settings** (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": ["--max-line-length=120"],
  "editor.formatOnSave": false,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

---

## Making Changes

### Branch Naming

Create feature branches with descriptive names:

```bash
# Feature branches
git checkout -b feature/add-bci-tool
git checkout -b feature/improve-memory-store

# Bug fix branches
git checkout -b bugfix/fix-import-error
git checkout -b bugfix/handle-redis-timeout

# Documentation
git checkout -b docs/update-api-reference

# Chores
git checkout -b chore/update-dependencies
```

### Code Style Guidelines

#### Python Style

Follow PEP 8 with `max-line-length=120`:

```python
# ✅ Good
def process_eeg_signal(
    signal: np.ndarray,
    sampling_frequency: float,
    band_range: Tuple[float, float]
) -> Dict[str, float]:
    """Extract band power from EEG signal.
    
    Args:
        signal: EEG samples (time series)
        sampling_frequency: Sampling rate in Hz
        band_range: (low_freq, high_freq) tuple
    
    Returns:
        Dictionary with band power metrics
    """
    # Implementation...
    pass

# ❌ Avoid
def process_eeg_signal(signal, sfreq, band_range):
    # Missing docstring and type hints
    pass
```

#### Imports

```python
# ✅ Good - organized by type
import json
import logging
import os
from typing import Dict, List, Tuple

import numpy as np

from core.tools import classify_brainwave_bands
from core.memory import semantic_search

# ❌ Avoid
from typing import *
import numpy as np, scipy, sklearn  # Multiple imports on same line
```

#### Type Hints

```python
# ✅ Good
def extract_features(
    signal: np.ndarray,
    fs: float = 250.0,
    bands: Optional[List[Tuple[float, float]]] = None
) -> Dict[str, float]:
    """Extract spectral features from signal."""
    pass

# ❌ Avoid
def extract_features(signal, fs=250.0, bands=None):
    """Extract spectral features from signal."""
    pass
```

#### Docstrings

Use Google-style docstrings:

```python
def detect_p300(
    signal: np.ndarray,
    fs: float = 250.0,
    threshold: float = 0.5
) -> Tuple[bool, float]:
    """Detect P300 component in ERP signal.
    
    Uses peak detection and morphological analysis to identify
    the P300 component in event-related potential recordings.
    
    Args:
        signal: 1D array of EEG samples
        fs: Sampling frequency in Hz
        threshold: Detection threshold (0-1)
    
    Returns:
        Tuple of (detected: bool, confidence: float)
    
    Raises:
        ValueError: If signal is empty or invalid
    
    Example:
        >>> signal = np.random.randn(1000)
        >>> detected, conf = detect_p300(signal)
        >>> print(f"P300 detected: {detected}, confidence: {conf:.2f}")
    """
    # Implementation...
    pass
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_bigp3.py -v

# Run specific test
pytest tests/test_motor_imagery.py::test_extract_features_shape -v

# Run with coverage
pytest tests/ --cov=core --cov=memory --cov-report=html

# Run specific test pattern
pytest -k "test_classify" -v
```

### Writing Tests

```python
# ✅ Good test
def test_bandpower_extraction():
    """Test that bandpower extraction returns correct dimensions."""
    # Arrange
    signal = np.random.randn(1000)
    fs = 250.0
    bands = [(8, 13), (13, 30)]  # alpha, beta
    
    # Act
    powers = extract_bandpower(signal, fs, bands)
    
    # Assert
    assert len(powers) == len(bands), "Should return power for each band"
    assert all(p >= 0 for p in powers), "Powers should be non-negative"

# ❌ Avoid
def test_bandpower():
    """Test bandpower."""
    signal = np.random.randn(1000)
    powers = extract_bandpower(signal, 250.0, None)
    assert powers is not None  # Too vague
```

### Test Coverage Goals

- **Overall**: ≥ 80% of code
- **Core modules**: ≥ 85%
- **Critical paths**: 100%
- **Generators**: ≥ 90%

---

## Code Quality

### Linting

```bash
# Run flake8
flake8 --max-line-length=120

# Fix common issues automatically
autopep8 --in-place --aggressive --aggressive <file>

# Check import order
isort --check-only --diff <file>
```

### Security Checks

```bash
# Run bandit
bandit -r core memory models data -ll

# Check dependencies
safety check

# SBOM generation
pip-audit
```

### Pre-commit Hooks

Setup automatic checks before commit:

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks (create .pre-commit-config.yaml)
pre-commit install

# Run manually
pre-commit run --all-files
```

Sample `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.13
        
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120']
        
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

---

## Commit Guidelines

### Commit Message Format

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, missing semicolons, etc)
- `refactor`: Code refactoring without feature changes
- `perf`: Performance improvements
- `test`: Test additions or modifications
- `chore`: Build, CI/CD, or dependency changes

#### Examples

```bash
# Good commits
git commit -m "feat(tools): add P300 speller detection

Implements P300 component detection using morphological
analysis and peak detection. Includes:
- extract_p300_features: Feature extraction
- detect_p300: Component detection with threshold
- 95% accuracy on benchmark dataset

Closes #123"

git commit -m "fix(memory): handle Redis connection timeout

Retry connection up to 3 times with exponential backoff.
Add graceful fallback to in-memory store if Redis unavailable.

Fixes #456"

git commit -m "docs: update README with deployment guide"

git commit -m "test: add coverage for motor imagery CNN"
```

---

## Submitting Pull Requests

### Before Submitting

```bash
# Update your branch with latest upstream
git fetch upstream
git rebase upstream/main

# Run full test suite
pytest tests/ -v
flake8 --max-line-length=120
```

### PR Description Template

```markdown
## Description
Brief description of changes and why they're needed.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring
- [ ] Performance improvement

## Related Issues
Closes #123

## Changes Made
- Specific change 1
- Specific change 2
- Specific change 3

## Testing
- [ ] All tests pass
- [ ] Added/updated tests
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines (flake8 passing)
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes
```

### PR Review Process

1. **Automated Checks**
   - Linting (flake8) must pass
   - All tests must pass
   - Coverage must not decrease
   
2. **Code Review**
   - At least 1 maintainer approval required
   - Constructive feedback provided
   - Common issues explained
   
3. **Final Approval**
   - All conversations resolved
   - Rebase on latest main
   - Merge via "Squash and merge"

---

## Documentation

### README Updates

Update README.md if your changes:
- Add new features
- Change API
- Add dependencies
- Update setup instructions

### Code Comments

```python
# ✅ Good - explains why, not what
# Check for P300 component in 200-600ms window to account for
# individual variability in latency (+/- 100ms from standard 300ms)
if 100 < peak_latency < 600:
    detected = True

# ❌ Avoid - states the obvious
# Check if latency is between 100 and 600
if 100 < peak_latency < 600:
    detected = True
```

### API Documentation

Add docstrings to all public functions:

```python
def create_bci_interface(
    paradigm: str = "motor_imagery",
    **kwargs
) -> BCIInterface:
    """Create a BCI interface for specified paradigm.
    
    Supported paradigms: motor_imagery, p300, hybrid, asd_analysis
    
    Args:
        paradigm: Type of BCI interface
        **kwargs: Additional paradigm-specific parameters
    
    Returns:
        BCIInterface instance
    
    Raises:
        ValueError: If paradigm not supported
    
    Example:
        >>> bci = create_bci_interface("motor_imagery")
        >>> result = bci.classify(signal)
    """
```

---

## Performance Guidelines

### Optimization Tips

1. **Avoid unnecessary imports** in module scope
2. **Use vectorized NumPy operations** instead of loops
3. **Profile before optimizing** (use cProfile)
4. **Cache expensive computations** (use functools.lru_cache)
5. **Avoid creating large temporary arrays**

### Performance Testing

```bash
# Profile a script
python -m cProfile -s cumtime scripts/profile_bci_modules.py | head -20

# Benchmark specific function
python -m timeit "import numpy; numpy.fft.fft(numpy.random.randn(1000))"
```

---

## Common Contribution Patterns

### Adding a New BCI Tool

1. Create `core/tools/my_tool.py`
2. Implement main function(s)
3. Add to `core/tools/__init__.py` exports
4. Add tests in `tests/test_my_tool.py`
5. Update documentation
6. Run full test suite

### Fixing a Bug

1. Create minimal test case reproducing bug
2. Make fix
3. Verify test passes
4. Add explanation comment if non-obvious
5. Submit PR with bug fix and test

### Performance Improvement

1. Baseline with benchmark/profiler
2. Implement optimization
3. Verify correctness with tests
4. Document performance gain in PR
5. Update comments explaining optimization

---

## Questions & Support

- **General questions**: GitHub Discussions
- **Bug reports**: GitHub Issues
- **Security issues**: Private security report
- **Documentation**: Check README.md and DEPLOYMENT.md

---

## Acknowledgments

Contributors who help improve Sentience Core are recognized in:
- GitHub Contributor graph
- Project README (with permission)
- Release notes

Thank you for contributing! 🎉

---

**Last Updated**: March 18, 2026
