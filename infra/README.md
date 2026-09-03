# Azure infrastructure draft

This folder describes the Azure resources but does not create them by itself.

`main.bicep` prepares one resource group, one Flex Consumption Function App,
one Storage Account and weather table, Application Insights, Log Analytics,
and the Managed Identity permissions needed to connect them.

Cost controls already represented here are 512 MB function instances, no
always-ready instance, 30-day log retention, Application Insights sampling,
and one resource group that can remove the whole project together.

The expected cost for light portfolio traffic is roughly $0 to $1 USD per
month, but this is not a guarantee. The assumptions and official pricing links
are explained in `../LEARNING_GUIDE.md`. We will calculate a subscription- and
region-specific estimate before creating anything.

Azure CLI is installed, the Azure for Students subscription is confirmed, and
its policy permits `northcentralus`, which supports Python Flex Consumption.
Before deployment we still must review a successful Bicep preview, calculate
current regional pricing, and obtain explicit approval. To remove the deployed project later, delete the resource group named
`rg-brooklyn-weather`. That removes its website, table data, logs, and settings.
We will first download any data worth keeping, then verify the exact resource
group name, delete it, and confirm that it no longer appears in Azure.
