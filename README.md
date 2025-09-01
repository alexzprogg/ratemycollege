# ratemycollege

A Flask-based web app that helps University of Toronto students **compare colleges** using both **structured ratings** (food, social life, study space, opportunities, clubs) and **NLP-derived themes** from student comments. The goal is to go beyond unstructured forum threads and provide **clean comparisons, trends over time, and semantic insights**.

> Built for UofT colleges first; architecture is generalizable to other schools.

---

## ✨ Key Features

- **Structured review funnel**: category checkboxes → short free-text → category ratings → auto-generated tags (users can edit/approve).
- **Dynamic averages & rankings**: compute real averages from real reviews (not hard-coded).
- **Trends & hashtags**: “Trending Right Now” on the homepage; top 3 hashtags per college.
- **Side-by-side comparisons**: visualize differences across colleges (e.g., food rating over time, tag distributions).
- **NLP pipeline**: extract themes/keywords, cluster topics, and weight recommendations by user intent.
- **Auth-gated contributions (optional)**: login/registration before submitting reviews.
- **Data quality flags**: warn when a college has limited data (e.g., “Based on few reviews”).

---

## 🗂 Project Structure

ratemycollege/
├─ app/
│ ├─ static/ # CSS/JS/assets
│ ├─ templates/ # home.html, colleges.html, collegeprofile.html, etc.
│ ├─ modules.py # Flask blueprints / wiring (if used)
│ ├─ nlp_utils.py # tokenization, keyword/tag extraction, clustering
│ ├─ recommenderutils.py # ranking logic (weights, similarity, model hooks)
│ └─ init.py # create_app() / Flask factory
├─ data/ # seed data, sample comments (optional)
├─ instance/
│ └─ database.db # SQLite DB (runtime; git-ignored)
├─ init_db.py # initialize the SQLite schema
├─ run.py # dev entrypoint (python run.py)
├─ requirements.txt # Python deps
├─ scrape_reddit.py # experimental data collection (optional)
└─ README.md


---

## 🚀 Quickstart

### 1) Create a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

```
### 2) Install dependencies
```
pip install -r requirements.txt
```

