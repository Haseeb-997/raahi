import sys
sys.path.insert(0, ".")
from logic.scorer import score_universities

results = score_universities(
    fsc_percentage=80,
    annual_budget=250000,
    preferred_cities=["Lahore", "Islamabad"],
    gender="Male",
    personality_scores={
        "CS": 9, "SE": 6, "AI": 4, "Data": 2,
        "Elec": 2, "Mech": 0, "Civil": 0, "BBA": 0,
        "Fin": 0, "Med": 0, "Pharma": 0, "Psych": 0,
    },
    top_n=5,
)

print(f"Results returned: {len(results)}")
for r in results:
    score     = r["total_score"]
    uni       = r["university_short"]
    prog      = r["program_name"]
    city      = r["city"]
    fee       = r["annual_fee_pkr"]
    adm       = r["admission_label"]
    bud       = r["budget_label"]
    pers      = r["personality_score"]
    print(f"  [{score:3d}] {uni:<12} {prog:<25} | {city:<12} | PKR {fee:,} | {adm} | {bud} | pers={pers}")
