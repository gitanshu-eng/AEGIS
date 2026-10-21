from phase5_retrieval import EpisodeMemory

def test_math_fixture():
    print("=================================================================")
    print("      PHASE 5: ISOLATED MATH & LOGIC VERIFICATION")
    print("=================================================================\n")
    
    mem = EpisodeMemory()
    
    ep1 = {
        "memory_id": "EP-1",
        "dataset": "D1",
        "structured_metadata": {"sustained_tactics": ["TA0008", "TA0043"]},
        "semantic_context": {"kinematic_vector": [0.80, 10, 0.50, 5]} # risk, dur, ar, lt
    }
    
    ep2_identical = {
        "memory_id": "EP-2",
        "dataset": "D2",
        "structured_metadata": {"sustained_tactics": ["TA0008", "TA0043"]},
        "semantic_context": {"kinematic_vector": [0.80, 10, 0.50, 5]}
    }

    ep3_diff = {
        "memory_id": "EP-3",
        "dataset": "D2",
        "structured_metadata": {"sustained_tactics": ["TA0008"]}, # Jaccard: 1 intersection / 2 union = 0.5
        "semantic_context": {"kinematic_vector": [0.60, 100, 0.10, 0]} 
    }

    mem.from_memory_obj(ep1)
    mem.from_memory_obj(ep2_identical)
    mem.from_memory_obj(ep3_diff)
    
    errors = 0

    # TEST A: Exact Identity Match
    res_a = mem._calculate_similarity_robust(ep1, ep2_identical)
    if res_a["total_score"] != 1.0:
        print(f"[FAIL] Identical episodes did not score 1.0. Score: {res_a['total_score']}")
        errors += 1
    else:
        print("[PASS] Identity match logic verified (1.0).")

    # TEST B: Jaccard Math Verification
    res_b = mem._calculate_similarity_robust(ep1, ep3_diff)
    if res_b["sub_scores"]["mitre_jaccard"] != 0.5:
        print(f"[FAIL] Jaccard math incorrect. Expected 0.5, got {res_b['sub_scores']['mitre_jaccard']}")
        errors += 1
    else:
        print("[PASS] MITRE Jaccard Index verified.")

    # TEST C: Live Query Feature Masking (Step 4)
    # If we mask out duration and lead_time, their sub-scores should be zeroed in the weighting
    res_c = mem._calculate_similarity_robust(ep1, ep3_diff, use=["risk", "attack_rate"])
    if res_c["sub_scores"]["log_duration_sim"] != 0.0 or res_c["sub_scores"]["lead_time_sim"] != 0.0:
        print(f"[FAIL] Feature mask failed to zero out unused vectors.")
        errors += 1
    else:
        print("[PASS] Live-query feature mask dynamically isolates requested vectors.")
        
    if errors == 0:
        print("\n[✓] Phase 5 core math verified. Safe to proceed to real data.")

if __name__ == "__main__":
    test_math_fixture()
