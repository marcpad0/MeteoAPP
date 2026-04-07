# MeteoAPP

MeteoAPP is a simple weather web app built with FastAPI, SQLite, and a static HTML frontend.

Users can:
- search for the current weather of a city
- view the next days forecast
- create an account and log in
- save favorite cities
- remove cities from favorites

## Requirements

- Python 3.10 or newer
- Internet connection for weather data

## Install

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

## Run the project

```bash
python main.py
```

Then open:

```text
http://127.0.0.1:8000
```

## Project structure

- `main.py` - FastAPI app and API routes
- `database.py` - database connection
- `user_class.py` - database models
- `schemas.py` - request and response schemas
- `static/index.html` - frontend interface

## Notes

- The SQLite database file `app.db` is created automatically when the app starts.
- Weather data is fetched from Open-Meteo.
