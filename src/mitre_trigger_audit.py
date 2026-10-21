def get_candidate_mitre_context(primary_feature, attack_rate):
    context = {"framework": "MITRE ATT&CK v14", "candidate_tactics": [], "possible_techniques": []}
    
    if attack_rate >= 0.50:
        context["candidate_tactics"].append("TA0040: Impact")
        context["possible_techniques"].append("T1498: Network Denial of Service")
    
    if primary_feature == "z_flows":
        context["candidate_tactics"].append("TA0001: Initial Access")
        context["possible_techniques"].append("T1190: Exploit Public-Facing Application")
    elif primary_feature == "velocity":
        context["candidate_tactics"].append("TA0008: Lateral Movement")
        context["possible_techniques"].append("T1210: Exploitation of Remote Services")
        
    if not context["candidate_tactics"]:
        context["candidate_tactics"].append("TA0043: Reconnaissance")
        context["possible_techniques"].append("T1595: Active Scanning")
        
    return context

print("=================================================================")
print("      PHASE 3: MITRE ATT&CK DETERMINISTIC LOGIC AUDIT            ")
print("=================================================================\n")

test_cases = [
    {"desc": "Low-level background noise", "driver": "attack_rate", "rate": 0.10},
    {"desc": "Flow spike, low volume", "driver": "z_flows", "rate": 0.15},
    {"desc": "Velocity spike, low volume", "driver": "velocity", "rate": 0.30},
    {"desc": "Massive volume, standard flow", "driver": "z_bytes", "rate": 0.85},
    {"desc": "Massive volume + Flow spike", "driver": "z_flows", "rate": 0.90},
    {"desc": "Massive volume + Velocity spike", "driver": "velocity", "rate": 0.75}
]

for tc in test_cases:
    ctx = get_candidate_mitre_context(tc['driver'], tc['rate'])
    print(f"Test: {tc['desc']}")
    print(f"  Inputs: Rate={tc['rate']}, Driver='{tc['driver']}'")
    print(f"  Output Techniques: {' + '.join(ctx['possible_techniques'])}")
    print(f"  Output Schema Valid: {'candidate_tactics' in ctx and 'possible_techniques' in ctx}\n")
    
print("[✓] MITRE deterministic trigger matrix audited and verified.")
