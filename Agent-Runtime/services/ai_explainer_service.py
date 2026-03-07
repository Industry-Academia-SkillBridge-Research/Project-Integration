"""
AI Explainer Service

Loads fine-tuned Qwen model (LoRA adapter) for generating skill gap explanations.
Replaces external Colab/ngrok dependency with local inference.

Model: Qwen2.5-3B-Instruct with fine-tuned LoRA adapter
Location: Agent-Runtime/ai_explanation/qwen-explainer-output
"""
import logging
import os
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Lazy imports for PyTorch (deferred until model loading)
# This allows the service to be imported even if PyTorch DLLs fail to load
torch = None
AutoModelForCausalLM = None
AutoTokenizer = None
PeftModel = None

def _import_pytorch():
    """Import PyTorch dependencies lazily."""
    global torch, AutoModelForCausalLM, AutoTokenizer, PeftModel
    if torch is None:
        # Disable vision modules in transformers to avoid torchvision conflicts
        os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        import torch as _torch
        from transformers import AutoModelForCausalLM as _AutoModelForCausalLM
        from transformers import AutoTokenizer as _AutoTokenizer
        from peft import PeftModel as _PeftModel
        
        torch = _torch
        AutoModelForCausalLM = _AutoModelForCausalLM
        AutoTokenizer = _AutoTokenizer
        PeftModel = _PeftModel


class AIExplainerService:
    """
    Service for generating AI-powered skill gap explanations using fine-tuned Qwen model.
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize the explainer service.
        
        Args:
            model_path: Path to fine-tuned LoRA adapter directory
        """
        if model_path is None:
            # Default to the fine-tuned model in AI Explanation folder
            import os
            from pathlib import Path
            base_path = Path(__file__).parent.parent / "AI Explanation" / "qwen-explainer-output"
            model_path = str(base_path.resolve())
        
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.device = None  # Will be set in _load_model after importing torch
        self.model_load_attempted = False
        self.model_load_error = None
        
        logger.info(f"Initializing AI Explainer Service (model will load on first use)")
        # Don't load model immediately - load on first use
        # This prevents blocking the server startup
    
    def _ensure_model_loaded(self):
        """Ensure model is loaded before use."""
        if not self.model_load_attempted:
            self.model_load_attempted = True
            try:
                self._load_model()
            except Exception as e:
                self.model_load_error = str(e)
                logger.warning(f"❌ Model loading failed, will use fallback: {e}")
    
    def _load_model(self):
        """Load the fine-tuned model and tokenizer."""
        try:
            logger.info("Loading AI model (this may take a minute on first run)...")
            # Import PyTorch dependencies (lazy loading)
            try:
                _import_pytorch()
            except ImportError as pytorch_err:
                error_msg = (
                    "PyTorch is not properly installed or DLL loading failed. "
                    "On Windows, this typically requires Visual C++ Redistributables. "
                    "Install from: https://aka.ms/vs/17/release/vc_redist.x64.exe"
                )
                logger.error(f"❌ PyTorch import failed: {pytorch_err}")
                logger.error(f"💡 Solution: {error_msg}")
                raise ImportError(error_msg) from pytorch_err
            
            # Set device after importing torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Device: {self.device}")
            logger.info(f"Loading base model and LoRA adapter from {self.model_path}")
            
            # Read adapter config to get base model
            import json
            config_path = os.path.join(self.model_path, "adapter_config.json")
            with open(config_path, 'r') as f:
                adapter_config = json.load(f)
            
            base_model_name = adapter_config.get("base_model_name_or_path", "Qwen/Qwen2.5-3B-Instruct")
            logger.info(f"Base model: {base_model_name}")
            
            # Check if base model is cached locally (avoid downloading 3GB+ model)
            from transformers import AutoConfig
            try:
                # This will only work if model is already cached
                config = AutoConfig.from_pretrained(base_model_name, local_files_only=True)
                logger.info("Base model found in cache")
            except Exception:
                logger.warning(
                    f"⚠️  Base model '{base_model_name}' not found in local cache. "
                    "Skipping AI model loading to avoid long download (3GB+). "
                    "Using fast fallback explanations instead. "
                    "To enable AI model: run 'huggingface-cli download Qwen/Qwen2.5-3B-Instruct' first."
                )
                raise FileNotFoundError("Base model not cached locally")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            
            # Load base model
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                trust_remote_code=True,
                local_files_only=True  # Don't download if not cached
            )
            
            # Load LoRA adapter
            self.model = PeftModel.from_pretrained(
                base_model,
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            # Set to evaluation mode
            self.model.eval()
            
            logger.info("✅ Model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise
    
    def _normalize_value(self, value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """
        Normalize a value to 0-1 range, handling values that may be outside this range.
        
        Args:
            value: Value to normalize
            min_val: Minimum expected value
            max_val: Maximum expected value
        
        Returns:
            Normalized value between 0 and 1
        """
        # Clamp to expected range
        if value < min_val:
            return 0.0
        if value > max_val:
            return 1.0
        
        # Already in range
        if min_val == 0.0 and max_val == 1.0:
            return value
        
        # Normalize to 0-1
        return (value - min_val) / (max_val - min_val)
    
    def _format_prompt(self, input_data: Dict[str, Any]) -> str:
        """
        Format the input data into a prompt for the model.
        
        Args:
            input_data: Dictionary containing gap analysis data
        
        Returns:
            Formatted prompt string
        """
        target_name = input_data.get("target_name", "Unknown")
        target_type = "role" if input_data.get("mode") == "role_gap" else "job"
        
        # Normalize readiness and skill_gap_index to 0-1 range
        readiness = self._normalize_value(input_data.get("readiness", 0))
        skill_gap_index = self._normalize_value(input_data.get("skill_gap_index", 0))
        
        matched_skills = input_data.get("matched_skills", [])
        num_matched = input_data.get("num_matched", len(matched_skills))
        
        missing_skills = input_data.get("missing_skills", [])
        num_missing = input_data.get("num_missing", len(missing_skills))
        
        total_skills = input_data.get("total_role_skills", num_matched + num_missing)
        
        # Normalize project_relevance to 0-1 range
        project_relevance = self._normalize_value(input_data.get("project_relevance_score", 0))
        relevant_projects = input_data.get("relevant_projects", [])
        total_projects = input_data.get("total_projects", len(relevant_projects))
        
        # Format missing skills with importance (normalize if needed)
        missing_skills_str = "\n".join([
            f"  - {skill['skill']} (importance: {self._normalize_value(skill.get('importance', 0.5)):.2f}, deficit: {self._normalize_value(skill.get('deficit', 1.0)):.2f})"
            for skill in missing_skills[:10]  # Limit to top 10
        ])
        
        # Format relevant projects (normalize relevance if needed)
        projects_str = "\n".join([
            f"  - {proj['name']} (relevance: {self._normalize_value(proj.get('relevance', 0)):.2f}, matched: {len(proj.get('matched_skills', []))}/{proj.get('total_skills', 0)})"
            for proj in relevant_projects[:5]  # Limit to top 5
        ])
        
        # Create concise, focused prompt for faster generation
        if readiness >= 0.7:
            tone = "strong position but can improve"
        elif readiness >= 0.5:
            tone = "decent foundation with gaps to fill"
        else:
            tone = "significant development needed"
        
        # Get top skills concisely
        top_matched = ', '.join(matched_skills[:5]) if matched_skills else "None"
        top_missing_names = ', '.join([s['skill'] for s in missing_skills[:5]]) if missing_skills else "None"
        
        prompt = f"""You are {readiness:.0%} ready for {target_name}. You have {num_matched} matching skills but need {num_missing} more.

Strengths: {top_matched}
Key Gaps: {top_missing_names}
Projects: {len(relevant_projects)} relevant ({project_relevance:.0%} relevance)

Provide a brief, actionable 3-part explanation:
1. Overall status ({tone})
2. Top 2-3 critical skills to learn
3. One specific next step

Keep response under 100 words, professional and encouraging."""

        return prompt
    
    def generate_explanation(
        self,
        input_data: Dict[str, Any],
        max_length: int = 150,
        temperature: float = 0.6,
        top_p: float = 0.85
    ) -> Dict[str, Any]:
        """
        Generate explanation for skill gap analysis.
        
        Args:
            input_data: Dictionary containing gap analysis data with keys:
                - mode: 'role_gap' or 'job_gap'
                - target_name: Name of role/job
                - readiness: Readiness score
                - skill_gap_index: Gap index
                - matched_skills: List of matched skills
                - missing_skills: List of missing skill details
                - project_relevance_score: Project relevance score
                - relevant_projects: List of relevant projects
            max_length: Maximum length of generated text
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
        
        Returns:
            Dictionary with:
                - explanation_text: Generated explanation
                - generation_time: Time taken in seconds
                - model: Model identifier
        """
        start_time = time.time()
        
        # Ensure model is loaded
        self._ensure_model_loaded()
        
        # If model failed to load, use fallback immediately
        if self.model is None or self.tokenizer is None:
            logger.warning("Model not available, using fallback explanation")
            generation_time = time.time() - start_time
            return {
                "explanation_text": self._get_fallback_explanation(input_data),
                "generation_time": generation_time,
                "model": "fallback"
            }
        
        try:
            # Format prompt
            prompt = self._format_prompt(input_data)
            
            # Prepare messages for chat template
            messages = [
                {"role": "system", "content": "You are a career advisor. Give brief, actionable skill gap feedback in under 100 words."},
                {"role": "user", "content": prompt}
            ]
            
            # Apply chat template
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Tokenize with smaller context
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=1024  # Reduced for faster processing
            ).to(self.device)
            
            # Generate with optimized settings
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    repetition_penalty=1.1,  # Reduce repetition
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    use_cache=True  # Enable KV cache for speed
                )
            
            # Decode
            generated_text = self.tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            )
            
            generation_time = time.time() - start_time
            
            logger.info(f"✅ Generated explanation in {generation_time:.2f}s")
            
            return {
                "explanation_text": generated_text.strip(),
                "generation_time": generation_time,
                "model": "Qwen2.5-3B-Instruct-LoRA (fine-tuned)"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate explanation: {e}")
            generation_time = time.time() - start_time
            
            # Return fallback explanation
            return {
                "explanation_text": self._get_fallback_explanation(input_data),
                "generation_time": generation_time,
                "model": "fallback"
            }
    
    def _get_fallback_explanation(self, input_data: Dict[str, Any]) -> str:
        """
        Generate a simple fallback explanation without AI model.
        
        Args:
            input_data: Gap analysis data
        
        Returns:
            Basic explanation string
        """
        target_name = input_data.get("target_name", "Unknown")
        readiness = self._normalize_value(input_data.get("readiness", 0))
        num_matched = input_data.get("num_matched", 0)
        num_missing = input_data.get("num_missing", 0)
        missing_skills = input_data.get("missing_skills", [])
        project_relevance = self._normalize_value(input_data.get("project_relevance_score", 0))
        
        if readiness >= 0.8:
            status = "You're very well positioned for this role!"
            advice = "Polish the few remaining gaps to become an ideal candidate"
        elif readiness >= 0.6:
            status = "You have a solid foundation for this role."
            advice = "Focus on acquiring the most important missing skills to strengthen your profile"
        elif readiness >= 0.4:
            status = "You have some relevant experience, but key gaps remain."
            advice = "Target the high-priority skills through coursework or hands-on projects"
        else:
            status = "There's significant work needed to meet this role's requirements."
            advice = "Begin with foundational skills, then progressively build toward advanced capabilities"
        
        # Get top 3 missing skills by importance
        top_missing = sorted(missing_skills, key=lambda x: x.get('importance', 0), reverse=True)[:3]
        top_missing_names = [skill['skill'] for skill in top_missing]
        
        # Project insight
        proj_insight = ""
        if project_relevance >= 0.6:
            proj_insight = f" Your project portfolio shows {project_relevance:.0%} relevance, which strengthens your application."
        elif project_relevance >= 0.3:
            proj_insight = f" Consider expanding your project work to better demonstrate these skills."
        
        return f"""{status}

**Current Position:** {readiness:.0%} ready - You have {num_matched}/{num_matched + num_missing} required skills.{proj_insight}

**Priority Gaps:** {', '.join(top_missing_names) if top_missing_names else 'No critical gaps identified'}.

**Recommended Action:** {advice}. Look for online courses, certifications, or practical projects to build these competencies."""


# Global service instance
_explainer_service = None


def get_explainer_service() -> AIExplainerService:
    """
    Get or create the global explainer service instance.
    
    By default, uses fast fallback explanations.
    Model loading is attempted automatically on first use.
    
    Returns:
        AIExplainerService instance
    """
    global _explainer_service
    
    if _explainer_service is None:
        # Create service instance (model loads lazily on first use)
        _explainer_service = AIExplainerService()
    
    return _explainer_service
