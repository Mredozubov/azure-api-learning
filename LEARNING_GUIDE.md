# How the Brooklyn Weather Project Works

This file explains the project in simple words. Read it from top to bottom once.
Then keep it open while looking at the code.

## The whole idea

Once every hour, the app asks Open-Meteo for Brooklyn weather. It saves the
answer. A website and API read the saved answers.

```text
Open-Meteo -> collector -> database -> FastAPI -> browser
                  ^
                  |
              scheduler
```

The arrow means “sends data to.”

## What each word means

An **API** is a way for two programs to talk. Our API returns weather as JSON.

An **endpoint** is one API address, such as `/api/weather/latest`.

**JSON** is plain text arranged as names and values. For example:

```json
{"temperature_f": 72.4, "condition": "Partly cloudy"}
```

A **database** keeps data after the Python program stops.

A **scheduler** starts work at a chosen time. Ours starts the collector hourly.

A **server** waits for requests. FastAPI is our Python web server application.

A **test** runs code with known inputs and checks the result automatically.

An **environment variable** is a setting kept outside the code. This lets local
and Azure versions use different settings without changing Python files.

**Serverless** means Azure starts and runs our code when it is needed. We do not
manage a full-time server.

**Managed Identity** lets the Azure Function prove who it is to Azure Storage.
It avoids placing a storage password in the code.

**Bicep** is a text description of Azure resources. Azure reads it and creates
the same setup each time.

## What happens each hour locally

`app/scheduler.py` waits until the start of the hour. It starts
`app/collector.py`. The collector asks `app/weather_client.py` for current
weather. `app/models.py` checks that the returned fields have the expected
types. `app/storage.py` sends the report to `app/database.py`, which writes it
to `weather.db`.

Only one collector run is allowed at a time. If Open-Meteo fails, the error is
written as a JSON log and the scheduler stays alive. It tries again at the next
scheduled time.

## What happens when somebody opens the website

The browser sends a request to FastAPI. A route in `app/main.py` receives it.
The route asks `app/storage.py` for data. Local storage reads SQLite. FastAPI
puts the data into an HTML template from `app/templates/` and sends the finished
page to the browser.

The home page reads the newest report and shows how long ago it was updated.
The history page reads a selected date range. It returns 25 reports at a time,
so a large search is split into pages.

## Why storage has two implementations

The rest of the app should not care where reports live. It asks the same four
questions: initialize, save, get latest, and get history.

Locally, `WEATHER_STORAGE_BACKEND=sqlite` selects `app/database.py`. It is free,
simple, and works without an Azure account.

In production, `WEATHER_STORAGE_BACKEND=azure_table` selects
`app/azure_table_store.py`. Azure Table Storage is shared and permanent even
when a serverless Function stops.

This separation lets us learn locally without paying, then change storage with
a setting instead of rewriting the website.

## Local version and finished Azure version

```text
LOCAL                              AZURE
Your terminal runs FastAPI         HTTP trigger runs FastAPI
APScheduler starts hourly work     Timer trigger starts hourly work
SQLite stores reports              Azure Table Storage stores reports
Terminal shows JSON logs           Application Insights stores logs
Settings come from your shell      Function App holds settings
```

`function_app.py` connects FastAPI to an Azure HTTP trigger and the collector to
an Azure timer trigger. The timer uses Azure's schedule monitor, which helps
avoid duplicate timer work and records scheduled runs.

The files in `infra/` describe the Function App, storage, monitoring, and access
permissions. The Bicep compiler now validates their syntax. A signed-in Azure
deployment preview is still needed to check them against a real subscription.

## How to run and observe it

Start the website in terminal 1:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

Start a fast demonstration in terminal 2:

```bash
source .venv/bin/activate
python -m app.scheduler --interval-seconds 10
```

Open <http://127.0.0.1:8000/> and refresh after a collection. Open
<http://127.0.0.1:8000/history> to see reports build up. Watch terminal 2 for
one JSON success or failure log per attempt. Stop both terminals with `Ctrl+C`.

For real local hourly operation, run `python -m app.scheduler` without the short
interval.

## How to learn from the tests

Run `python -m pytest`. Each file in `tests/` checks one part of the app.

Start with `tests/test_scheduler.py`. It shows the hourly schedule, the
one-at-a-time rule, and recovery after an error. Next read
`tests/test_main.py`; it shows what a browser or API user receives. Finally read
`tests/test_azure_table_store.py`; it shows that the Azure storage code behaves
like the local storage code without using a real Azure account.

## Videos to watch, in this order

1. [Python FastAPI Tutorial, Part 1](https://www.youtube.com/watch?v=7AMjmCTumuo) — see how routes become a website and REST API.
2. [Get started with Azure Functions](https://learn.microsoft.com/en-us/shows/azure/get-started-azure-functions) — learn triggers and serverless execution.
3. [Get started with Azure Storage](https://learn.microsoft.com/en-us/shows/azure/get-started-azure-storage) — learn blobs, tables, files, and queues.
4. [Build your first Bicep template](https://learn.microsoft.com/en-us/shows/learn-live/use-bicep-deploy-azure-infrastructure-as-code-ep02-build-first-bicep-template) — learn how the `infra/` files describe Azure.

Do not try to memorize them. After each video, find the matching file in this
project and explain its job in one sentence.

## Expected Azure cost

The timer runs about 730 times in a 30-day month. Website visits also count as
Function executions. Azure Flex Consumption currently includes 250,000
on-demand executions and 100,000 GB-seconds per paid consumption subscription
each month. With no always-ready instances, light portfolio traffic should stay
inside that compute grant.

One report per hour is only 8,760 history rows per year. Table storage and its
small number of read/write operations should cost pennies. Low-volume logs are
also expected to remain inside Azure Monitor's first 5 GB per billing account
for Analytics Logs.

The practical estimate for this small portfolio app is **$0 to $1 USD per
month**, assuming light traffic and that the subscription qualifies for the
free grants. This is an estimate, not a guarantee. Traffic spikes, verbose
logging, extra apps sharing the grants, networking, or changed Azure prices can
raise it. Before deployment we will use the signed-in pricing calculator for
the exact subscription and East US 2 prices.

Sources: [Azure Functions pricing](https://azure.microsoft.com/en-us/pricing/details/functions/),
[Azure Table Storage pricing](https://azure.microsoft.com/en-us/pricing/details/storage/tables/),
and [Azure Monitor pricing](https://azure.microsoft.com/en-us/pricing/details/monitor/).

## What is finished and what comes next

Finished locally: weather collection, SQLite storage, website, API, history,
pagination, last-updated display, hourly scheduler, overlap protection,
structured logs, failure recovery, environment settings, and automated tests.

Prepared but not deployed: Azure Table Storage code, Azure Functions HTTP/timer
entry points, compiled Bicep resources, managed identity permissions,
monitoring limits, and removal notes. The Functions HTTP routes have also been
run locally through Azure Functions Core Tools.

The next major step needs your decision: install Azure CLI and Azure Functions
Core Tools, validate the Bicep draft, and run a read-only deployment preview.
After we review that preview and the live price estimate together, you can
separately approve creating resources.
