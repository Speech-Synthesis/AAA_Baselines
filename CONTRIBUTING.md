# Contributing Guide

Guidelines for contributing to AAA Engine.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

### Expected Behavior

- Be respectful and inclusive in all communications
- Accept constructive criticism professionally
- Focus on what benefits the project
- Support fellow contributors

### Unacceptable Behavior

- Harassment or discriminatory language
- Personal attacks or trolling
- Publishing private information without consent
- Other unprofessional conduct

---

## Getting Started

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/AAA_Baselines.git
cd AAA_Baselines

# Add upstream remote
git remote add upstream https://github.com/Speech-Synthesis/AAA_Baselines.git
```

### Development Environment

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy  # Dev tools

# Frontend setup
cd ../frontend
npm install
```

### Environment Configuration

```bash
cp backend/.env.example backend/.env
# Edit .env with your settings
```

---

## Development Workflow

### Branch Strategy

| Branch Type | Naming | Example |
|-------------|--------|---------|
| Feature | `feature/<description>` | `feature/gpu-acceleration` |
| Bug Fix | `fix/<description>` | `fix/cors-header-issue` |
| Documentation | `docs/<description>` | `docs/api-reference` |
| Refactor | `refactor/<description>` | `refactor/layer1-cleanup` |

### Workflow Steps

1. **Sync with upstream**
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make changes and commit**
   ```bash
   git add <files>
   git commit -m "feat(scope): description"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open Pull Request**
   - Use the PR template
   - Link related issues

---

## Coding Standards

### Python (Backend)

**Style:** PEP 8

**Tools:**
```bash
# Format code
black app/

# Check linting
flake8 app/ --max-line-length=100

# Type checking
mypy app/
```

**Naming Conventions:**

| Element | Convention | Example |
|---------|------------|---------|
| Functions | snake_case | `verify_speaker` |
| Variables | snake_case | `audio_bytes` |
| Classes | PascalCase | `AuthLogResponse` |
| Constants | UPPER_SNAKE | `L2_THRESHOLD` |
| Private | _leading | `_load_model` |

**Function Documentation:**

```python
def verify_speaker(
    audio_bytes: bytes,
    stored_embedding: list[float]
) -> dict:
    """
    Compare audio to stored voiceprint.

    Args:
        audio_bytes: Raw WAV audio data (16kHz mono)
        stored_embedding: 192-dimensional ECAPA embedding

    Returns:
        dict: {
            "score": float,  # Cosine similarity [0, 1]
            "embedding": list[float]  # For EMA update
        }

    Raises:
        ValueError: If audio format is invalid

    Example:
        >>> audio = open("sample.wav", "rb").read()
        >>> result = verify_speaker(audio, voiceprint)
        >>> result["score"]
        0.87
    """
```

### JavaScript/React (Frontend)

**Style:** Airbnb JavaScript Style Guide

**Component Structure:**

```jsx
import { useState } from 'react';
import { apiCall } from '../api';

export default function ComponentName() {
  const [state, setState] = useState(initialValue);

  const handleEvent = async (event) => {
    event.preventDefault();
    // Implementation
  };

  return (
    <div>
      {/* JSX */}
    </div>
  );
}
```

**Naming Conventions:**

| Element | Convention | Example |
|---------|------------|---------|
| Components | PascalCase | `RegisterPage` |
| Functions | camelCase | `handleSubmit` |
| Variables | camelCase | `audioBlob` |
| Constants | UPPER_SNAKE | `API_BASE` |
| Event handlers | handle* | `handleClick` |

---

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code formatting (no logic change) |
| `refactor` | Code restructuring (no behavior change) |
| `test` | Add or modify tests |
| `chore` | Build process, dependencies |

### Scopes

| Scope | Description |
|-------|-------------|
| `layer1` | Speaker verification |
| `layer2` | Deepfake detection |
| `layer3` | Challenge-response, EMA |
| `asr` | Phrase verification |
| `api` | API routes |
| `db` | Database |
| `frontend` | React application |
| `docker` | Container configuration |

### Examples

**Good:**
```
feat(layer2): add confidence threshold configuration

- Add L2_SPOOF_THRESHOLD environment variable
- Update detect_spoof() to use configurable threshold
- Add threshold documentation

Closes #45
```

```
fix(frontend): resolve microphone permission handling

The permission dialog was not appearing on Safari.
Added explicit getUserMedia call with proper error handling.

Fixes #67
```

**Bad:**
```
update stuff
```

```
added feature
```

---

## Pull Request Process

### Before Submitting

Verify the following:

- [ ] Code follows style guidelines
- [ ] All existing tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No merge conflicts with main
- [ ] Branch is up-to-date with main

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Manually tested

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings

## Related Issues
Closes #<issue number>
```

### Review Process

1. Automated CI checks must pass
2. At least one maintainer approval required
3. All review comments addressed
4. Squash and merge to main

### After Merge

```bash
# Delete local branch
git branch -d feature/your-feature

# Update your fork
git checkout main
git pull upstream main
git push origin main
```

---

## Testing

### Backend Tests

**Location:** `backend/tests/`

**Running Tests:**

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Verbose output
pytest -v

# Specific file
pytest tests/test_layer1.py

# With coverage
pytest --cov=app
```

**Test Structure:**

```python
import pytest
from app.layer1_speaker import verify_speaker

class TestSpeakerVerification:
    def test_verify_speaker_accept(self, sample_audio, sample_voiceprint):
        result = verify_speaker(sample_audio, sample_voiceprint)

        assert "score" in result
        assert "embedding" in result
        assert result["score"] >= 0.0
        assert result["score"] <= 1.0
        assert len(result["embedding"]) == 192

    def test_verify_speaker_reject(self, sample_audio, different_voiceprint):
        result = verify_speaker(sample_audio, different_voiceprint)

        assert result["score"] < 0.5
```

### Frontend Tests

**Location:** `frontend/src/__tests__/`

**Running Tests:**

```bash
cd frontend
npm test
```

---

## Documentation

### Code Comments

Write comments that explain "why", not "what":

```python
# Good: Explain rationale
# Use EMA alpha=0.2 to require ~10 samples for 50% shift,
# preventing single-sample poisoning attacks
voiceprint_new = 0.8 * voiceprint_old + 0.2 * embedding

# Bad: State the obvious
# Multiply old voiceprint by 0.8
voiceprint_new = 0.8 * voiceprint_old + 0.2 * embedding
```

### Documentation Files

| File | Purpose |
|------|---------|
| README.md | Project overview |
| ARCHITECTURE.md | Technical design |
| INSTALLATION.md | Setup instructions |
| CONTRIBUTING.md | This file |
| CHANGELOG.md | Version history |
| DEMO.md | Usage walkthrough |

### Updating Documentation

When making changes:

1. Update relevant doc files
2. Update docstrings for modified functions
3. Update API documentation if endpoints change
4. Add changelog entry for significant changes

---

## Project Structure Reference

```
AAA_Baselines/
|
+-- backend/
|   +-- app/
|   |   +-- main.py              # API routes
|   |   +-- db.py                # Database config
|   |   +-- models.py            # ORM models
|   |   +-- layer1_speaker.py    # Speaker verification
|   |   +-- layer2_deepfake.py   # Deepfake detection
|   |   +-- layer3_adaptive.py   # Challenge + EMA
|   |   +-- layer3_asr.py        # Phrase verification
|   +-- tests/                   # Backend tests
|   +-- requirements.txt
|
+-- frontend/
|   +-- src/
|   |   +-- components/          # React pages
|   |   +-- api.js               # API client
|   |   +-- App.jsx              # Router
|   +-- package.json
|
+-- docs/                        # Additional documentation
```

---

## Getting Help

- **Questions:** Open a [Discussion](https://github.com/Speech-Synthesis/AAA_Baselines/discussions)
- **Bugs:** Open an [Issue](https://github.com/Speech-Synthesis/AAA_Baselines/issues)
- **Security:** Email maintainers directly (do not open public issue)

---

**Thank you for contributing to AAA Engine.**
