# Contributing to AAA Engine

Thank you for your interest in contributing to AAA Engine! This document provides guidelines for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism
- Focus on what's best for the project
- Show empathy towards other contributors

### Unacceptable Behavior

- Harassment or discriminatory language
- Trolling or insulting comments
- Publishing others' private information
- Other unprofessional conduct

---

## How to Contribute

### Reporting Bugs

**Before submitting a bug report:**
1. Check existing [Issues](https://github.com/Speech-Synthesis/AAA_Baselines/issues)
2. Ensure you're using the latest version
3. Verify the issue is reproducible

**Bug Report Template:**
```markdown
**Description**: Brief description of the bug

**Steps to Reproduce**:
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**: What should happen

**Actual Behavior**: What actually happens

**Environment**:
- OS: [e.g., Windows 11]
- Python Version: [e.g., 3.11.2]
- Node Version: [e.g., 20.10.0]
- Browser: [e.g., Chrome 120]

**Logs**:
```
Paste relevant error logs here
```
```

### Suggesting Features

**Feature Request Template:**
```markdown
**Problem**: What problem does this solve?

**Proposed Solution**: How should it work?

**Alternatives**: What alternatives have you considered?

**Additional Context**: Any relevant information
```

### Contributing Code

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**: Follow coding standards
4. **Test your changes**: Ensure all tests pass
5. **Commit**: Follow commit guidelines
6. **Push**: `git push origin feature/your-feature-name`
7. **Open Pull Request**: Use PR template

---

## Development Setup

### 1. Fork and Clone

```bash
git clone https://github.com/YOUR_USERNAME/AAA_Baselines.git
cd AAA_Baselines
git remote add upstream https://github.com/Speech-Synthesis/AAA_Baselines.git
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy  # Dev dependencies
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Create .env File

```bash
cp backend/.env.example backend/.env
# Edit .env with your database credentials
```

### 5. Run Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

---

## Coding Standards

### Python (Backend)

**Style Guide**: PEP 8

**Formatting**:
```bash
# Auto-format code
black app/

# Check linting
flake8 app/ --max-line-length=100

# Type checking
mypy app/
```

**Code Structure**:
```python
# Good
def verify_speaker(audio_bytes: bytes, voiceprint: list[float]) -> dict:
    """
    Verify speaker identity against stored voiceprint.

    Args:
        audio_bytes: Raw WAV audio data
        voiceprint: Stored 192-dim ECAPA embedding

    Returns:
        {"score": float, "embedding": list[float]}
    """
    # Implementation
    pass

# Bad
def verify(a, v):  # No type hints, unclear names
    pass  # No docstring
```

**Naming Conventions**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### JavaScript/React (Frontend)

**Style Guide**: Airbnb JavaScript Style Guide

**Formatting**:
```bash
npm run lint
npm run format  # If available
```

**Component Structure**:
```jsx
// Good
import { useState } from 'react';
import { registerUser } from '../api';

export default function Register() {
  const [name, setName] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    // Implementation
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* JSX */}
    </form>
  );
}

// Bad
function register() {  // Not exported, lowercase component name
  var n = '';  // Use const/let, not var
  // No clear structure
}
```

**Naming Conventions**:
- Components: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `UPPER_SNAKE_CASE`
- Event handlers: `handleEventName`

### Database

**Migration Naming**: `YYYY_MM_DD_description.sql`

**Schema Changes**:
- Always create migrations (don't edit models.py directly in production)
- Include rollback scripts
- Test migrations on sample data

---

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code formatting (no logic change)
- `refactor`: Code restructuring (no behavior change)
- `test`: Add/modify tests
- `chore`: Build process, dependencies

**Examples**:
```bash
feat(layer1): Add ECAPA-TDNN speaker verification

- Implement embedding extraction
- Add cosine similarity comparison
- Configure threshold at 0.7

Closes #23

---

fix(frontend): Resolve CORS error on production

Change API_BASE to use environment-based detection instead
of hardcoded localhost.

Fixes #45

---

docs(readme): Update installation instructions

Add Supabase setup steps and troubleshooting section.
```

**Bad Examples**:
```bash
# Too vague
update stuff

# No type prefix
added feature

# Too long subject (>72 chars)
feat(backend): Implement the new authentication layer with deepfake detection and speaker verification
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated (README, docstrings)
- [ ] No merge conflicts with main branch
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

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Related Issues
Closes #[issue number]
```

### Review Process

1. **Automated Checks**: CI/CD must pass
2. **Code Review**: At least 1 maintainer approval required
3. **Testing**: Reviewers verify functionality
4. **Merge**: Squash and merge to main

### After Merge

- Delete your feature branch
- Update your fork:
  ```bash
  git checkout main
  git pull upstream main
  git push origin main
  ```

---

## Project Structure

```
AAA_Baselines/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + routes
│   │   ├── db.py                # Database engine
│   │   ├── models.py            # ORM models
│   │   ├── layer1_speaker.py    # Speaker verification
│   │   ├── layer2_deepfake.py   # Deepfake detection
│   │   ├── layer3_adaptive.py   # Challenge + EMA
│   │   └── layer3_asr.py        # ASR phrase verification
│   ├── tests/                   # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── api.js               # API client
│   │   └── App.jsx              # Router
│   └── package.json
└── docs/
    ├── TEAM_CONTRACT.md         # Team contract
    └── DB_SCHEMA.sql            # Database schema
```

### Where to Make Changes

**Layer 1 (Speaker Verification)**: `backend/app/layer1_speaker.py`
**Layer 2 (Deepfake Detection)**: `backend/app/layer2_deepfake.py`
**Layer 3 (Challenge/EMA)**: `backend/app/layer3_adaptive.py`
**ASR Phrase Verification**: `backend/app/layer3_asr.py`
**API Routes**: `backend/app/main.py`
**Database Models**: `backend/app/models.py`
**Frontend Pages**: `frontend/src/components/`

---

## Branch Strategy

**Main Branch**: `main` (protected, requires PR)

**Feature Branches**:
- `feature/layer1-improvements`
- `feature/frontend-dashboard`
- `fix/cors-issue`
- `docs/update-readme`

**Original Team Branches** (historical):
- `infra-backend` (Navadeep)
- `layer1-speaker` (Surya)
- `layer2-deepfake` (Nandan)
- `layer3-frontend` (Aditya)

**Naming Convention**: `<type>/<description>` (lowercase, hyphens)

---

## Testing Guidelines

### Backend Tests

**Location**: `backend/tests/`

**Example**:
```python
import pytest
from app.layer1_speaker import verify_speaker

def test_speaker_verification_accept():
    # Load test audio and voiceprint
    audio = load_test_audio("user1_sample1.wav")
    voiceprint = load_test_voiceprint("user1")

    result = verify_speaker(audio, voiceprint)

    assert result["score"] >= 0.7
    assert len(result["embedding"]) == 192
```

**Run Tests**:
```bash
pytest                    # All tests
pytest -v                 # Verbose
pytest tests/test_layer1.py  # Specific file
pytest --cov=app          # With coverage
```

### Frontend Tests

**Location**: `frontend/src/__tests__/`

**Example**:
```javascript
import { render, screen } from '@testing-library/react';
import Register from '../components/Register';

test('renders registration form', () => {
  render(<Register />);
  expect(screen.getByText(/Register/i)).toBeInTheDocument();
});
```

---

## Documentation

### Docstring Format (Python)

```python
def verify_speaker(audio_bytes: bytes, voiceprint: list[float]) -> dict:
    """
    Verify speaker identity using ECAPA-TDNN embeddings.

    Args:
        audio_bytes: Raw WAV audio data (16kHz mono)
        voiceprint: Stored 192-dimensional embedding

    Returns:
        dict: {
            "score": float (cosine similarity 0-1),
            "embedding": list[float] (192-dim)
        }

    Raises:
        ValueError: If audio format is invalid

    Example:
        >>> audio = open("sample.wav", "rb").read()
        >>> voiceprint = [0.1, 0.2, ...]  # 192 values
        >>> result = verify_speaker(audio, voiceprint)
        >>> result["score"]
        0.87
    """
```

### Code Comments

```python
# Good: Explain WHY, not WHAT
# Use EMA to prevent one-shot voiceprint poisoning attacks
voiceprint_new = 0.8 * voiceprint_old + 0.2 * embedding_current

# Bad: Redundant comment
# Multiply voiceprint_old by 0.8
voiceprint_new = 0.8 * voiceprint_old + 0.2 * embedding_current
```

---

## Release Process

1. **Version Bump**: Update version in `package.json`, `__init__.py`
2. **Changelog**: Update `CHANGELOG.md`
3. **Tag**: `git tag -a v1.0.0 -m "Release v1.0.0"`
4. **Push**: `git push origin main --tags`
5. **GitHub Release**: Create release notes

**Version Format**: Semantic Versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

---

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/Speech-Synthesis/AAA_Baselines/discussions)
- **Bugs**: Open an [Issue](https://github.com/Speech-Synthesis/AAA_Baselines/issues)
- **Security**: Email maintainers (do not open public issue)

---

## Recognition

Contributors will be acknowledged in:
- `README.md` Contributors section
- GitHub Contributors page
- Release notes (for significant contributions)

---

**Thank you for contributing to AAA Engine!**
