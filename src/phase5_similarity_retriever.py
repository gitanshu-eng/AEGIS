import json
from pathlib import Path
from typing import Dict, Any, List

MEMORY_BANK_PATH = Path("outputs/phase5_memory/aegis_memory_bank.json")

class KinematicSimilarityRetriever:
    def __init__(self, memory_bank_path: Path = MEMORY_BANK_PATH):
        if not memory_bank_path.exists():
            raise FileNotFoundError(f"Memory bank not found at {memory_bank_path}")
        with open(memory_bank_path, "r") as f:
            self.memory_bank = json.load(f)
        self.memory_map = {m["memory_id"]: m for m in self.memory_bank}

    def calculate_similarity(self, ep1: Dict, ep2: Dict) -> float:
        """
        Calculates a deterministic similarity score [0.0, 1.0] based on physical 
        kinematics and candidate MITRE overlap.
        """
        v1 = ep1["semantic_context"]["kinematic_vector"]
        v2 = ep2["semantic_context"]["kinematic_vector"]

        # v = [risk(0-1), duration(mins), attack_rate(0-1), lead_time(mins)]
        risk_sim = 1.0 - abs(v1[0] - v2[0])
        dur_sim = min(v1[1], v2[1]) / max(v1[1], v2[1]) if max(v1[1], v2[1]) > 0 else 1.0
        ar_sim = 1.0 - abs(v1[2] - v2[2])
        
        lt_diff = abs(v1[3] - v2[3])
        lt_sim = max(0.0, 1.0 - (lt_diff / 15.0)) # 0 similarity if > 15 min difference in lead time

        kinematic_score = (risk_sim * 0.3) + (ar_sim * 0.3) + (dur_sim * 0.2) + (lt_sim * 0.2)

        # MITRE Jaccard Index (Intersection over Union)
        t1 = set(ep1["structured_metadata"].get("sustained_tactics", []))
        t2 = set(ep2["structured_metadata"].get("sustained_tactics", []))
        
        if not t1 and not t2:
            return kinematic_score # Fallback purely to kinematic if neither has MITRE
        elif not t1 or not t2:
            mitre_score = 0.0 # One has MITRE, one doesn't -> 0 similarity on this axis
        else:
            mitre_score = len(t1 & t2) / len(t1 | t2)

        return (kinematic_score * 0.7) + (mitre_score * 0.3)

    def find_similar(self, target_id: str, top_k: int = 3) -> List[Dict]:
        if target_id not in self.memory_map:
            raise ValueError(f"Target ID {target_id} not found in memory bank.")
        
        target_ep = self.memory_map[target_id]
        results = []

        for candidate in self.memory_bank:
            # Prevent matching the episode against itself
            if candidate["memory_id"] == target_id:
                continue
            
            sim_score = self.calculate_similarity(target_ep, candidate)
            results.append({
                "memory_id": candidate["memory_id"],
                "similarity_score": sim_score,
                "dataset": candidate["source_traceability"]["source_dataset"],
                "kinematics": candidate["semantic_context"]["kinematic_vector"],
                "summary": candidate["semantic_context"]["semantic_document"]
            })

        # Sort descending by similarity
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

def run_similarity_tests():
    print("=================================================================")
    print("      PHASE 5 — STEPS 7 & 9: KINEMATIC SIMILARITY RETRIEVAL")
    print("=================================================================\n")

    retriever = KinematicSimilarityRetriever()
    
    # Target our known LEADING episode
    target_id = "EP-Friday-02-03-2018-02b744"
    target_obj = retriever.memory_map[target_id]
    
    print(f"Target Query Episode: {target_id}")
    print(f"Target Kinematics [Risk, Dur, AR, Lead]: {target_obj['semantic_context']['kinematic_vector']}")
    print(f"Target Summary: {target_obj['semantic_context']['semantic_document']}\n")
    print("-" * 65)
    
    matches = retriever.find_similar(target_id, top_k=3)
    
    for i, m in enumerate(matches, 1):
        print(f"\nMatch #{i} | Similarity Score: {m['similarity_score']:.4f}")
        print(f"  Historical ID: {m['memory_id']} ({m['dataset']})")
        print(f"  Kinematics :   {m['kinematics']}")
        print(f"  Summary    :   {m['summary']}")

    print("\n[PASS] Deterministic similarity retrieval executed successfully.")

if __name__ == "__main__":
    run_similarity_tests()
