"""
FastAPI Routes for Skill Readiness Prediction
Endpoints for single predictions, batch predictions, and model information
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from ..models.readiness_predictor import SkillReadinessPredictor
import os

router = APIRouter(prefix="/api/readiness", tags=["Readiness Prediction"])

# Initialize predictor (singleton)
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        xgb_model = os.path.join(base_path, 'data/models/xgboost_readiness.pkl')
        xgb_features = os.path.join(base_path, 'data/models/xgboost_readiness_features.pkl')
        br_model = os.path.join(base_path, 'data/models/bayesian_ridge_uncertainty.pkl')
        br_scaler = os.path.join(base_path, 'data/models/bayesian_ridge_uncertainty_scaler.pkl')
        
        predictor = SkillReadinessPredictor(
            xgb_model_path=xgb_model,
            xgb_features_path=xgb_features,
            br_model_path=br_model,
            br_scaler_path=br_scaler
        )
    return predictor

# Pydantic models for request/response

class StudentFeaturesRequest(BaseModel):
    """Student features for readiness prediction"""
    cohort: int = Field(..., description="Academic cohort (1-5)")
    grade_normalized: float = Field(..., ge=0, le=1, description="Normalized grade (0-1)")
    grade_quality: float = Field(..., ge=0, le=1, description="Grade quality score")
    avg_course_difficulty: float = Field(..., ge=0, le=1, description="Average course difficulty")
    domain_alignment: float = Field(..., ge=0, le=1, description="Domain alignment score")
    avg_skill_score: float = Field(..., ge=0, le=1, description="Average skill score")
    skill_diversity: float = Field(..., ge=0, le=1, description="Skill diversity ratio")
    n_skills: float = Field(..., ge=0, le=1, description="Number of skills (normalized)")
    gender_code: float = Field(..., description="Gender code (0=Female, 0.5=Other, 1=Male)")
    ses_code: float = Field(..., ge=0, le=1, description="SES code (0=Low, 0.5=Medium, 1=High)")
    
    # Engineered features (optional - can be auto-computed)
    grade_normalized_squared: Optional[float] = None
    grade_normalized_cubed: Optional[float] = None
    avg_skill_score_squared: Optional[float] = None
    avg_skill_score_cubed: Optional[float] = None
    grade_normalized_x_avg_course_difficulty: Optional[float] = None
    grade_normalized_x_skill_diversity: Optional[float] = None
    grade_normalized_x_domain_alignment: Optional[float] = None
    avg_skill_score_x_skill_diversity: Optional[float] = None
    avg_skill_score_x_domain_alignment: Optional[float] = None
    skill_diversity_x_domain_alignment: Optional[float] = None
    skill_diversity_x_n_skills: Optional[float] = None
    avg_course_difficulty_squared: Optional[float] = None
    skill_diversity_squared: Optional[float] = None
    domain_alignment_squared: Optional[float] = None
    grade_normalized_to_avg_course_difficulty: Optional[float] = None
    avg_skill_score_to_skill_diversity: Optional[float] = None
    domain_alignment_to_avg_course_difficulty: Optional[float] = None
    difficulty_inverse: Optional[float] = None
    academic_strength: Optional[float] = None
    skill_readiness: Optional[float] = None
    comprehensive_readiness: Optional[float] = None
    difficulty_adjusted_score: Optional[float] = None
    grade_normalized_percentile: Optional[float] = None
    avg_skill_score_percentile: Optional[float] = None
    skill_diversity_percentile: Optional[float] = None
    domain_alignment_percentile: Optional[float] = None
    grade_normalized_zscore: Optional[float] = None
    avg_skill_score_zscore: Optional[float] = None
    skill_diversity_zscore: Optional[float] = None
    domain_alignment_zscore: Optional[float] = None
    high_grade: Optional[int] = None
    high_skill: Optional[int] = None
    high_diversity: Optional[int] = None
    good_domain_fit: Optional[int] = None
    well_rounded: Optional[int] = None
    skill_std: Optional[float] = None
    grade_quality: Optional[float] = None
    disability_code: Optional[float] = 0.0

class PredictionResponse(BaseModel):
    """Response from prediction endpoint"""
    prediction: int
    prediction_label: str
    confidence: float
    class_probabilities: Dict[str, float]
    uncertainty: Optional[Dict] = None

class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    students: List[StudentFeaturesRequest]
    include_uncertainty: bool = True

class BatchPredictionResponse(BaseModel):
    """Batch prediction response"""
    predictions: List[PredictionResponse]
    total: int
    ready_count: int
    nearly_ready_count: int
    gaps_count: int

# Endpoints

@router.post("/predict", response_model=PredictionResponse)
async def predict_single(request: StudentFeaturesRequest, include_uncertainty: bool = True):
    """
    Predict skill readiness for a single student
    
    Returns:
    - prediction: Readiness class (0=Ready, 1=Nearly Ready, 2=Gaps)
    - confidence: Model confidence (0-1)
    - class_probabilities: Probability for each class
    - uncertainty: 95% confidence interval from Bayesian model
    """
    try:
        pred = get_predictor()
        
        # Convert request to dict
        features = request.dict(exclude_none=True)
        
        # Auto-compute engineered features if not provided
        features = _compute_engineered_features(features)
        
        result = pred.predict_single(features, include_uncertainty=include_uncertainty)
        return PredictionResponse(**result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/predict-batch", response_model=BatchPredictionResponse)
async def predict_batch(request: BatchPredictionRequest):
    """
    Batch predict skill readiness for multiple students
    
    Returns:
    - predictions: List of predictions
    - summary statistics (counts by class)
    """
    try:
        pred = get_predictor()
        
        # Convert requests to dicts
        features_list = [s.dict(exclude_none=True) for s in request.students]
        
        # Auto-compute engineered features
        features_list = [_compute_engineered_features(f) for f in features_list]
        
        results = pred.predict_batch(features_list, include_uncertainty=request.include_uncertainty)
        
        # Count by class
        predictions = [PredictionResponse(**r) for r in results]
        ready_count = sum(1 for p in predictions if p.prediction == 0)
        nearly_ready_count = sum(1 for p in predictions if p.prediction == 1)
        gaps_count = sum(1 for p in predictions if p.prediction == 2)
        
        return BatchPredictionResponse(
            predictions=predictions,
            total=len(predictions),
            ready_count=ready_count,
            nearly_ready_count=nearly_ready_count,
            gaps_count=gaps_count
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@router.get("/features")
async def get_required_features():
    """Get list of required features for prediction"""
    pred = get_predictor()
    return {
        'features': pred.get_feature_names(),
        'count': len(pred.get_feature_names()),
        'labels': pred.get_label_names()
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        pred = get_predictor()
        return {
            'status': 'healthy',
            'xgb_model_loaded': pred.xgb_model is not None,
            'br_model_loaded': pred.br_model is not None,
            'features_count': len(pred.xgb_features)
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }

# Helper functions

def _compute_engineered_features(features: Dict) -> Dict:
    """Auto-compute engineered features if not provided"""
    
    # Base features
    grade = features.get('grade_normalized', 0)
    skill = features.get('avg_skill_score', 0)
    difficulty = features.get('avg_course_difficulty', 0)
    diversity = features.get('skill_diversity', 0)
    domain = features.get('domain_alignment', 0)
    n_skills = features.get('n_skills', 0)
    
    # Compute missing engineered features
    if 'grade_normalized_squared' not in features or features.get('grade_normalized_squared') is None:
        features['grade_normalized_squared'] = grade ** 2
    
    if 'grade_normalized_cubed' not in features or features.get('grade_normalized_cubed') is None:
        features['grade_normalized_cubed'] = grade ** 3
    
    if 'avg_skill_score_squared' not in features or features.get('avg_skill_score_squared') is None:
        features['avg_skill_score_squared'] = skill ** 2
    
    if 'avg_skill_score_cubed' not in features or features.get('avg_skill_score_cubed') is None:
        features['avg_skill_score_cubed'] = skill ** 3
    
    if 'avg_course_difficulty_squared' not in features or features.get('avg_course_difficulty_squared') is None:
        features['avg_course_difficulty_squared'] = difficulty ** 2
    
    if 'skill_diversity_squared' not in features or features.get('skill_diversity_squared') is None:
        features['skill_diversity_squared'] = diversity ** 2
    
    if 'domain_alignment_squared' not in features or features.get('domain_alignment_squared') is None:
        features['domain_alignment_squared'] = domain ** 2
    
    # Interaction terms
    if 'grade_normalized_x_avg_course_difficulty' not in features or features.get('grade_normalized_x_avg_course_difficulty') is None:
        features['grade_normalized_x_avg_course_difficulty'] = grade * difficulty
    
    if 'grade_normalized_x_skill_diversity' not in features or features.get('grade_normalized_x_skill_diversity') is None:
        features['grade_normalized_x_skill_diversity'] = grade * diversity
    
    if 'grade_normalized_x_domain_alignment' not in features or features.get('grade_normalized_x_domain_alignment') is None:
        features['grade_normalized_x_domain_alignment'] = grade * domain
    
    if 'avg_skill_score_x_skill_diversity' not in features or features.get('avg_skill_score_x_skill_diversity') is None:
        features['avg_skill_score_x_skill_diversity'] = skill * diversity
    
    if 'avg_skill_score_x_domain_alignment' not in features or features.get('avg_skill_score_x_domain_alignment') is None:
        features['avg_skill_score_x_domain_alignment'] = skill * domain
    
    if 'skill_diversity_x_domain_alignment' not in features or features.get('skill_diversity_x_domain_alignment') is None:
        features['skill_diversity_x_domain_alignment'] = diversity * domain
    
    if 'skill_diversity_x_n_skills' not in features or features.get('skill_diversity_x_n_skills') is None:
        features['skill_diversity_x_n_skills'] = diversity * n_skills
    
    # Ratio features
    if 'grade_normalized_to_avg_course_difficulty' not in features or features.get('grade_normalized_to_avg_course_difficulty') is None:
        features['grade_normalized_to_avg_course_difficulty'] = grade / (difficulty + 1e-6)
    
    if 'avg_skill_score_to_skill_diversity' not in features or features.get('avg_skill_score_to_skill_diversity') is None:
        features['avg_skill_score_to_skill_diversity'] = skill / (diversity + 1e-6)
    
    if 'domain_alignment_to_avg_course_difficulty' not in features or features.get('domain_alignment_to_avg_course_difficulty') is None:
        features['domain_alignment_to_avg_course_difficulty'] = domain / (difficulty + 1e-6)
    
    if 'difficulty_inverse' not in features or features.get('difficulty_inverse') is None:
        features['difficulty_inverse'] = 1.0 - difficulty
    
    # Composite scores
    if 'academic_strength' not in features or features.get('academic_strength') is None:
        features['academic_strength'] = 0.6 * grade + 0.2 * skill + 0.2 * domain
    
    if 'skill_readiness' not in features or features.get('skill_readiness') is None:
        features['skill_readiness'] = 0.5 * skill + 0.3 * diversity + 0.2 * domain
    
    if 'comprehensive_readiness' not in features or features.get('comprehensive_readiness') is None:
        skill_readiness = 0.5 * skill + 0.3 * diversity + 0.2 * domain
        features['comprehensive_readiness'] = (
            0.35 * grade + 0.30 * skill + 0.15 * diversity + 
            0.10 * domain + 0.10 * skill_readiness
        )
    
    if 'difficulty_adjusted_score' not in features or features.get('difficulty_adjusted_score') is None:
        features['difficulty_adjusted_score'] = grade * (1 - 0.2 * difficulty)
    
    # Percentile features (assume uniform)
    if 'grade_normalized_percentile' not in features or features.get('grade_normalized_percentile') is None:
        features['grade_normalized_percentile'] = grade
    
    if 'avg_skill_score_percentile' not in features or features.get('avg_skill_score_percentile') is None:
        features['avg_skill_score_percentile'] = skill
    
    if 'skill_diversity_percentile' not in features or features.get('skill_diversity_percentile') is None:
        features['skill_diversity_percentile'] = diversity
    
    if 'domain_alignment_percentile' not in features or features.get('domain_alignment_percentile') is None:
        features['domain_alignment_percentile'] = domain
    
    # Z-score features (assume standardized)
    if 'grade_normalized_zscore' not in features or features.get('grade_normalized_zscore') is None:
        features['grade_normalized_zscore'] = grade
    
    if 'avg_skill_score_zscore' not in features or features.get('avg_skill_score_zscore') is None:
        features['avg_skill_score_zscore'] = skill
    
    if 'skill_diversity_zscore' not in features or features.get('skill_diversity_zscore') is None:
        features['skill_diversity_zscore'] = diversity
    
    if 'domain_alignment_zscore' not in features or features.get('domain_alignment_zscore') is None:
        features['domain_alignment_zscore'] = domain
    
    # Threshold features
    if 'high_grade' not in features or features.get('high_grade') is None:
        features['high_grade'] = int(grade > 0.85)
    
    if 'high_skill' not in features or features.get('high_skill') is None:
        features['high_skill'] = int(skill > 0.85)
    
    if 'high_diversity' not in features or features.get('high_diversity') is None:
        features['high_diversity'] = int(diversity > 0.70)
    
    if 'good_domain_fit' not in features or features.get('good_domain_fit') is None:
        features['good_domain_fit'] = int(domain > 0.90)
    
    if 'well_rounded' not in features or features.get('well_rounded') is None:
        features['well_rounded'] = int((grade > 0.80) and (diversity > 0.65))
    
    # Other missing features
    if 'skill_std' not in features or features.get('skill_std') is None:
        features['skill_std'] = 0.016  # Default from synthetic data
    
    if 'grade_quality' not in features or features.get('grade_quality') is None:
        features['grade_quality'] = grade
    
    if 'disability_code' not in features or features.get('disability_code') is None:
        features['disability_code'] = 0.0
    
    return features
