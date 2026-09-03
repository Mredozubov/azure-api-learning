# Brooklyn Weather API

A learning project that collects hourly weather for Brooklyn ZIP code 11234.
It has a public-style website, a JSON API, searchable history, and an automatic
collector.

Local development uses SQLite. The production draft uses Azure Functions and
Azure Table Storage. Nothing in this repository creates Azure resources until
you choose to run the deployment commands.

Read [LEARNING_GUIDE.md](LEARNING_GUIDE.md) for a plain-English explanation of
how every part connects.

## Run it locally

You need Python 3.11 or newer. From this folder, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Use terminal 1 for the website:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

Use terminal 2 for automatic collection:

```bash
source .venv/bin/activate
python -m app.scheduler
```

The scheduler collects at the start of every UTC hour. For a quick local demo,
replace the last command with:

```bash
python -m app.scheduler --interval-seconds 10
```

The short interval is only for testing. Stop either program with `Ctrl+C`.

Open these pages:

- Website: <http://127.0.0.1:8000/>
- History: <http://127.0.0.1:8000/history>
- API documentation: <http://127.0.0.1:8000/docs>
- Health check: <http://127.0.0.1:8000/health>

Website times use New York local time, displaying EST or EDT correctly for the
date. History has one search field for dates, times, conditions, temperatures,
humidity, wind, UV, AQI, ZIP code, and provider. API Docs includes a link back
to the current-weather page. The home page also charts the most recent 24 hours
of temperature and labels UV/AQI levels with clear colors.

The weather source is [Open-Meteo](https://open-meteo.com/). The app stores
weather, UV index, and U.S. air-quality index. Pollen is deferred because the
current free provider does not supply it for this location.

## Run one collection manually

```bash
python -m app.collector
```

The local `weather.db` file is created automatically and is ignored by Git.
Collecting the same observed hour again updates that hour instead of adding a
duplicate.

## Test the Azure timer locally with Azurite

Azurite acts like Azure Storage on this computer and uses no Azure credits.
Create the ignored local settings file once:

```bash
cp local.settings.json.example local.settings.json
```

Start Azurite in terminal 1:

```bash
azurite --silent --location /tmp/brooklyn-weather-azurite
```

Start Azure Functions in terminal 2:

```bash
source .venv/bin/activate
func start
```

The example schedule runs every five seconds so you can watch it work. Stop
both programs with `Ctrl+C` after one or two successful runs. Azure production
uses the hourly schedule stored in `infra/main.bicep`.

## Run the tests

```bash
python -m pytest
```

Tests use temporary data and fake provider responses. They do not contact Azure.

## Main project files

```text
app/main.py                 website and API routes
app/collector.py            fetches and saves one report
app/scheduler.py            runs the collector hourly
app/storage.py              chooses SQLite or Azure Table Storage
app/database.py             local SQLite storage
app/azure_table_store.py    future Azure storage
app/templates/              website pages
function_app.py             future Azure HTTP and timer entry points
infra/                      future Azure infrastructure definitions
tests/                      automated checks
```

Configuration examples are in `.env.example` and
`local.settings.json.example`. Never put secrets into committed files.

## Current status

Local collection, scheduling, failure recovery, logging, website display,
history pagination, environment configuration, and tests are implemented. The
Azure code and infrastructure are drafts. The Bicep files compile successfully,
and the Functions HTTP routes run locally. Nothing has been deployed to Azure.

The Azure timer has been tested locally with Azurite. The next Azure step is
signing in and generating a deployment preview. Signing in or creating
resources requires your approval; neither happens during normal local work.
