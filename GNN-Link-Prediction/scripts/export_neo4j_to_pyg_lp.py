"""
Export Neo4j heterogeneous knowledge graph to PyTorch Geometric HeteroData.

This script:
1. Connects to Neo4j
2. Exports all relevant nodes (Person, Skill, Project, SkillCategory)
3. Exports all relevant edges (HAS_SKILL, WORKED_ON, USES_TECHNOLOGY, BELONGS_TO_CATEGORY)
4. Builds node features from embeddings and computed properties
5. Saves HeteroData object + ID mappings for reproducibility

Node Features:
- Skill: embedding vector (384-dim, pad if missing)
- Person: [num_skills, num_projects, experience_months] (normalized)
- Project: mean of connected skill embeddings
- SkillCategory: mean of member skill embeddings
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import torch
from neo4j import GraphDatabase
from torch_geometric.data import HeteroData
from sklearn.preprocessing import StandardScaler

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD,
    HETERODATA_PATH, ID_MAPS_PATH, STATS_PATH,
    SKILL_EMBEDDING_DIM, RANDOM_SEED, LOG_LEVEL, LOG_FILE
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set random seeds
np.random.seed(RANDOM_SEED)
torch.manual_seed(RANDOM_SEED)


class Neo4jToHeteroDataExporter:
    """Export Neo4j heterogeneous KG to PyTorch Geometric HeteroData."""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.id_maps = {
            'person': {},
            'skill': {},
            'project': {},
            'skill_category': {}
        }
        self.stats = {}
        
    def close(self):
        self.driver.close()
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ========================================================================
    # NODE EXPORT
    # ========================================================================
    
    def export_persons(self, session) -> Tuple[torch.Tensor, Dict[str, int]]:
        """
        Export Person nodes with features: [num_skills, num_projects, experience_months].
        
        Returns:
            features: Tensor of shape [num_persons, 3]
            id_map: {person_id: idx}
        """
        logger.info("Exporting Person nodes...")
        
        query = """
        MATCH (p:Person)
        OPTIONAL MATCH (p)-[:HAS_SKILL]->(s:Skill)
        OPTIONAL MATCH (p)-[:WORKED_ON]->(proj:Project)
        WITH p,
             count(DISTINCT s) as num_skills,
             count(DISTINCT proj) as num_projects
        RETURN p.candidate_id as person_id,
               num_skills,
               num_projects,
               COALESCE(p.experience_months, 0) as experience_months
        ORDER BY person_id
        """
        
        result = session.run(query)
        persons = list(result)
        
        if not persons:
            raise ValueError("No Person nodes found in Neo4j!")
        
        logger.info(f"Found {len(persons)} Person nodes")
        
        # Build ID map
        id_map = {p['person_id']: idx for idx, p in enumerate(persons)}
        
        # Extract features
        features = np.array([
            [p['num_skills'], p['num_projects'], p['experience_months']]
            for p in persons
        ], dtype=np.float32)
        
        # Normalize features
        scaler = StandardScaler()
        features = scaler.fit_transform(features)
        
        logger.info(f"Person features shape: {features.shape}")
        logger.info(f"Person features stats: mean={features.mean():.3f}, std={features.std():.3f}")
        
        self.stats['num_persons'] = len(persons)
        self.stats['person_feature_stats'] = {
            'mean': features.mean(axis=0).tolist(),
            'std': features.std(axis=0).tolist()
        }
        
        return torch.tensor(features, dtype=torch.float), id_map
    
    def export_skills(self, session) -> Tuple[torch.Tensor, Dict[str, int]]:
        """
        Export Skill nodes with embedding features.
        If embedding is missing, use zero vector.
        
        Returns:
            features: Tensor of shape [num_skills, embedding_dim]
            id_map: {skill_name: idx}
        """
        logger.info("Exporting Skill nodes...")
        
        query = """
        MATCH (s:Skill)
        RETURN s.name as skill_name,
               s.embedding as embedding
        ORDER BY skill_name
        """
        
        result = session.run(query)
        skills = list(result)
        
        if not skills:
            raise ValueError("No Skill nodes found in Neo4j!")
        
        logger.info(f"Found {len(skills)} Skill nodes")
        
        # Build ID map
        id_map = {s['skill_name']: idx for idx, s in enumerate(skills)}
        
        # Extract embeddings with dimension checking
        features = []
        missing_count = 0
        wrong_dim_count = 0
        
        for skill in skills:
            emb = skill['embedding']
            if emb is not None and len(emb) > 0:
                emb_array = np.array(emb, dtype=np.float32)
                
                # Check dimension and pad/truncate if needed
                if len(emb_array) == SKILL_EMBEDDING_DIM:
                    features.append(emb_array)
                elif len(emb_array) < SKILL_EMBEDDING_DIM:
                    # Pad with zeros
                    padded = np.zeros(SKILL_EMBEDDING_DIM, dtype=np.float32)
                    padded[:len(emb_array)] = emb_array
                    features.append(padded)
                    wrong_dim_count += 1
                else:
                    # Truncate
                    features.append(emb_array[:SKILL_EMBEDDING_DIM])
                    wrong_dim_count += 1
            else:
                features.append(np.zeros(SKILL_EMBEDDING_DIM, dtype=np.float32))
                missing_count += 1
        
        # Now all embeddings have same dimension, safe to convert to array
        features = np.array(features, dtype=np.float32)
        
        logger.info(f"Skill features shape: {features.shape}")
        logger.info(f"Skills with missing embeddings: {missing_count}/{len(skills)} ({missing_count/len(skills)*100:.1f}%)")
        if wrong_dim_count > 0:
            logger.warning(f"Skills with wrong embedding dimensions (padded/truncated): {wrong_dim_count}/{len(skills)}")
        
        self.stats['num_skills'] = len(skills)
        self.stats['skills_missing_embeddings'] = missing_count
        self.stats['skill_embedding_coverage'] = 1 - (missing_count / len(skills))
        
        return torch.tensor(features, dtype=torch.float), id_map
    
    def export_projects(self, session, skill_id_map: Dict[str, int], 
                        skill_features: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, int]]:
        """
        Export Project nodes with features = mean of connected skill embeddings.
        
        Returns:
            features: Tensor of shape [num_projects, embedding_dim]
            id_map: {project_id: idx}
        """
        logger.info("Exporting Project nodes...")
        
        query = """
        MATCH (proj:Project)
        OPTIONAL MATCH (proj)-[:USES_TECHNOLOGY]->(s:Skill)
        WITH proj, collect(s.name) as skill_names
        RETURN proj.project_id as project_id,
               skill_names
        ORDER BY project_id
        """
        
        result = session.run(query)
        projects = list(result)
        
        if not projects:
            logger.warning("No Project nodes found in Neo4j!")
            return torch.empty(0, SKILL_EMBEDDING_DIM), {}
        
        logger.info(f"Found {len(projects)} Project nodes")
        
        # Build ID map
        id_map = {p['project_id']: idx for idx, p in enumerate(projects)}
        
        # Compute features as mean of skill embeddings
        features = []
        projects_without_skills = 0
        
        for project in projects:
            skill_names = project['skill_names']
            if skill_names:
                # Get skill indices
                skill_indices = [skill_id_map[name] for name in skill_names if name in skill_id_map]
                if skill_indices:
                    # Average embeddings
                    skill_embeds = skill_features[skill_indices]
                    project_emb = skill_embeds.mean(dim=0)
                    features.append(project_emb.numpy())
                else:
                    features.append(np.zeros(SKILL_EMBEDDING_DIM, dtype=np.float32))
                    projects_without_skills += 1
            else:
                features.append(np.zeros(SKILL_EMBEDDING_DIM, dtype=np.float32))
                projects_without_skills += 1
        
        features = np.array(features)
        
        logger.info(f"Project features shape: {features.shape}")
        logger.info(f"Projects without skill connections: {projects_without_skills}/{len(projects)}")
        
        self.stats['num_projects'] = len(projects)
        self.stats['projects_without_skills'] = projects_without_skills
        
        return torch.tensor(features, dtype=torch.float), id_map
    
    def export_skill_categories(self, session, skill_id_map: Dict[str, int],
                                skill_features: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, int]]:
        """
        Export SkillCategory nodes with features = mean of member skill embeddings.
        
        Returns:
            features: Tensor of shape [num_categories, embedding_dim]
            id_map: {category_name: idx}
        """
        logger.info("Exporting SkillCategory nodes...")
        
        query = """
        MATCH (c:SkillCategory)
        OPTIONAL MATCH (s:Skill)-[:BELONGS_TO_CATEGORY]->(c)
        WITH c, collect(s.name) as skill_names
        RETURN c.name as category_name,
               skill_names
        ORDER BY category_name
        """
        
        result = session.run(query)
        categories = list(result)
        
        if not categories:
            logger.warning("No SkillCategory nodes found in Neo4j!")
            return torch.empty(0, SKILL_EMBEDDING_DIM), {}
        
        logger.info(f"Found {len(categories)} SkillCategory nodes")
        
        # Build ID map
        id_map = {c['category_name']: idx for idx, c in enumerate(categories)}
        
        # Compute features as mean of skill embeddings
        features = []
        categories_without_skills = 0
        
        for category in categories:
            skill_names = category['skill_names']
            if skill_names:
                skill_indices = [skill_id_map[name] for name in skill_names if name in skill_id_map]
                if skill_indices:
                    skill_embeds = skill_features[skill_indices]
                    category_emb = skill_embeds.mean(dim=0)
                    features.append(category_emb.numpy())
                else:
                    features.append(np.zeros(SKILL_EMBEDDING_DIM, dtype=np.float32))
                    categories_without_skills += 1
            else:
                features.append(np.zeros(SKILL_EMBEDDING_DIM, dtype=np.float32))
                categories_without_skills += 1
        
        features = np.array(features)
        
        logger.info(f"SkillCategory features shape: {features.shape}")
        logger.info(f"Categories without skill members: {categories_without_skills}/{len(categories)}")
        
        self.stats['num_skill_categories'] = len(categories)
        self.stats['categories_without_skills'] = categories_without_skills
        
        return torch.tensor(features, dtype=torch.float), id_map
    
    # ========================================================================
    # EDGE EXPORT
    # ========================================================================
    
    def export_edges(self, session, edge_type: Tuple[str, str, str],
                     src_id_map: Dict, dst_id_map: Dict,
                     cypher_query: str) -> torch.Tensor:
        """
        Generic edge export function.
        
        Args:
            edge_type: (src_type, relation, dst_type)
            src_id_map: {src_id: idx}
            dst_id_map: {dst_id: idx}
            cypher_query: Cypher query returning src_id, dst_id
            
        Returns:
            edge_index: Tensor of shape [2, num_edges]
        """
        src_type, relation, dst_type = edge_type
        logger.info(f"Exporting edges: ({src_type})-[{relation}]->({dst_type})...")
        
        result = session.run(cypher_query)
        edges = list(result)
        
        if not edges:
            logger.warning(f"No edges found for {edge_type}")
            return torch.empty((2, 0), dtype=torch.long)
        
        # Build edge_index
        edge_list = []
        skipped = 0
        
        for edge in edges:
            src_id = edge['src_id']
            dst_id = edge['dst_id']
            
            # Skip if IDs not in maps (shouldn't happen, but be safe)
            if src_id not in src_id_map or dst_id not in dst_id_map:
                skipped += 1
                continue
            
            src_idx = src_id_map[src_id]
            dst_idx = dst_id_map[dst_id]
            edge_list.append([src_idx, dst_idx])
        
        if skipped > 0:
            logger.warning(f"Skipped {skipped} edges due to missing node IDs")
        
        if not edge_list:
            return torch.empty((2, 0), dtype=torch.long)
        
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        
        logger.info(f"Exported {edge_index.shape[1]} edges for {edge_type}")
        
        return edge_index
    
    def export_has_skill_edges(self, session, person_id_map: Dict, 
                               skill_id_map: Dict) -> torch.Tensor:
        """Export Person-HAS_SKILL->Skill edges."""
        query = """
        MATCH (p:Person)-[:HAS_SKILL]->(s:Skill)
        RETURN p.candidate_id as src_id, s.name as dst_id
        """
        edge_index = self.export_edges(
            session,
            ('person', 'has_skill', 'skill'),
            person_id_map,
            skill_id_map,
            query
        )
        self.stats['num_has_skill_edges'] = edge_index.shape[1]
        return edge_index
    
    def export_worked_on_edges(self, session, person_id_map: Dict,
                               project_id_map: Dict) -> torch.Tensor:
        """Export Person-WORKED_ON->Project edges."""
        query = """
        MATCH (p:Person)-[:WORKED_ON]->(proj:Project)
        RETURN p.candidate_id as src_id, proj.project_id as dst_id
        """
        edge_index = self.export_edges(
            session,
            ('person', 'worked_on', 'project'),
            person_id_map,
            project_id_map,
            query
        )
        self.stats['num_worked_on_edges'] = edge_index.shape[1]
        return edge_index
    
    def export_uses_technology_edges(self, session, project_id_map: Dict,
                                     skill_id_map: Dict) -> torch.Tensor:
        """Export Project-USES_TECHNOLOGY->Skill edges."""
        query = """
        MATCH (proj:Project)-[:USES_TECHNOLOGY]->(s:Skill)
        RETURN proj.project_id as src_id, s.name as dst_id
        """
        edge_index = self.export_edges(
            session,
            ('project', 'uses_technology', 'skill'),
            project_id_map,
            skill_id_map,
            query
        )
        self.stats['num_uses_technology_edges'] = edge_index.shape[1]
        return edge_index
    
    def export_belongs_to_category_edges(self, session, skill_id_map: Dict,
                                        category_id_map: Dict) -> torch.Tensor:
        """Export Skill-BELONGS_TO_CATEGORY->SkillCategory edges."""
        query = """
        MATCH (s:Skill)-[:BELONGS_TO_CATEGORY]->(c:SkillCategory)
        RETURN s.name as src_id, c.name as dst_id
        """
        edge_index = self.export_edges(
            session,
            ('skill', 'belongs_to_category', 'skill_category'),
            skill_id_map,
            category_id_map,
            query
        )
        self.stats['num_belongs_to_category_edges'] = edge_index.shape[1]
        return edge_index
    
    # ========================================================================
    # MAIN EXPORT
    # ========================================================================
    
    def export_to_heterodata(self) -> HeteroData:
        """Main export function: build complete HeteroData object."""
        logger.info("="*80)
        logger.info("Starting Neo4j to HeteroData export...")
        logger.info("="*80)
        
        data = HeteroData()
        
        with self.driver.session() as session:
            # 1. Export nodes
            logger.info("\n[STEP 1/2] Exporting nodes...")
            
            person_x, person_id_map = self.export_persons(session)
            skill_x, skill_id_map = self.export_skills(session)
            project_x, project_id_map = self.export_projects(session, skill_id_map, skill_x)
            category_x, category_id_map = self.export_skill_categories(session, skill_id_map, skill_x)
            
            # Store in HeteroData
            data['person'].x = person_x
            data['skill'].x = skill_x
            if project_x.shape[0] > 0:
                data['project'].x = project_x
            if category_x.shape[0] > 0:
                data['skill_category'].x = category_x
            
            # Store ID maps
            self.id_maps['person'] = person_id_map
            self.id_maps['skill'] = skill_id_map
            self.id_maps['project'] = project_id_map
            self.id_maps['skill_category'] = category_id_map
            
            # 2. Export edges
            logger.info("\n[STEP 2/2] Exporting edges...")
            
            has_skill_edges = self.export_has_skill_edges(session, person_id_map, skill_id_map)
            data['person', 'has_skill', 'skill'].edge_index = has_skill_edges
            
            if project_id_map:
                worked_on_edges = self.export_worked_on_edges(session, person_id_map, project_id_map)
                data['person', 'worked_on', 'project'].edge_index = worked_on_edges
                
                uses_tech_edges = self.export_uses_technology_edges(session, project_id_map, skill_id_map)
                data['project', 'uses_technology', 'skill'].edge_index = uses_tech_edges
            
            if category_id_map:
                belongs_edges = self.export_belongs_to_category_edges(session, skill_id_map, category_id_map)
                data['skill', 'belongs_to_category', 'skill_category'].edge_index = belongs_edges
        
        logger.info("\n" + "="*80)
        logger.info("Export complete!")
        logger.info("="*80)
        logger.info(f"\nHeteroData summary:")
        logger.info(data)
        
        return data
    
    def save_outputs(self, data: HeteroData):
        """Save HeteroData, ID maps, and statistics."""
        logger.info("\nSaving outputs...")
        
        # Save HeteroData
        torch.save(data, HETERODATA_PATH)
        logger.info(f"[OK] Saved HeteroData to: {HETERODATA_PATH}")
        
        # Save ID maps
        with open(ID_MAPS_PATH, 'w') as f:
            json.dump(self.id_maps, f, indent=2)
        logger.info(f"[OK] Saved ID maps to: {ID_MAPS_PATH}")
        
        # Save statistics
        with open(STATS_PATH, 'w') as f:
            json.dump(self.stats, f, indent=2)
        logger.info(f"[OK] Saved statistics to: {STATS_PATH}")
        
        logger.info("\n[OK] All outputs saved successfully!")


def main():
    """Main execution function."""
    try:
        with Neo4jToHeteroDataExporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD) as exporter:
            # Export to HeteroData
            data = exporter.export_to_heterodata()
            
            # Save outputs
            exporter.save_outputs(data)
            
            logger.info("\n" + "="*80)
            logger.info("SUCCESS: Neo4j -> HeteroData export completed!")
            logger.info("="*80)
            logger.info(f"\nNext steps:")
            logger.info(f"1. Review statistics: {STATS_PATH}")
            logger.info(f"2. Run baseline evaluation: python scripts/eval_baselines.py")
            logger.info(f"3. Train GNN: python scripts/train_linkpred_gnn.py")
            
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
