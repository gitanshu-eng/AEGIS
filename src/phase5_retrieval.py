import math

SCALES  = {"risk": 0.25, "attack_rate": 0.25,
           "duration": math.log(10), "lead": 15.0}
WEIGHTS = {0: 0.3, 1: 0.2, 2: 0.3, 3: 0.2}

class EpisodeMemory:
    def __init__(self):
        self.bank = {}

    def from_memory_obj(self, obj):
        self.bank[obj["memory_id"]] = obj

    def _calculate_similarity_robust(self, ep1, ep2, use=None):
        v1 = ep1["semantic_context"]["kinematic_vector"]
        v2 = ep2["semantic_context"]["kinematic_vector"]
        feature_map = {"risk": 0, "duration": 1, "attack_rate": 2, "lead_time": 3}
        if use:
            active = [feature_map[f] for f in use if f in feature_map]
        else:
            active = [0, 1, 2, 3]
        l1, l2 = v1[3], v2[3]
        if 3 in active and (l1 is None or l2 is None or (l1 == 0 and l2 == 0)):
            active = [i for i in active if i != 3]
        total_active_weight = sum(WEIGHTS[i] for i in active)
        if total_active_weight == 0:
            return {"total_score": 0.0, "sub_scores": {}}
        w = {i: (WEIGHTS[i] / total_active_weight if i in active else 0.0) for i in range(4)}
        risk_sim = 1.0 - min(1.0, abs(v1[0] - v2[0]) / SCALES["risk"]) if w[0] > 0 else 0.0
        if w[1] > 0:
            dur_sim = 1.0 - min(1.0, abs(math.log1p(v1[1]) - math.log1p(v2[1])) / SCALES["duration"])
        else:
            dur_sim = 0.0
        ar_sim = 1.0 - min(1.0, abs(v1[2] - v2[2]) / SCALES["attack_rate"]) if w[2] > 0 else 0.0
        lt_sim = max(0.0, 1.0 - abs(l1 - l2) / SCALES["lead"]) if w[3] > 0 else 0.0
        kin_score = (risk_sim*w[0]) + (dur_sim*w[1]) + (ar_sim*w[2]) + (lt_sim*w[3])
        t1 = set(ep1["structured_metadata"].get("sustained_tactics", []))
        t2 = set(ep2["structured_metadata"].get("sustained_tactics", []))
        if not t1 and not t2:
            mitre_score = 1.0
        elif not t1 or not t2:
            mitre_score = 0.0
        else:
            mitre_score = len(t1 & t2) / len(t1 | t2)
        total_score = (kin_score * 0.7) + (mitre_score * 0.3)
        return {
            "total_score": round(total_score, 10),
            "sub_scores": {
                "risk_sim":         round(risk_sim, 10),
                "attack_rate_sim":  round(ar_sim, 10),
                "log_duration_sim": round(dur_sim, 10),
                "lead_time_sim":    round(lt_sim, 10) if w[3] > 0 else None,
                "mitre_jaccard":    round(mitre_score, 10),
            }
        }

    def query_by_id(self, query_id, exclude_dataset=None, k=5, use=None):
        if query_id not in self.bank:
            raise KeyError(f"Episode ID {query_id} not found.")
        query_ep = self.bank[query_id]
        results  = []
        for ep_id, ep in self.bank.items():
            if ep_id == query_id: continue
            if exclude_dataset and ep["dataset"] == exclude_dataset: continue
            sim_data = self._calculate_similarity_robust(query_ep, ep, use=use)
            results.append({
                "memory_id":           ep_id,
                "dataset":             ep["dataset"],
                "similarity_score":    sim_data["total_score"],
                "sub_scores":          sim_data["sub_scores"],
                "structured_metadata": ep["structured_metadata"],
            })
        results.sort(key=lambda x: (-x["similarity_score"], x["memory_id"]))
        return results[:k]
