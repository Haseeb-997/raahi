import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from logic.matcher import get_recommendations, PROGRAM_FAMILY

def validate(label, recs):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    if not recs:
        print("  No results.")
        return
    for r in recs:
        over = " [OVER BUDGET]" if r.get("budget_over") else ""
        print(f"\n  #{r['rank']} [{r['total_score']:3d}pts] {r['university_short']} | "
              f"{r['program_name']} | {r['city']} | "
              f"PKR {r['annual_fee_pkr']:,}{over}")
        print(f"         Adm={r['admission_label']}  Bud={r['budget_label']}  "
              f"Pers={r['personality_score']}  City={r['city_score']}")
        for w in r["why_list"]:
            print(f"         WHY:  {w}")
        for risk in r["risk_list"]:
            print(f"         RISK: {risk}")

    unis = [r["university_short"] for r in recs]
    fams = [PROGRAM_FAMILY.get(r["program_name"], "other") for r in recs]
    has_strong = any(r["admission_label"] == "Strong Match" for r in recs)
    has_budget = any(not r.get("budget_over") for r in recs)

    print(f"\n  RULES:")
    print(f"    [1] Uni caps (max 2): { {u: unis.count(u) for u in set(unis)} }")
    print(f"    [2] Has Strong Match:  {has_strong}")
    print(f"    [3] Families:          {fams}")
    print(f"    [4] Has within-budget: {has_budget}")


# Profile A: CS leaning student, Lahore/Islamabad, 250k
validate("Profile A | 80% FSc | 250k | Lahore+Islamabad | CS-leaning",
    get_recommendations(
        fsc_percentage=80, annual_budget=250_000,
        preferred_cities=["Lahore", "Islamabad"], gender="Male",
        personality_scores={
            "CS":9,"SE":6,"AI":4,"Data":3,
            "Elec":2,"Mech":0,"Civil":0,
            "BBA":0,"Fin":0,"Med":0,"Pharma":0,"Psych":0,
        },
    )
)

# Profile B: Bio student, Karachi, tight 100k budget
validate("Profile B | 75% FSc | 100k | Karachi | Med/Pharma-leaning",
    get_recommendations(
        fsc_percentage=75, annual_budget=100_000,
        preferred_cities=["Karachi"], gender="Female",
        personality_scores={
            "CS":0,"SE":0,"AI":0,"Data":1,
            "Elec":0,"Mech":0,"Civil":0,
            "BBA":0,"Fin":0,"Med":6,"Pharma":5,"Psych":3,
        },
    )
)
