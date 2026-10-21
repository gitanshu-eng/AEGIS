import json
from pathlib import Path
from typing import Dict, Any, List, Optional

MEMORY_BANK_PATH = Path("outputs/phase5_memory/aegis_memory_bank.json")

class StructuredRetriever:
    def __init__(self, memory_bank_path: Path = MEMORY_BANK_PATH):
        if not memory_bank_path.exists():
            raise FileNotFoundError(f"Memory bank not found at {memory_bank_path}")
        with open(memory_bank_path, "r") as f:
            self.memory_bank: List[Dict[str, Any]] = json.load(f)

    def query(
        self,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        peak_risk_level: Optional[str] = None,
        dominant_signal: Optional[str] = None,
        lead_lag_classification: Optional[str] = None,
        has_tactic: Optional[str] = None,
        has_technique: Optional[str] = None,
        min_duration_minutes: Optional[int] = None,
        exclude_memory_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes an exact boolean intersection (AND) over structured metadata.
        """
        results = []
        for mem in self.memory_bank:
            # Prevent matching against self during incident investigations
            if exclude_memory_id and mem["memory_id"] == exclude_memory_id:
                continue

            meta = mem["structured_metadata"]
            bounds = mem["source_traceability"]["temporal_bounds"]

            if min_risk_score is not None and meta["peak_risk_score"] < min_risk_score:
                continue
            if max_risk_score is not None and meta["peak_risk_score"] > max_risk_score:
                continue
            if peak_risk_level is not None and meta["peak_risk_level"] != peak_risk_level:
                continue
            if dominant_signal is not None and meta["dominant_signal"] != dominant_signal:
                continue
            if lead_lag_classification is not None and meta["lead_lag_classification"] != lead_lag_classification:
                continue
            if has_tactic is not None and has_tactic not in meta["sustained_tactics"]:
                continue
            if has_technique is not None and has_technique not in meta["sustained_techniques"]:
                continue
            if min_duration_minutes is not None and bounds["duration_minutes"] < min_duration_minutes:
                continue

            results.append(mem)

        return results

def run_retrieval_tests():
    print("=================================================================")
    print("      PHASE 5 — STEP 6: STRUCTURED RETRIEVAL TESTS")
    print("=================================================================\n")

    retriever = StructuredRetriever()
    print(f"Loaded memory bank with {len(retriever.memory_bank)} records.\n")

    # Test 1: Query for CRITICAL risk episodes
    criticals = retriever.query(peak_risk_level="CRITICAL")
    print(f"Test 1: peak_risk_level='CRITICAL'")
    print(f"  Result Count: {len(criticals)}")
    for c in criticals:
        print(f"  - {c['memory_id']} (Score: {c['structured_metadata']['peak_risk_score']}, "
              f"Signal: {c['structured_metadata']['dominant_signal']}, "
              f"Lead/Lag: {c['structured_metadata']['lead_lag_classification']})")
    assert len(criticals) > 0, "Failed: Expected at least 1 CRITICAL episode"

    # Test 2: Query for the genuine LEADING episode
    leadings = retriever.query(lead_lag_classification="LEADING")
    print(f"\nTest 2: lead_lag_classification='LEADING'")
    print(f"  Result Count: {len(leadings)}")
    for l in leadings:
        print(f"  - {l['memory_id']} (Lead time: {l['structured_metadata']['lead_time_minutes']} min, "
              f"Dataset: {l['source_traceability']['source_dataset']})")
    assert len(leadings) == 1, f"Failed: Expected exactly 1 LEADING episode, got {len(leadings)}"

    # Test 3: Compound query with exclusion (Self-matching guard)
    target_id = leadings[0]["memory_id"]
    excluded = retriever.query(lead_lag_classification="LEADING", exclude_memory_id=target_id)
    print(f"\nTest 3: Self-exclusion on {target_id}")
    print(f"  Result Count: {len(excluded)}")
    assert len(excluded) == 0, "Failed: Self-exclusion did not drop target memory_id"

    # Test 4: Empty result test (Non-existent criteria)
    impossible = retriever.query(min_risk_score=99.9, dominant_signal="NonExistentSignal")
    print(f"\nTest 4: Impossible query filtering")
    print(f"  Result Count: {len(impossible)}")
    assert len(impossible) == 0, "Failed: Expected empty list for impossible query"

    print("\n[PASS] Structured retrieval passed all 4 test cases.")

if __name__ == "__main__":
    run_retrieval_tests()
