"""
Test Script for Skill Readiness Prediction API
Demonstrates how to use the prediction endpoints
"""

import requests
import json
from typing import Dict, List

# Configuration
BASE_URL = "http://localhost:8000/api/readiness"
TIMEOUT = 10

class ReadinessAPIClient:
    """Client for Skill Readiness Prediction API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def health_check(self) -> Dict:
        """Check if API is healthy"""
        response = requests.get(f"{self.base_url}/health", timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    
    def get_features(self) -> Dict:
        """Get list of required features"""
        response = requests.get(f"{self.base_url}/features", timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    
    def predict_single(self, features: Dict, include_uncertainty: bool = True) -> Dict:
        """Predict readiness for single student"""
        params = {"include_uncertainty": include_uncertainty}
        response = requests.post(
            f"{self.base_url}/predict",
            json=features,
            params=params,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    
    def predict_batch(self, students: List[Dict], include_uncertainty: bool = True) -> Dict:
        """Predict readiness for multiple students"""
        data = {
            "students": students,
            "include_uncertainty": include_uncertainty
        }
        response = requests.post(
            f"{self.base_url}/predict-batch",
            json=data,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()


def test_health_check():
    """Test health check endpoint"""
    print("\n" + "="*80)
    print("TEST 1: Health Check")
    print("="*80)
    
    client = ReadinessAPIClient()
    health = client.health_check()
    
    print(f"Status: {health['status']}")
    print(f"XGBoost Model: {'✓ Loaded' if health['xgb_model_loaded'] else '✗ Not loaded'}")
    print(f"Bayesian Ridge Model: {'✓ Loaded' if health['br_model_loaded'] else '✗ Not loaded'}")
    print(f"Features Count: {health['features_count']}")


def test_get_features():
    """Test get features endpoint"""
    print("\n" + "="*80)
    print("TEST 2: Get Features")
    print("="*80)
    
    client = ReadinessAPIClient()
    features_info = client.get_features()
    
    print(f"Total Features: {features_info['count']}")
    print(f"\nReadiness Classes:")
    for class_id, label in features_info['labels'].items():
        print(f"  {class_id}: {label}")
    
    print(f"\nFirst 10 Required Features:")
    for feat in features_info['features'][:10]:
        print(f"  - {feat}")
    
    print(f"\nLast 10 Features:")
    for feat in features_info['features'][-10:]:
        print(f"  - {feat}")


def test_single_prediction():
    """Test single prediction endpoint"""
    print("\n" + "="*80)
    print("TEST 3: Single Student Prediction")
    print("="*80)
    
    # Example 1: High-performing student (likely Ready)
    student_ready = {
        "cohort": 3,
        "grade_normalized": 0.88,
        "grade_quality": 0.89,
        "avg_course_difficulty": 0.52,
        "domain_alignment": 0.95,
        "avg_skill_score": 0.90,
        "skill_diversity": 0.75,
        "n_skills": 0.73,
        "gender_code": 1.0,
        "ses_code": 0.5
    }
    
    # Example 2: Medium-performing student (likely Nearly Ready)
    student_nearly_ready = {
        "cohort": 2,
        "grade_normalized": 0.72,
        "grade_quality": 0.74,
        "avg_course_difficulty": 0.55,
        "domain_alignment": 0.80,
        "avg_skill_score": 0.70,
        "skill_diversity": 0.65,
        "n_skills": 0.62,
        "gender_code": 0.0,
        "ses_code": 0.0
    }
    
    client = ReadinessAPIClient()
    
    print("\nPrediction 1: High-performing student")
    pred1 = client.predict_single(student_ready)
    print(f"  Prediction: {pred1['prediction_label']}")
    print(f"  Confidence: {pred1['confidence']:.4f}")
    print(f"  Class Probabilities:")
    for class_name, prob in pred1['class_probabilities'].items():
        print(f"    - {class_name}: {prob:.4f}")
    
    if pred1.get('uncertainty'):
        print(f"  Uncertainty Estimate:")
        print(f"    - Score: {pred1['uncertainty']['predicted_score']:.4f}")
        print(f"    - Std Dev: {pred1['uncertainty']['std_dev']:.4f}")
        print(f"    - 95% CI: [{pred1['uncertainty']['ci_lower']:.4f}, {pred1['uncertainty']['ci_upper']:.4f}]")
    
    print("\nPrediction 2: Medium-performing student")
    pred2 = client.predict_single(student_nearly_ready)
    print(f"  Prediction: {pred2['prediction_label']}")
    print(f"  Confidence: {pred2['confidence']:.4f}")
    print(f"  Class Probabilities:")
    for class_name, prob in pred2['class_probabilities'].items():
        print(f"    - {class_name}: {prob:.4f}")


def test_batch_prediction():
    """Test batch prediction endpoint"""
    print("\n" + "="*80)
    print("TEST 4: Batch Prediction (5 students)")
    print("="*80)
    
    students = [
        {
            "cohort": 3,
            "grade_normalized": 0.88,
            "grade_quality": 0.89,
            "avg_course_difficulty": 0.52,
            "domain_alignment": 0.95,
            "avg_skill_score": 0.90,
            "skill_diversity": 0.75,
            "n_skills": 0.73,
            "gender_code": 1.0,
            "ses_code": 0.5
        },
        {
            "cohort": 2,
            "grade_normalized": 0.72,
            "grade_quality": 0.74,
            "avg_course_difficulty": 0.55,
            "domain_alignment": 0.80,
            "avg_skill_score": 0.70,
            "skill_diversity": 0.65,
            "n_skills": 0.62,
            "gender_code": 0.0,
            "ses_code": 0.0
        },
        {
            "cohort": 4,
            "grade_normalized": 0.82,
            "grade_quality": 0.84,
            "avg_course_difficulty": 0.50,
            "domain_alignment": 0.92,
            "avg_skill_score": 0.85,
            "skill_diversity": 0.71,
            "n_skills": 0.70,
            "gender_code": 0.5,
            "ses_code": 1.0
        },
        {
            "cohort": 1,
            "grade_normalized": 0.65,
            "grade_quality": 0.68,
            "avg_course_difficulty": 0.58,
            "domain_alignment": 0.70,
            "avg_skill_score": 0.60,
            "skill_diversity": 0.55,
            "n_skills": 0.50,
            "gender_code": 1.0,
            "ses_code": 0.0
        },
        {
            "cohort": 5,
            "grade_normalized": 0.75,
            "grade_quality": 0.77,
            "avg_course_difficulty": 0.54,
            "domain_alignment": 0.88,
            "avg_skill_score": 0.78,
            "skill_diversity": 0.68,
            "n_skills": 0.67,
            "gender_code": 0.0,
            "ses_code": 0.5
        }
    ]
    
    client = ReadinessAPIClient()
    batch_result = client.predict_batch(students)
    
    print(f"\nBatch Results:")
    print(f"  Total Students: {batch_result['total']}")
    print(f"  Ready: {batch_result['ready_count']}")
    print(f"  Nearly Ready: {batch_result['nearly_ready_count']}")
    print(f"  Significant Gaps: {batch_result['gaps_count']}")
    
    print(f"\nDetailed Predictions:")
    for i, pred in enumerate(batch_result['predictions'], 1):
        print(f"\n  Student {i}:")
        print(f"    Label: {pred['prediction_label']}")
        print(f"    Confidence: {pred['confidence']:.4f}")
        print(f"    Top probability: {max(pred['class_probabilities'].values()):.4f}")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*80)
    print("TEST 5: Edge Cases")
    print("="*80)
    
    client = ReadinessAPIClient()
    
    # Test 1: Perfect student
    print("\nEdge Case 1: Perfect student (all 1.0)")
    perfect_student = {
        "cohort": 3,
        "grade_normalized": 1.0,
        "grade_quality": 1.0,
        "avg_course_difficulty": 0.5,
        "domain_alignment": 1.0,
        "avg_skill_score": 1.0,
        "skill_diversity": 1.0,
        "n_skills": 1.0,
        "gender_code": 1.0,
        "ses_code": 1.0
    }
    pred = client.predict_single(perfect_student)
    print(f"  Prediction: {pred['prediction_label']}")
    print(f"  Confidence: {pred['confidence']:.4f}")
    
    # Test 2: Struggling student
    print("\nEdge Case 2: Struggling student (low scores)")
    struggling_student = {
        "cohort": 1,
        "grade_normalized": 0.50,
        "grade_quality": 0.50,
        "avg_course_difficulty": 0.80,
        "domain_alignment": 0.40,
        "avg_skill_score": 0.40,
        "skill_diversity": 0.30,
        "n_skills": 0.25,
        "gender_code": 0.0,
        "ses_code": 0.0
    }
    pred = client.predict_single(struggling_student)
    print(f"  Prediction: {pred['prediction_label']}")
    print(f"  Confidence: {pred['confidence']:.4f}")
    
    # Test 3: Without uncertainty
    print("\nEdge Case 3: Prediction without uncertainty")
    pred = client.predict_single(perfect_student, include_uncertainty=False)
    print(f"  Has uncertainty: {'uncertainty' in pred}")
    print(f"  Prediction: {pred['prediction_label']}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SKILL READINESS PREDICTION API - TEST SUITE")
    print("="*80)
    
    try:
        # Run tests
        test_health_check()
        test_get_features()
        test_single_prediction()
        test_batch_prediction()
        test_edge_cases()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80)
        print("\nAPI is ready for integration!")
        print("Documentation: API_READINESS_PREDICTION.md")
        
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Connection Error: Cannot reach {BASE_URL}")
        print("Make sure the API server is running:")
        print("  cd Nipuni_backend")
        print("  uvicorn src.app.main:app --reload")
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Request Error: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
