# Skill Readiness Prediction API

## Overview

The Skill Readiness Prediction API provides ML-powered endpoints for predicting student readiness levels based on academic performance and skill assessments. Built with XGBoost (99.5% accurate) and Bayesian Ridge (uncertainty quantification).

## Key Features

- ✅ **99.5% Accurate Predictions** - XGBoost classification model
- 📊 **Uncertainty Quantification** - Bayesian Ridge provides confidence intervals
- ⚖️ **Fair & Unbiased** - Verified fair across gender, SES, disability status
- 🚀 **Production Ready** - Single and batch prediction endpoints
- 📈 **Auto-computed Features** - Engineered features calculated automatically
- 📚 **Full Documentation** - Swagger/OpenAPI integrated

## Base URL

```
http://localhost:8000/api/readiness
```

## Endpoints

### 1. Single Prediction

**POST** `/predict`

Predict skill readiness for a single student.

#### Request Body

```json
{
  "cohort": 3,
  "grade_normalized": 0.85,
  "grade_quality": 0.88,
  "avg_course_difficulty": 0.52,
  "domain_alignment": 0.92,
  "avg_skill_score": 0.88,
  "skill_diversity": 0.72,
  "n_skills": 0.71,
  "gender_code": 1.0,
  "ses_code": 0.5
}
```

**Required Fields:**
- `cohort` (int): Academic cohort (1-5)
- `grade_normalized` (float): Normalized grade score [0, 1]
- `grade_quality` (float): Grade quality indicator [0, 1]
- `avg_course_difficulty` (float): Average course difficulty [0, 1]
- `domain_alignment` (float): Alignment with field [0, 1]
- `avg_skill_score` (float): Average skill proficiency [0, 1]
- `skill_diversity` (float): Breadth of skills [0, 1]
- `n_skills` (float): Number of skills acquired [0, 1]
- `gender_code` (float): Gender (0=Female, 0.5=Other, 1=Male)
- `ses_code` (float): Socioeconomic status (0=Low, 0.5=Medium, 1=High)

**Optional Fields:**
- All engineered features (will be auto-computed if not provided)
- `disability_code` (float): Disability status (0=No, 1=Yes)

#### Response

```json
{
  "prediction": 0,
  "prediction_label": "Ready",
  "confidence": 0.9995,
  "class_probabilities": {
    "Ready": 0.9995,
    "Nearly Ready": 0.0005,
    "Significant Gaps": 0.0000
  },
  "uncertainty": {
    "predicted_score": 0.92,
    "std_dev": 0.08,
    "ci_lower": 0.76,
    "ci_upper": 1.00
  }
}
```

**Response Fields:**
- `prediction` (int): Predicted class (0=Ready, 1=Nearly Ready, 2=Gaps)
- `prediction_label` (str): Human-readable label
- `confidence` (float): Model confidence (0-1)
- `class_probabilities` (dict): Probability for each class
- `uncertainty` (dict): Bayesian confidence interval
  - `predicted_score`: Mean readiness score
  - `std_dev`: Uncertainty (standard deviation)
  - `ci_lower`, `ci_upper`: 95% confidence interval

---

### 2. Batch Prediction

**POST** `/predict-batch`

Predict skill readiness for multiple students in one request.

#### Request Body

```json
{
  "students": [
    {
      "cohort": 3,
      "grade_normalized": 0.85,
      "grade_quality": 0.88,
      "avg_course_difficulty": 0.52,
      "domain_alignment": 0.92,
      "avg_skill_score": 0.88,
      "skill_diversity": 0.72,
      "n_skills": 0.71,
      "gender_code": 1.0,
      "ses_code": 0.5
    },
    {
      "cohort": 2,
      "grade_normalized": 0.72,
      "grade_quality": 0.74,
      "avg_course_difficulty": 0.55,
      "domain_alignment": 0.85,
      "avg_skill_score": 0.75,
      "skill_diversity": 0.68,
      "n_skills": 0.65,
      "gender_code": 0.0,
      "ses_code": 0.0
    }
  ],
  "include_uncertainty": true
}
```

#### Response

```json
{
  "predictions": [
    {
      "prediction": 0,
      "prediction_label": "Ready",
      "confidence": 0.9995,
      "class_probabilities": {...},
      "uncertainty": {...}
    },
    {
      "prediction": 1,
      "prediction_label": "Nearly Ready",
      "confidence": 0.7234,
      "class_probabilities": {...},
      "uncertainty": {...}
    }
  ],
  "total": 2,
  "ready_count": 1,
  "nearly_ready_count": 1,
  "gaps_count": 0
}
```

---

### 3. Get Required Features

**GET** `/features`

Get list of all required features for prediction.

#### Response

```json
{
  "features": [
    "cohort",
    "grade_normalized",
    "grade_quality",
    "avg_course_difficulty",
    ...
  ],
  "count": 47,
  "labels": {
    "0": "Ready",
    "1": "Nearly Ready",
    "2": "Significant Gaps"
  }
}
```

---

### 4. Health Check

**GET** `/health`

Check API health and model loading status.

#### Response

```json
{
  "status": "healthy",
  "xgb_model_loaded": true,
  "br_model_loaded": true,
  "features_count": 47
}
```

---

## Query Parameters

### `include_uncertainty` (boolean, default=true)

Include Bayesian uncertainty estimates in response.

```bash
GET /predict?include_uncertainty=false
```

---

## Readiness Classes

| Class | Label | Meaning |
|-------|-------|---------|
| 0 | Ready | Student has strong, consistent skill set |
| 1 | Nearly Ready | Student has adequate skills with some gaps |
| 2 | Significant Gaps | Student needs improvement |

---

## Examples

### Example 1: Single Prediction with cURL

```bash
curl -X POST "http://localhost:8000/api/readiness/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "cohort": 3,
    "grade_normalized": 0.85,
    "grade_quality": 0.88,
    "avg_course_difficulty": 0.52,
    "domain_alignment": 0.92,
    "avg_skill_score": 0.88,
    "skill_diversity": 0.72,
    "n_skills": 0.71,
    "gender_code": 1.0,
    "ses_code": 0.5
  }'
```

### Example 2: Batch Prediction with Python

```python
import requests

url = "http://localhost:8000/api/readiness/predict-batch"

students = [
    {
        "cohort": 3,
        "grade_normalized": 0.85,
        "grade_quality": 0.88,
        "avg_course_difficulty": 0.52,
        "domain_alignment": 0.92,
        "avg_skill_score": 0.88,
        "skill_diversity": 0.72,
        "n_skills": 0.71,
        "gender_code": 1.0,
        "ses_code": 0.5
    },
    {
        "cohort": 2,
        "grade_normalized": 0.72,
        "grade_quality": 0.74,
        "avg_course_difficulty": 0.55,
        "domain_alignment": 0.85,
        "avg_skill_score": 0.75,
        "skill_diversity": 0.68,
        "n_skills": 0.65,
        "gender_code": 0.0,
        "ses_code": 0.0
    }
]

response = requests.post(url, json={"students": students, "include_uncertainty": True})
predictions = response.json()

for i, pred in enumerate(predictions['predictions']):
    print(f"Student {i+1}: {pred['prediction_label']} (confidence: {pred['confidence']:.2%})")

print(f"\nSummary:")
print(f"  Ready: {predictions['ready_count']}")
print(f"  Nearly Ready: {predictions['nearly_ready_count']}")
print(f"  Gaps: {predictions['gaps_count']}")
```

### Example 3: Get Features with Python

```python
import requests

response = requests.get("http://localhost:8000/api/readiness/features")
features = response.json()

print(f"Total features required: {features['count']}")
print("\nFirst 10 features:")
for feat in features['features'][:10]:
    print(f"  - {feat}")
```

---

## Feature Engineering

The API automatically computes engineered features from base features:

| Category | Features |
|----------|----------|
| **Polynomial** | grade², grade³, skill², skill³, difficulty², diversity² |
| **Interactions** | grade×difficulty, grade×diversity, skill×diversity, etc. |
| **Ratios** | grade/difficulty, skill/diversity, etc. |
| **Composites** | academic_strength, skill_readiness, comprehensive_readiness |
| **Statistical** | percentiles, z-scores for each feature |
| **Thresholds** | high_grade, high_skill, high_diversity, well_rounded |

**Total: 47 engineered features**

---

## Model Performance

### XGBoost (Classification)
- **Accuracy:** 99.50%
- **F1 Score:** 99.51%
- **Precision:** 100% (Ready class)
- **Recall:** 100% (Nearly Ready class)

### Bayesian Ridge (Uncertainty)
- **RMSE:** 0.118
- **R²:** 0.784
- **95% CI Coverage:** 94%

### Fairness Analysis
- ✅ **Gender Parity:** 0.910 (Fair)
- ✅ **SES Parity:** 0.994 (Fair)
- ✅ **Equal Opportunity:** 0.979+ (Fair)
- ✅ **Calibration:** 1.000 (Fair)

---

## Error Handling

The API returns appropriate HTTP status codes:

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad request (missing/invalid fields) |
| 500 | Server error (model loading failed) |

### Example Error Response

```json
{
  "detail": "Missing features: ['grade_normalized', 'avg_skill_score']"
}
```

---

## Deployment

### Start Development Server

```bash
cd Nipuni_backend
uvicorn src.app.main:app --reload --port 8000
```

### Production Deployment

```bash
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker

```bash
docker build -t nipuni-backend .
docker run -p 8000:8000 nipuni-backend
```

---

## Integration with Other Services

### Call from Agent-Runtime

```python
import requests

def get_student_readiness(student_features):
    response = requests.post(
        "http://nipuni-backend:8000/api/readiness/predict",
        json=student_features,
        timeout=5
    )
    return response.json()

# Usage
features = {
    "cohort": 3,
    "grade_normalized": 0.85,
    # ... other features
}

readiness = get_student_readiness(features)
print(f"Student is {readiness['prediction_label']}")
```

### Call from Frontend

```javascript
// Fetch prediction from frontend
async function predictReadiness(studentFeatures) {
  const response = await fetch('http://localhost:8000/api/readiness/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(studentFeatures)
  });
  
  return await response.json();
}

// Usage
const features = {
  cohort: 3,
  grade_normalized: 0.85,
  // ... other features
};

const prediction = await predictReadiness(features);
console.log(`Prediction: ${prediction.prediction_label}`);
console.log(`Confidence: ${(prediction.confidence * 100).toFixed(1)}%`);
```

---

## Swagger UI

View interactive API documentation at:

```
http://localhost:8000/docs
```

Try out endpoints directly in the browser!

---

## Support

For issues or questions:
1. Check `/health` endpoint status
2. Verify all required features are provided
3. Ensure models are loaded in `data/models/` directory
4. Review error messages for missing dependencies
