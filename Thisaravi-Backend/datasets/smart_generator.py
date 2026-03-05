import random

def get_smart_data(student_data, job_data):
    """
    Returns a dictionary of high-quality, deterministic recommendations.
    Used to prompt the LLM with expert context.
    """
    role = student_data.get("demographics", "Student")
    target_role = job_data.get("target_job_role", "Data Scientist")
    
    # Normalize
    role_lower = role.lower()
    
    # Extract years
    years = 0
    words = role_lower.split()
    for i, w in enumerate(words):
        if w.isdigit() and i+1 < len(words) and "year" in words[i+1]:
            try: years = int(w)
            except: pass
    
    match_score = 45 + (years * 3)
    if match_score > 85: match_score = 85
    match_score_str = f"{match_score}%"

    # Logic
    if any(x in role_lower for x in ['quantitative', 'economics', 'mba', 'fintech', 'financial', 'finance']):
        return {
            "missing_skills": ["Python (NumPy/Pandas)", "Stochastic Calculus in code", "Machine Learning (Time Series)", "Algo Trading Backtesting", "SQL for financial data"],
            "match_score": match_score_str,
            "analysis": f"You have the strong math/theory background from your {role}. The gap is implementation. Quant finance is no longer just equations; it's high-performance code. You need to translate stochastic models into fast Python/C++ code and test them on tick-level data.",
            "project_title": "Algorithmic Trading Strategy Backtester",
            "objective": "Build a discrete-event simulator to test a pairs-trading or mean-reversion strategy on historical crypto/stock data.",
            "tech_stack": ["Python", "Pandas", "Backtrader (or custom loop)", "Matplotlib"],
            "implementation_plan": [
                "**Strategy**: Define a mean-reversion logic (Z-Score of spread) or momentum signal.",
                "**Data**: Ingest 1-minute interval price data from an API (e.g., YFinance or CryptoCompare).",
                "**Engine**: Simulate execution, accounting for slippage and commission fees.",
                "**Metrics**: Calculate Sharpe Ratio, Max Drawdown, and Alpha."
            ]
        }

    elif any(x in role_lower for x in ['design', 'graphic', 'video', 'sound', 'art', 'novel', 'poet', 'interior', 'writer', 'editor']):
        if "sound" in role_lower or "audio" in role_lower or "music" in role_lower:
             return {
                "missing_skills": ["Python (Librosa)", "Digital Signal Processing (DSP)", "Generative Deep Learning (WaveNet)", "Audio APIs"],
                "match_score": match_score_str,
                "analysis": f"You understand the medium ({role}). The gap is generative AI. Instead of manually editing, you need to use Python to generate or modify content algorithmically.",
                "project_title": "Generative Lo-Fi Beat Maker",
                "objective": "Train a simple LSTM or VAE to generate infinite Lo-Fi hip hop tracks (MIDI or Audio).",
                "tech_stack": ["Python", "PyTorch", "Librosa", "Streamlit"],
                "implementation_plan": [
                    "**Data**: MIDI dataset of drum patterns.",
                    "**Model**: Train an RNN to predict the next note/beat.",
                    "**Synthesis**: Map the generated MIDI to samples (Kick, Snare).",
                    "**UI**: A simple web player that generates a new beat on click."
                ]
             }
        else:
             return {
                "missing_skills": ["Python", "Computer Vision (Generative Adversarial Networks)", "Data Visualization (D3.js/Three.js)", "Computational Creativity"],
                "match_score": match_score_str,
                "analysis": "You have the creative eye. The gap is the 'Code Brush'. Generative Design isn't about drawing; it's about defining the constraints and letting the computer draw.",
                "project_title": "AI-Assisted Creative Tool",
                "objective": "Build a tool that takes a rough sketch or text prompt and refines it using a generative model.",
                "tech_stack": ["Python", "Stable Diffusion API", "Streamlit", "OpenCV"],
                "implementation_plan": [
                    "**Interface**: Canvas to draw a crude shape.",
                    "**Pipeline**: Send the image + prompt to an Image-to-Image model.",
                    "**Refinement**: Allow user to adjust 'Denoising Strength' (Creativity slider).",
                    "**Gallery**: Save and display the iterations."
                ]
             }

    elif any(x in role_lower for x in ['nurse', 'dental', 'veterinarian', 'doctor', 'radiologist', 'pharmacist', 'therapist', 'medical', 'biology', 'bio']):
        return {
            "missing_skills": ["Python", "Computer Vision (Medical Imaging)", "Bioinformatics", "Privacy (HIPAA) in AI", "Data pipelines"],
            "match_score": match_score_str,
            "analysis": f"{role} gives you deep domain expertise. You know what a pathology looks like. The gap is teaching the machine to see it. Medical AI is heavily focused on Image Analysis.",
            "project_title": "Medical Imaging Triage Assistant",
            "objective": "Train a CNN to detect anomalies (e.g., Pneumonia or fracture) in medical scans to prioritize radiologist review.",
            "tech_stack": ["Python", "PyTorch/Monai", "DICOM standard", "NIH Chest X-ray dataset"],
            "implementation_plan": [
                "**Data**: Load anonymized X-ray dataset.",
                "**Model**: Fine-tune a ResNet or DenseNet model.",
                "**Grad-CAM**: Visualize *where* the model is looking (Heatmap overlay).",
                "**App**: Upload a scan and get a probability score."
            ]
        }

    elif any(x in role_lower for x in ['chef', 'travel', 'event', 'social', 'bootcamp', 'teacher', 'retail']):
        return {
            "missing_skills": ["Python", "Recommender Systems", "Graph Databases", "Constraint Optimization", "API Integration"],
            "match_score": match_score_str,
            "analysis": f"In {role}, you manage complex logistics or preferences. The gap is scaling that personalization. Applications here are about finding connections in massive datasets.",
            "project_title": "Personalized Recommendation Engine",
            "objective": "Build a system that recommends unique combinations (Recipes, Itineraries) based on user constraints and hidden similarities.",
            "tech_stack": ["Python", "Pandas", "Scikit-learn (Cosine Similarity)", "Neo4j (Graph)"],
            "implementation_plan": [
                "**Data**: Scrape recipes or travel logs.",
                "**Graph**: Connect ingredients/locations that often appear together.",
                "**Query**: 'Find a path from Ingredient A to B'.",
                "**UI**: User enters 3 items, gets a 'Perfect Match' suggestion."
            ]
        }

    elif any(x in role_lower for x in ['pilot', 'traffic', 'ship', 'miner', 'oil', 'civil', 'engineer', 'mechanical', 'electrical']):
        return {
            "missing_skills": ["Python", "Simulation (Agent-based or Physics)", "Optimization Algorithms", "IoT/Sensor Fusion", "Spatial Analysis"],
            "match_score": match_score_str,
            "analysis": f"As a {role}, you deal with high-stakes physical systems. The gap is 'Digital Twinning'. You need to simulate the environment (Airspace, Ocean, Mine) in code to test 'What If' scenarios.",
            "project_title": "Operational Trajectory Optimizer",
            "objective": "Calculate the most fuel-efficient or safe path through a dynamic environment (Weather, Traffic).",
            "tech_stack": ["Python", "NetworkX (A* Algorithm)", "SciPy (Optimization)", "Geopandas"],
            "implementation_plan": [
                "**Environment**: Model the world as a grid with costs (Wind, Terrain).",
                "**Algorithm**: Implement A* or Dijkstra's algorithm to find the lowest cost path.",
                "**Constraint**: Add dynamic obstacles (Storms) that move over time.",
                "**Viz**: Animation of the optimal route updating as conditions change."
            ]
        }

    elif any(x in role_lower for x in ['police', 'detective', 'security', 'fire', 'investigator', 'guard', 'intelligence', 'soldier', 'officer', 'military']):
         return {
            "missing_skills": ["Python", "Network Analysis (Link Analysis)", "Anomaly Detection (Video/Data)", "OSINT tools", "GIS"],
            "match_score": match_score_str,
            "analysis": f"The investigative mindset of a {role} is perfect for Data Forensics. The gap is the toolset. You need to analyze the network of connections using Graph Analysis and Computer Vision.",
            "project_title": "Anomaly Detection in Surveillance/Network Data",
            "objective": "Automatically flag suspicious behavior in a video feed or transaction network.",
            "tech_stack": ["Python", "OpenCV (Video) or NetworkX (Data)", "Scikit-learn (Isolation Forest)"],
            "implementation_plan": [
                "**Ingest**: specific Data stream (Video frames or Log lines).",
                "**Baseline**: Learn the 'Normal' pattern (Background extraction or typical traffic).",
                "**Detect**: Flag deviations (Motion in restricted area, Spike in connections).",
                "**Alert**: Dashboard showing the flagged event clip/graph node."
            ]
         }
         
    else:
        return {
            "missing_skills": ["Python", "Natural Language Processing (NLP)", "Data Mining", "Ethics in AI", "Social Network Analysis"],
            "match_score": "60%",
            "analysis": f"Domain experts like you ({role}) bring critical context to AI. The gap is the technical ability to test your theories at scale using Python to mine large datasets.",
            "project_title": "Domain-Specific Interaction Analyzer",
            "objective": "Analyze patterns in text or social data relevant to your field using NLP and Graph Theory.",
            "tech_stack": ["Python", "NLTK/Spacy", "Gephi", "Pandas"],
            "implementation_plan": [
                "**Data**: Collect a corpus of relevant documents or interactions.",
                "**Extract**: Use NLP to pull out key entities and relationships.",
                "**Network**: Build a graph of who talks to whom.",
                "**Insight**: Identify central nodes or recurring themes."
            ]
        }


