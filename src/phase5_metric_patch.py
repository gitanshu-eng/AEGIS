import math

def calculate_similarity_robust(ep1, ep2):
    v1 = ep1["semantic_context"]["kinematic_vector"]
    v2 = ep2["semantic_context"]["kinematic_vector"]

    # v = [risk, duration, attack_rate, lead_time]
    risk_sim = 1.0 - abs(v1[0] - v2[0])
    ar_sim = 1.0 - abs(v1[2] - v2[2])
    
    # Reviewer Patch: Log-duration to prevent massive episodes from dominating
    dur1, dur2 = math.log1p(v1[1]), math.log1p(v2[1])
    dur_sim = 1.0 - (abs(dur1 - dur2) / max(dur1, dur2, 1e-5))
    
    lt_sim = max(0.0, 1.0 - (abs(v1[3] - v2[3]) / 15.0))
    
    kin_score = (risk_sim * 0.3) + (ar_sim * 0.3) + (dur_sim * 0.2) + (lt_sim * 0.2)

    # Reviewer Patch: Fix metric space empty-set hack
    t1 = set(ep1["structured_metadata"].get("sustained_tactics", []))
    t2 = set(ep2["structured_metadata"].get("sustained_tactics", []))
    
    if not t1 and not t2:
        mitre_score = 1.0  # Perfect match on "no tactics identified"
    elif not t1 or not t2:
        mitre_score = 0.0
    else:
        mitre_score = len(t1 & t2) / len(t1 | t2)

    total_score = (kin_score * 0.7) + (mitre_score * 0.3)
    
    # Return per-component sub-scores for SOC analyst interpretability
    return {
        "total_score": total_score,
        "sub_scores": {
            "risk_sim": risk_sim,
            "attack_rate_sim": ar_sim,
            "log_duration_sim": dur_sim,
            "lead_time_sim": lt_sim,
            "mitre_jaccard": mitre_score
        }
    }

print("[✓] Log-duration, metric properties, and sub-score reporting patched for Phase 5.")
