# HelpMap — Community Resource Navigation Platform

HelpMap is a civic-technology project designed to make public and nonprofit community resources easier to discover through a simple geospatial interface.

The project began as a Cook County prototype and is being developed as a scalable resource-navigation platform connecting users with services such as food assistance, healthcare, housing, legal aid, employment support, workforce training, and other community resources.

## Project Status

**Active development / functional prototype**

The current pilot includes a curated set of real community resources in northwest Cook County, Illinois. The project is being expanded toward verified multi-category data ingestion, moderation, and scalable resource discovery.

## Current Features

- Interactive geospatial resource map
- ZIP-code and resource-name search
- Category-based resource filtering
- Individual map markers and resource details
- Responsive browser-based interface
- Structured resource data
- FastAPI-based backend architecture
- SQLite data storage
- Draft/publish administrative moderation workflow
- Authenticated development write operations
- Programmatic bulk-ingestion testing

## Technology Stack

### Frontend
- HTML5
- CSS3
- JavaScript
- Leaflet

### Backend
- Python
- FastAPI
- Uvicorn

### Data
- SQLite
- JSON / CSV ingestion workflows

## Architecture

HelpMap is being developed around a separation between public resource discovery and controlled data ingestion.

Planned data workflow:

`Public / nonprofit data sources → Collection → Normalization → Geocoding → Deduplication → Verification → Human moderation → Publication → Periodic re-check`

This approach is intended to prevent automatically collected information from being published directly to users without review.

## Data Quality

The project is being designed to support:

- Source provenance
- Verification status
- Last-verified timestamps
- Duplicate detection
- Human review before publication
- Periodic resource re-validation

Automated collection and parsing are development objectives. Automatically discovered records are not intended to become public resources without verification.

## Repository Structure

```text
app/                    Backend application components
web/helpmap/            Public HelpMap interface
web/helpmap/data/       Pilot resource data
main.py                 FastAPI application entry point
mass_upload.py          Development bulk-ingestion utility
requirements.txt        Python dependencies 
```


## Local Development

Clone the repository and create a Python virtual environment:

```powershell
git clone https://github.com/andyvkon/edu-grants.git
cd edu-grants

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000

```

Then open the HelpMap interface locally through the development server.

## Development Roadmap

Current development priorities include:

1. Expanding verified resource categories
2. Building a source-aware parser and ingestion pipeline
3. Improving normalization and duplicate detection
4. Adding verification metadata and periodic re-checks
5. Strengthening production authentication and configuration
6. Expanding employment, workforce-training, ESL, and self-sufficiency resources
7. Preparing the platform for public pilot deployment
8. Measuring navigation efficiency and data quality during pilot testing

## Development and Testing Notice

This repository contains an actively developed prototype.

Some scripts and records are used specifically for development, API testing, and scalability testing. Simulated test records are not represented as verified community resources.

Production security, deployment infrastructure, automated verification, and nationwide data coverage remain under development.

## Developer

**Andrii Volivach**  
Computer Engineering / Civic Technology

HelpMap combines software engineering with practical experience in community-resource navigation and public-service environments.

The project is being developed as a free civic-technology resource-navigation platform with an emphasis on accessibility, data integrity, workforce participation, and economic self-sufficiency.

