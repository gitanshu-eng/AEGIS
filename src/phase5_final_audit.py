import json
from pathlib import Path
import os

MEMORY_BANK_PATH = Path("outputs/phase5_memory/aegis_memory_bank.json")

class AegisMemoryEngine:
    def __init__(self, memory_bank_path: Path = MEMORY_BANK_PATH):
        with open(memory_bank_path, "r") as f:
            self.memory_bank = json.load(f)
        self.memory_map = {m["memory_id"]: m for m in self.memory_bank}

    def _calc_sim(self, v1, v2, t1, t2):
        risk_sim = 1.0 - abs(v1[0] - v2[0])
        dur_sim = min(v1[1], v2[1]) / max(v1[1], v2[1]) if max(v1[1], v2[1]) > 0 else 1.0
        ar_sim = 1.0 - abs(v1[2] - v2[2])
        lt_sim = max(0.0, 1.0 - (abs(v1[3] - v2[3]) / 15.0))
        kin_score = (risk_sim * 0.3) + (ar_sim * 0.3) + (dur_sim * 0.2) + (lt_sim * 0.2)

        s1, s2 = set(t1), set(t2)
        if not s1 and not s2: mitre_score = kin_score
        elif not s1 or not s2: mitre_score = 0.0
        else: mitre_score = len(s1 & s2) / len(s1 | s2)

        return (kin_score * 0.7) + (mitre_score * 0.3)

    def retrieve(self, target_id: str, top_k: int = 3, exclude_dataset: str = None, require_risk: str = None):
        if target_id not in self.memory_map:
            raise ValueError(f"Target ID {target_id} not found in memory bank.")
        
        target_ep = self.memory_map[target_id]
        v1 = target_ep["semantic_context"]["kinematic_vector"]
        t1 = target_ep["structured_metadata"].get("sustained_tactics", [])

        results = []
        for cand in self.memory_bank:
            if cand["memory_id"] == target_id:
                continue
            
            # Step 10: Structured Metadata Pre-Filtering
            if exclude_dataset and cand["source_traceability"]["source_dataset"] == exclude_dataset:
                continue
            if require_risk and cand["structured_metadata"]["peak_risk_level"] != require_risk:
                continue
                
            # Semantic Similarity Calculation
            v2 = cand["semantic_context"]["kinematic_vector"]
            t2 = cand["structured_metadata"].get("sustained_tactics", [])
            sim = self._calc_sim(v1, v2, t1, t2)
            
            results.append({"memory_id": cand["memory_id"], "score": sim, "trace": cand["source_traceability"]})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

def run_final_audit():
    print("=================================================================")
    print("      PHASE 5 — STEPS 10-12: ADVERSARIAL & TRACEABILITY AUDIT")
    print("=================================================================\n")
    
    engine = AegisMemoryEngine()
    target = "EP-Friday-02-03-2018-02b744"
    target_ds = engine.memory_map[target]["source_traceability"]["source_dataset"]
    errors = 0

    print("Test A (Step 10): Combined Retrieval (Similarity + Filter)")
    print(f"  Target: {target}")
    print(f"  Filter: exclude_dataset = '{target_ds}'")
    cross_day_matches = engine.retrieve(target, exclude_dataset=target_ds)
    print(f"  Result count: {len(cross_day_matches)}")
    for m in cross_day_matches:
        print(f"  - {m['memory_id']} (Dataset: {m['trace']['source_dataset']}, Sim: {m['score']:.4f})")
        if m['trace']['source_dataset'] == target_ds:
            print("    [!] FATAL: Filter leakage detected.")
            errors += 1
    print("  [PASS] Pre-filtering effectively overrides similarity." if errors == 0 else "[FAIL]")

    print("\nTest B (Step 11): Traceability Audit")
    if cross_day_matches:
        trace = cross_day_matches[0]["trace"]
        p1_file = trace["phase1_file"]
        print(f"  Verifying trace for {cross_day_matches[0]['memory_id']}")
        print(f"  Expected Phase 1 Source: {p1_file}")
        if os.path.exists(p1_file):
            print("  [PASS] Source CSV verified on disk. unbroken traceability chain.")
        else:
            print("  [!] FATAL: Traceability link broken. File missing.")
            errors += 1

    print("\nTest C (Step 12): Adversarial - Hallucinated ID")
    try:
        engine.retrieve("EP-FAKE-HALLUCINATION-999")
        print("  [!] FATAL: System silently accepted hallucinated ID.")
        errors += 1
    except ValueError as e:
        print(f"  [PASS] System explicitly rejected hallucinated ID: {e}")

    print("\nTest D (Step 12): Adversarial - Overconstrained Filter")
    empty_matches = engine.retrieve(target, require_risk="LOW")
    if len(empty_matches) == 0:
        print("  [PASS] System correctly returned empty list without failing or hallucinating.")
    else:
        print("  [!] FATAL: System hallucinated matches for impossible constraints.")
        errors += 1

    if errors == 0:
        print("\n[✓] ALL TESTS PASSED. PHASE 5 IS OFFICIALLY READY FOR FREEZE.")
    else:
        print(f"\n[FAIL] Found {errors} critical errors.")

if __name__ == "__main__":
    run_final_audit()
