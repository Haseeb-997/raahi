import json

with open("data/fields.json", encoding="utf-8") as f:
    d = json.load(f)

REQUIRED = [
    "salary_min_pkr", "salary_max_pkr", "demand", "saturation",
    "growth_outlook", "market_trend", "top_employers_pakistan",
    "years_to_first_job", "jobs_after_3_years",
    "reality_note", "saturation_note", "remote_work_possible",
]

print(f"Fields in file: {len(d)}\n")
all_ok = True
for name, entry in d.items():
    missing = [k for k in REQUIRED if k not in entry]
    if missing:
        print(f"  MISSING in {name}: {missing}")
        all_ok = False
    else:
        ytj    = entry["years_to_first_job"]
        remote = entry["remote_work_possible"]
        emp    = entry["top_employers_pakistan"][0]
        print(f"  OK  {name:<30}  job={ytj:>2}mo  remote={str(remote):<5}  top_employer={emp}")

print()
print("All fields complete." if all_ok else "ERRORS FOUND.")
