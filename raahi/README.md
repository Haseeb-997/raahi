# 🧭 Raahi — Find Your Realistic University Path

**Raahi** helps Pakistani students cut through the noise and find the right university and degree — based on their FSc percentage, budget, city preference, and a short personality quiz.

> Live Demo: [Coming Soon — deploy on Streamlit Cloud](https://share.streamlit.io)

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-username/raahi.git
cd raahi

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app opens at **http://localhost:8501** automatically.

---

## How It Works

| Step | What happens |
|---|---|
| **Page 1 — Profile** | Student enters FSc %, home city, annual budget, and preferred study cities |
| **Page 2 — Quiz** | 6 personality questions map interests to field scores (CS, AI, Med, etc.) |
| **Page 3 — Results** | Raahi scores every university × program combination and shows the top 3 picks with admission status, budget fit, salary outlook, and honest reality notes |

### Scoring breakdown (max 100 pts per option)
- **Admission fit** — 0–30 pts (merit cutoff match)
- **Budget fit** — 0–25 pts (annual fee vs stated budget)
- **Personality fit** — 0–30 pts (quiz field scores, normalised)
- **Location fit** — 0–15 pts (preferred city match)

---

## Project Structure

```
raahi/
├── app.py                        # Streamlit entry point (3-page flow)
├── requirements.txt
├── .streamlit/
│   └── config.toml               # Dark theme + teal accent
├── data/
│   ├── universities.csv          # 90+ university × program rows
│   └── fields.json               # Salary, demand & career data for 12 fields
├── logic/
│   ├── scorer.py                 # Scores every (university, program) combo
│   └── matcher.py                # Picks top 3 with diversity rules
└── components/
    └── result_card.py            # Streamlit card UI for each recommendation
```

---

## Data Sources

- University fees and merit cutoffs: **2023–2024 admissions data** (manually curated from university websites and prospectuses)
- Salary ranges: **Pakistan tech & professional salary surveys 2024**
- Field demand & saturation: Based on **PSEB, HEC, and industry reports**

---

## Roadmap

- [ ] Add 20+ more universities (KPK, Balochistan, AJK)
- [ ] Filter by scholarship availability
- [ ] Add MDCAT score support for medical programs
- [ ] Streamlit Cloud deployment
- [ ] Mobile-responsive layout improvements

---

## Contributing

Pull requests welcome. To add a university, append rows to `data/universities.csv` following the existing column format.

---

*Raahi MVP — built for Pakistani students, by people who understand the admission struggle.*
