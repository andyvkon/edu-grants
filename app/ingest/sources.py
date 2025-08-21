# app/ingest/sources.py
from __future__ import annotations
import requests, csv, io
from bs4 import BeautifulSoup
from dateutil import parser as dtp

from .common import clean_text, upsert_many

UA = {"User-Agent": "Mozilla/5.0 (compatible; EduGrantsBot/1.0; +http://localhost)"}

# ---------- Fallback demo ----------
DEMO_COURSES = [
    {
        "title": "Intro to Web Development",
        "provider": "City Colleges of Chicago",
        "link": "https://www.ccc.edu/",
        "mode": "In-person/Online",
        "location": "Chicago, IL",
        "category": "IT",
        "tags": "ccc,free,training"
    },
    {
        "title": "Python for Data",
        "provider": "City Colleges of Chicago",
        "link": "https://www.ccc.edu/",
        "mode": "Online",
        "location": "Chicago, IL",
        "category": "Data/AI",
        "tags": "ccc,free,python"
    },
    {
        "title": "Cybersecurity Basics",
        "provider": "City Colleges of Chicago",
        "link": "https://www.ccc.edu/",
        "mode": "In-person",
        "location": "Chicago, IL",
        "category": "Security",
        "tags": "ccc,career"
    },
]

DEMO_NPOS = [
    {"name":"Code for Chicago","service":"Civic tech, meetups","link":"https://chihacknight.org","location":"Chicago, IL","tags":"meetup,civic"},
    {"name":"i.c.stars","service":"Tech training for underserved","link":"https://www.icstars.org","location":"Chicago, IL","tags":"bootcamp,underserved"},
    {"name":"Blue1647","service":"Community tech center","link":"https://blue1647.com","location":"Chicago, IL","tags":"community,tech"},
]

# ---------- Source 1: City Colleges (robust with fallback) ----------
def fetch_ccc_courses() -> dict:
    """
    Пытаемся распарсить публичную страницу. Если не вышло — используем DEMO_COURSES.
    """
    inserted = updated = 0
    try:
        url = "https://www.ccc.edu/academic-programs"
        html = requests.get(url, headers=UA, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")
        items = []
        # разные резервные селекторы
        for card in soup.select(".program-card, .program-card__content, .card"):
            text = clean_text(card.get_text(" ", strip=True))
            if not text:
                continue
            title = text[:120]
            items.append({
                "title": title,
                "provider": "City Colleges of Chicago",
                "link": url,
                "mode": "In-person/Online",
                "location": "Chicago, IL",
                "category": "IT/General",
                "tags": "ccc,free,training"
            })
            if len(items) >= 30:
                break
        if not items:
            items = DEMO_COURSES  # fallback
        res = upsert_many(
            table="courses",
            rows=items,
            key_fields=["title","provider"],
            all_fields=["title","provider","link","mode","location","category","tags"]
        )
        inserted, updated = res["inserted"], res["updated"]
    except Exception:
        # жёсткий fallback на демо
        res = upsert_many(
            table="courses",
            rows=DEMO_COURSES,
            key_fields=["title","provider"],
            all_fields=["title","provider","link","mode","location","category","tags"]
        )
        inserted, updated = res["inserted"], res["updated"]
    return {"inserted": inserted, "updated": updated, "fallback": (inserted>0 and updated==0)}

# ---------- Source 2: Grants from CSV URL ----------
def fetch_grants_from_csv(csv_url: str) -> dict:
    """
    CSV-URL с колонками: title,description,link,location,deadline,tags.
    """
    resp = requests.get(csv_url, headers=UA, timeout=30)
    resp.raise_for_status()
    f = io.StringIO(resp.text)
    reader = csv.DictReader(f)
    rows = []
    for r in reader:
        rows.append({
            "title": clean_text(r.get("title")),
            "description": clean_text(r.get("description")),
            "link": r.get("link",""),
            "location": r.get("location",""),
            "deadline": clean_text(r.get("deadline")),
            "tags": clean_text(r.get("tags")),
        })
    return upsert_many(
        "grants", rows,
        key_fields=["title","location"],
        all_fields=["title","description","link","location","deadline","tags"]
    )

# ---------- Source 3: Nonprofits demo ----------
def fetch_nonprofits_demo() -> dict:
    return upsert_many(
        "nonprofits", DEMO_NPOS,
        key_fields=["name","location"],
        all_fields=["name","service","link","location","tags"]
    )
