"""
GNN-Based Skill Gap Ranking Service.

Combines GNN predictions (P_gnn), skill confidence (P_has), and role importance
to rank missing skills using the RESEARCH-VALIDATED formula (Variant B_default):
    
    final_score = 0.3 × (1-P_has_norm) + 0.4 × importance_norm + 0.3 × P_gnn_norm
    
Where all components are normalized to [0,1] to prevent importance domination.
This additive approach achieved 19% Hits@10 vs 0% for multiplicative formula.
"""
import logging
from typing import Dict, List, Tuple
from collections import defaultdict
import numpy as np
from services.gnn_inference_service import gnn_service
from services.skill_confidence_service import SkillConfidenceService
from services.role_importance_service import RoleImportanceService
from services.category_service import CategoryService

logger = logging.getLogger(__name__)


class GNNRankingService:
    """
    Service for ranking missing skills using GNN predictions.
    """
    
    @staticmethod
    def rank_missing_skills_for_role(
        session,
        candidate_id: str,
        role_key: str,
        top_k: int = 20,
        p_has_threshold: float = 0.6
    ) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Rank missing skills for a candidate-role pair using GNN predictions.
        
        Algorithm:
        1. Get P_gnn for all skills from GNN
        2. Get role required skills with importance scores
        3. Get candidate skill confidence (P_has)
        4. Filter to missing skills (P_has < threshold)
        5. Normalize P_has, importance, P_gnn to [0,1]
        6. Compute final_score = 0.3×(1-P_has_norm) + 0.4×importance_norm + 0.3×P_gnn_norm
        7. Rank by final_score and return top_k
        8. Aggregate by category for XAI
        
        Args:
            session: Neo4j session
            candidate_id: Candidate identifier
            role_key: Role identifier
            top_k: Number of top skills to return (default: 20)
            p_has_threshold: Threshold for considering skill as "missing" (default: 0.6)
            
        Returns:
            Tuple of (ranked_skills, category_summary, metadata):
            - ranked_skills: List of dicts with skill, scores, and reasons
            - category_summary: List of dicts with category-level gap scores
            - metadata: Dict with computation statistics
        """
        logger.info(f"Ranking missing skills for candidate={candidate_id}, role={role_key}")
        
        # Check if GNN service is ready
        if not gnn_service.is_ready():
            raise RuntimeError("GNN model not loaded. Service not ready.")
        
        # Step 1: Get P_gnn for all skills from GNN
        # NOTE: predict_skill_probs uses fallback for new candidates (use_fallback=True by default)
        gnn_probs = gnn_service.predict_skill_probs(candidate_id, use_fallback=True)
        logger.info(f"GNN predicted probabilities for {len(gnn_probs)} skills")
        
        # Step 2: Get role required skills with importance scores
        role_importance_dict, total_jobs, role_name = RoleImportanceService.compute_role_importance(
            session, role_key
        )
        
        if not role_importance_dict:
            logger.warning(f"No skills found for role {role_key}")
            return [], [], {"warning": "Role has no required skills"}
        
        logger.info(f"Role '{role_name}' has {len(role_importance_dict)} required skills")
        
        # Step 3: Get candidate skill confidence (P_has)
        candidate_confidence = SkillConfidenceService.compute_confidence(session, candidate_id)
        logger.info(f"Candidate has confidence scores for {len(candidate_confidence)} skills")
        
        # Step 4: Filter to missing skills and collect raw values
        candidate_skills = []
        
        for skill_name, importance_data in role_importance_dict.items():
            # Get P_has (default to 0 if not in candidate profile)
            p_has = candidate_confidence.get(skill_name, {}).get('confidence', 0.0)
            
            # Filter: Only consider "missing" skills
            if p_has >= p_has_threshold:
                continue
            
            # Get P_gnn (default to 0 if not predicted)
            p_gnn = gnn_probs.get(skill_name, 0.0)
            
            # Get importance score (normalized 0-1)
            importance = importance_data.get('importance', 0.0)
            
            candidate_skills.append({
                'skill_name': skill_name,
                'p_has': p_has,
                'importance': importance,
                'p_gnn': p_gnn
            })
        
        # Step 5: Normalize all components to [0,1]
        if not candidate_skills:
            logger.warning(f"No missing skills found for candidate {candidate_id} in role {role_key}")
            return [], [], {"warning": "No missing skills"}
        
        p_has_values = np.array([s['p_has'] for s in candidate_skills])
        importance_values = np.array([s['importance'] for s in candidate_skills])
        p_gnn_values = np.array([s['p_gnn'] for s in candidate_skills])
        
        # Min-max normalization to [0,1]
        def normalize(values):
            if len(values) == 1:
                return np.array([0.5])  # Single value -> middle of range
            min_val, max_val = values.min(), values.max()
            if max_val - min_val < 1e-9:
                return np.ones_like(values) * 0.5  # All equal -> middle
            return (values - min_val) / (max_val - min_val)
        
        p_has_norm = normalize(p_has_values)
        importance_norm = normalize(importance_values)
        p_gnn_norm = normalize(p_gnn_values)
        
        # Step 6: Compute final scores using B_default formula
        # final_score = 0.3×(1-P_has_norm) + 0.4×importance_norm + 0.3×P_gnn_norm
        scored_skills = []
        
        for i, skill_data in enumerate(candidate_skills):
            gap_magnitude = 1.0 - skill_data['p_has']
            
            # B_default formula (research-validated)
            final_score = (
                0.3 * (1.0 - p_has_norm[i]) +  # Reward missing skills
                0.4 * importance_norm[i] +       # Weight by role importance
                0.3 * p_gnn_norm[i]              # Consider GNN learning potential
            )
            
            skill_name = skill_data['skill_name']
            p_has = skill_data['p_has']
            importance = skill_data['importance']
            p_gnn = skill_data['p_gnn']
            
            # Get skill category
            category = CategoryService.get_skill_category(session, skill_name)
            
            # Generate reason based on scores
            reason = GNNRankingService._generate_reason(
                p_has, p_gnn, importance, gap_magnitude
            )
            
            scored_skills.append({
                'skill': skill_name,
                'category': category or 'Uncategorized',
                'final_score': round(final_score, 4),
                'P_gnn': round(p_gnn, 4),
                'P_has': round(p_has, 4),
                'importance': round(importance, 4),
                'gap_magnitude': round(gap_magnitude, 4),
                'reason': reason
            })
        
        # Step 7: Sort by final_score descending
        scored_skills.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Step 8: Take top_k
        top_skills = scored_skills[:top_k]
        logger.info(f"Returning top {len(top_skills)} missing skills (scored with B_default formula)")
        
        # Step 9: Aggregate by category
        category_summary = GNNRankingService._aggregate_by_category(top_skills)
        
        # Metadata
        metadata = {
            'candidate_id': candidate_id,
            'role_key': role_key,
            'role_name': role_name,
            'total_required_skills': len(role_importance_dict),
            'total_missing_skills': len(scored_skills),
            'returned_skills': len(top_skills),
            'p_has_threshold': p_has_threshold,
            'scoring_formula': 'B_default: 0.3×(1-P_has_norm) + 0.4×importance_norm + 0.3×P_gnn_norm'
        }
        
        return top_skills, category_summary, metadata
    
    @staticmethod
    def _generate_reason(p_has: float, p_gnn: float, importance: float, gap_magnitude: float) -> str:
        """
        Generate human-readable reason for skill ranking with PRECISE numeric details.
        
        Args:
            p_has: Current skill confidence (0-1)
            p_gnn: GNN predicted probability (0-1)
            importance: Role importance score (0-1)
            gap_magnitude: 1 - P_has
            
        Returns:
            Detailed reason string with percentages and qualitative assessment
        """
        parts = []
        
        # Part 1: Gap Analysis (with exact percentage)
        gap_pct = gap_magnitude * 100
        if p_has == 0:
            parts.append(f"Completely missing ({gap_pct:.0f}% gap)")
        elif gap_magnitude > 0.7:
            parts.append(f"Major gap ({gap_pct:.0f}% missing, {p_has*100:.0f}% proficiency)")
        elif gap_magnitude > 0.4:
            parts.append(f"Moderate gap ({gap_pct:.0f}% missing, {p_has*100:.0f}% proficiency)")
        else:
            parts.append(f"Small gap ({gap_pct:.0f}% missing, {p_has*100:.0f}% proficiency)")
        
        # Part 2: Role Importance (with percentage and context)
        if importance > 0.9:
            parts.append(f"CRITICAL for role ({importance*100:.1f}% importance - top-tier skill)")
        elif importance > 0.7:
            parts.append(f"highly important ({importance*100:.1f}% - core requirement)")
        elif importance > 0.5:
            parts.append(f"important ({importance*100:.1f}% - standard requirement)")
        elif importance > 0.3:
            parts.append(f"moderately important ({importance*100:.1f}% - nice to have)")
        else:
            parts.append(f"useful ({importance*100:.1f}% - supplementary skill)")
        
        # Part 3: GNN Learning Potential (with percentage and confidence level)
        if p_gnn > 0.85:
            parts.append(f"STRONG learning potential ({p_gnn*100:.1f}% - very high confidence)")
        elif p_gnn > 0.75:
            parts.append(f"high learning potential ({p_gnn*100:.1f}% - strong match)")
        elif p_gnn > 0.65:
            parts.append(f"good learning potential ({p_gnn*100:.1f}% - solid fit)")
        elif p_gnn > 0.50:
            parts.append(f"moderate learning potential ({p_gnn*100:.1f}% - achievable)")
        else:
            parts.append(f"challenging to acquire ({p_gnn*100:.1f}% - may require prerequisites)")
        
        return " | ".join(parts)
    
    @staticmethod
    def _aggregate_by_category(ranked_skills: List[Dict]) -> List[Dict]:
        """
        Aggregate ranked skills by category for XAI.
        
        Args:
            ranked_skills: List of ranked skill dicts
            
        Returns:
            List of category summaries sorted by gap_score descending
        """
        category_data = defaultdict(lambda: {'gap_score': 0.0, 'count': 0, 'skills': []})
        
        for skill_data in ranked_skills:
            category = skill_data['category']
            category_data[category]['gap_score'] += skill_data['final_score']
            category_data[category]['count'] += 1
            category_data[category]['skills'].append(skill_data['skill'])
        
        # Convert to list and sort by gap_score
        category_summary = [
            {
                'category': category,
                'gap_score': round(data['gap_score'], 4),
                'missing_skills_count': data['count'],
                'top_skills': data['skills'][:3]  # Include top 3 skills per category
            }
            for category, data in category_data.items()
        ]
        
        category_summary.sort(key=lambda x: x['gap_score'], reverse=True)
        
        return category_summary
