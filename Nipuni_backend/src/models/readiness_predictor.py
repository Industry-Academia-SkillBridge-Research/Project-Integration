"""
Model Predictor Service
Wraps trained XGBoost and Bayesian Ridge models for inference
Handles prediction, uncertainty quantification, and batch processing
"""

import pandas as pd
import numpy as np
import joblib
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

class SkillReadinessPredictor:
    def __init__(self, 
                 xgb_model_path='data/models/xgboost_readiness.pkl',
                 xgb_features_path='data/models/xgboost_readiness_features.pkl',
                 br_model_path='data/models/bayesian_ridge_uncertainty.pkl',
                 br_scaler_path='data/models/bayesian_ridge_uncertainty_scaler.pkl'):
        """Load trained models and preprocessing objects"""
        
        # Load XGBoost model
        self.xgb_model = joblib.load(xgb_model_path)
        self.xgb_features = joblib.load(xgb_features_path)
        
        # Load Bayesian Ridge model
        self.br_model = joblib.load(br_model_path)
        self.br_scaler = joblib.load(br_scaler_path)
        
        self.label_names = {0: 'Ready', 1: 'Nearly Ready', 2: 'Significant Gaps'}
        
        print(f"✓ Loaded XGBoost model with {len(self.xgb_features)} features")
        print(f"✓ Loaded Bayesian Ridge model with scaler")
    
    def predict_single(self, features: Dict[str, float], 
                      include_uncertainty: bool = True) -> Dict:
        """
        Predict readiness for a single student
        
        Args:
            features: Dictionary with feature names and values
            include_uncertainty: Whether to include Bayesian uncertainty estimates
            
        Returns:
            Dictionary with predictions, confidence, and uncertainty
        """
        
        # Convert to DataFrame
        X = pd.DataFrame([features])
        
        # Ensure all required features are present
        missing = set(self.xgb_features) - set(X.columns)
        if missing:
            raise ValueError(f"Missing features: {missing}")
        
        # Reorder columns
        X = X[self.xgb_features]
        
        # XGBoost prediction
        y_pred = self.xgb_model.predict(X)[0]
        y_pred_proba = self.xgb_model.predict_proba(X)[0]
        
        result = {
            'prediction': int(y_pred),
            'prediction_label': self.label_names[y_pred],
            'confidence': float(y_pred_proba[y_pred]),
            'class_probabilities': {
                self.label_names[i]: float(prob) 
                for i, prob in enumerate(y_pred_proba)
            }
        }
        
        # Bayesian Ridge uncertainty
        if include_uncertainty:
            X_scaled = self.br_scaler.transform(X)
            y_br_mean, y_br_std = self.br_model.predict(X_scaled, return_std=True)
            
            result['uncertainty'] = {
                'predicted_score': float(y_br_mean[0]),
                'std_dev': float(y_br_std[0]),
                'ci_lower': float(np.clip(y_br_mean[0] - 1.96 * y_br_std[0], 0, 1)),
                'ci_upper': float(np.clip(y_br_mean[0] + 1.96 * y_br_std[0], 0, 1))
            }
        
        return result
    
    def predict_batch(self, features_list: List[Dict[str, float]], 
                     include_uncertainty: bool = True) -> List[Dict]:
        """
        Predict readiness for multiple students
        
        Args:
            features_list: List of feature dictionaries
            include_uncertainty: Whether to include uncertainty estimates
            
        Returns:
            List of prediction dictionaries
        """
        
        results = []
        for features in features_list:
            result = self.predict_single(features, include_uncertainty)
            results.append(result)
        
        return results
    
    def predict_dataframe(self, df: pd.DataFrame, 
                         include_uncertainty: bool = True) -> pd.DataFrame:
        """
        Predict readiness for DataFrame of students
        
        Args:
            df: DataFrame with feature columns
            include_uncertainty: Whether to include uncertainty estimates
            
        Returns:
            DataFrame with predictions and uncertainty
        """
        
        # Ensure all required features present
        missing = set(self.xgb_features) - set(df.columns)
        if missing:
            raise ValueError(f"Missing features: {missing}")
        
        # Prepare features
        X = df[self.xgb_features]
        
        # XGBoost predictions
        y_pred = self.xgb_model.predict(X)
        y_pred_proba = self.xgb_model.predict_proba(X)
        
        # Create results DataFrame
        results_df = pd.DataFrame({
            'prediction': y_pred,
            'prediction_label': [self.label_names[p] for p in y_pred],
            'confidence': np.max(y_pred_proba, axis=1)
        })
        
        # Add class probabilities
        for i, label in enumerate(self.label_names.values()):
            results_df[f'prob_{label}'] = y_pred_proba[:, i]
        
        # Bayesian Ridge uncertainty
        if include_uncertainty:
            X_scaled = self.br_scaler.transform(X)
            y_br_mean, y_br_std = self.br_model.predict(X_scaled, return_std=True)
            
            results_df['uncertainty_score'] = y_br_mean
            results_df['uncertainty_std'] = y_br_std
            results_df['ci_lower'] = np.clip(y_br_mean - 1.96 * y_br_std, 0, 1)
            results_df['ci_upper'] = np.clip(y_br_mean + 1.96 * y_br_std, 0, 1)
        
        return results_df
    
    def get_feature_names(self) -> List[str]:
        """Get list of required feature names"""
        return self.xgb_features
    
    def get_label_names(self) -> Dict[int, str]:
        """Get label name mapping"""
        return self.label_names
