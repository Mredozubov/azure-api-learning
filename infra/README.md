# Azure infrastructure

This folder is the repeatable description of the deployed Azure resources.

`main.bicep` prepares one resource group, one Flex Consumption Function App,
one Storage Account and weather table, Application Insights, Log Analytics,
and the Managed Identity permissions needed to connect them.

Cost controls represented here are 512 MB function instances, no always-ready
instance, Standard LRS storage, 30-day log retention, 5% Application Insights
sampling, and one resource group that can remove the whole project together.

The expected cost for light portfolio traffic is roughly $0 to $1 USD per
month, but this is not a guarantee. The assumptions and official pricing links
are explained in `../LEARNING_GUIDE.md`. We will calculate a subscription- and
region-specific estimate before creating anything.

The production deployment is in `northcentralus` and is contained in
`rg-brooklyn-weather`. Its website is
<https://func-brooklyn-weather-kscgen6i.azurewebsites.net/>.

To preview a future infrastructure change without applying it:

```bash
az deployment sub what-if --location northcentralus \
  --template-file infra/main.bicep --parameters infra/main.bicepparam
```

After approval, apply infrastructure and publish code with:

```bash
az deployment sub create --name brooklyn-weather-production \
  --location northcentralus --template-file infra/main.bicep \
  --parameters infra/main.bicepparam
func azure functionapp publish func-brooklyn-weather-kscgen6i --python
```

In the Azure portal, open **Resource groups > rg-brooklyn-weather** to see the
resources. Open **Cost Management > Cost analysis**, filter to that resource
group, and group by resource to inspect actual charges.

To remove the project later, first save any desired Table data, verify the exact
resource group name, and then delete `rg-brooklyn-weather`. That removes the
website, table data, logs, identity permissions, and settings together. The
subscription-level budget named `brooklyn-weather-monthly` must be deleted
separately.
