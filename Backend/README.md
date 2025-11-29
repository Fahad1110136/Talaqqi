# Talaqqi Backend - AI Tajweed Analysis System

## Overview

Professional FastAPI backend demonstrating **OOP**, **SOLID principles**, and **Design Patterns** for Software Design and Analysis (SDA) course.

## Project Structure

```
Backend/
├── main.py                  # FastAPI application entry point (Application Factory)
├── config.py                # Settings (Singleton, Pydantic)
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
│
├── models/                  # Database models
│   ├── database.py         # SQLAlchemy ORM models
│   └── tajweed_rules.py    # Tajweed rule configurations
│
├── ml/                      # Machine Learning components
│   ├── interfaces/         # Abstract base classes (ISP)
│   │   ├── base_processor.py       # IAudioProcessor
│   │   ├── base_classifier.py      # ITajweedClassifier
│   │   └── base_detector.py        # ITajweedRuleDetector
│   │
│   ├── implementations/    # Concrete implementations  
│   │   ├── audio_processor.py      # Chain of Responsibility
│   │   ├── model_loader.py         # Singleton Pattern
│   │   └── tajweed_classifier.py   # TensorFlow/Keras
│   │
│   ├── detectors/          # Rule detectors (Open/Closed)
│   │   ├── madd_detector.py        # Al-Madd rule
│   │   ├── ghunnah_detector.py     # Ghunnah rule
│   │   └── ikhfa_detector.py       # Ikhfāʾ rule
│   │
│   ├── factories/          # Factory Pattern
│   │   └── detector_factory.py     # Create detectors
│   │
│   └── facades/            # Facade Pattern
│       └── tajweed_analyzer.py     # Simplified ML pipeline
│
└── utils/                   # Utility modules
    ├── exceptions.py       # Custom exception hierarchy
    ├── audio_utils.py      # Audio file utilities
    └── response_helpers.py # API response formatting
```

## Design Patterns Implemented

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Singleton** | `model_loader.py` | Ensure only one ML model in memory |
| **Factory** | `detector_factory.py` | Create Tajweed rule detectors |
| **Strategy** | `audio_processor.py` | Swappable feature extraction (MFCC/Mel-spec) |
| **Facade** | `tajweed_analyzer.py` | Simplify complex ML pipeline |
| **Chain of Responsibility** | `audio_processor.preprocess()` | Audio preprocessing pipeline |
| **Application Factory** | `main.py:create_app()` | FastAPI app configuration |

## SOLID Principles

### Single Responsibility Principle (SRP)
- `AudioProcessor`: Only handles audio preprocessing
- `TajweedClassifier`: Only performs ML inference
- `MaddDetector`, `GhunnahDetector`, `IkhfaDetector`: Each handles ONE Tajweed rule

### Open/Closed Principle (OCP)
- New Tajweed rules can be added by creating new detector classes
- `TajweedRuleDetectorFactory.register_detector()` allows extension without modification

### Liskov Substitution Principle (LSP)
- All detectors implement `ITajweedRuleDetector` and are interchangeable
- `AudioProcessor` can be swapped with `MelSpectrogramExtractor`

### Interface Segregation Principle (ISP)
- Separate interfaces: `IAudioProcessor`, `ITajweedClassifier`, `ITajweedRuleDetector`
- Clients only depend on methods they use

### Dependency Inversion Principle (DIP)
- High-level `TajweedAnalyzer` depends on abstractions (interfaces), not concrete classes
- Dependency Injection used in `TajweedAnalyzer.__init__()`

## Setup & Installation

### 1. Install Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Initialize Database

```python
from models.database import init_db
init_db()
```

### 4. Run Application

```bash
python main.py
# Or with uvicorn:
uvicorn main:app --reload
```

Server will start at: `http://localhost:8000`
API Docs: `http://localhost:8000/api/v1/docs`

## Usage Example

```python
from ml.facades.tajweed_analyzer import TajweedAnalyzer

# Create analyzer (Facade pattern)
analyzer = TajweedAnalyzer()

# Analyze audio file
result = analyzer.analyze_audio_file("recitation.wav")

print(f"Overall Score: {result['overall_score']}")
print(f"Detections: {len(result['detections'])}")
for feedback in result['feedback']:
    print(feedback)
```

## Code Quality Features

- ✅ **Type Hints**: All functions have type annotations
- ✅ **Docstrings**: Google-style documentation
- ✅ **Logging**: Comprehensive logging at all levels
- ✅ **Error Handling**: Custom exception hierarchy
- ✅ **Validation**: Input validation with Pydantic
- ✅ **Modularity**: Max 200 lines per file

## Testing (Future)

```bash
# Unit tests
pytest tests/test_audio_processor.py
pytest tests/test_tajweed_classifier.py

# Integration tests
pytest tests/test_api_endpoints.py
```

## API Endpoints (Planned)

- `POST /api/v1/analysis/upload` - Upload audio for analysis
- `WS /api/v1/ws/analyze` - Real-time WebSocket analysis
- `GET /api/v1/analysis/{id}` - Get analysis results
- `GET /api/v1/progress/{student_id}` - Get student progress

## Database Schema

**Tables**: `users`, `sessions`, `recitation_analyses`, `tajweed_errors`, `student_progress`

See `models/database.py` for full schema.

## ML Model

**Architecture**: CNN/LSTM with TensorFlow/Keras
**Input**: MFCC features (40 coefficients) or Mel-spectrograms
**Output**: Probabilities for 3 Tajweed rules (Al-Madd, Ghunnah, Ikhfāʾ)
**Training Data**: QDAT dataset (Surah Al-Ma'idah verse 109)

## License

Educational project for SDA course.
