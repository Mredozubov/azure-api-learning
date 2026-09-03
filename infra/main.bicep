targetScope = 'subscription'

@description('Short name used to label this deployment.')
param environmentName string = 'brooklyn-weather'

@description('Azure region. We will confirm availability and price before deployment.')
param location string = 'northcentralus'

@description('Smallest allowed Flex Consumption memory size.')
@allowed([512, 2048, 4096])
param instanceMemoryMB int = 512

var token = toLower(uniqueString(subscription().id, environmentName, location))
var resourceGroupName = 'rg-${environmentName}'
var storageAccountName = 'st${take(token, 20)}'
var functionAppName = 'func-${environmentName}-${take(token, 8)}'
var deploymentContainerName = 'app-package-${take(token, 8)}'
var tableName = 'weatherreports'
var queueEndpoint = 'https://${storageAccountName}.queue.${environment().suffixes.storage}'
var tableEndpoint = 'https://${storageAccountName}.table.${environment().suffixes.storage}'
var tags = {
  project: 'Brooklyn Weather API'
  environment: 'production'
  managedBy: 'Bicep'
}

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-11-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module logs 'br/public:avm/res/operational-insights/workspace:0.11.1' = {
  name: 'logs'
  scope: resourceGroup
  params: {
    name: 'log-${environmentName}-${take(token, 8)}'
    location: location
    dataRetention: 30
    tags: tags
  }
}

module insights 'br/public:avm/res/insights/component:0.6.0' = {
  name: 'insights'
  scope: resourceGroup
  params: {
    name: 'appi-${environmentName}-${take(token, 8)}'
    location: location
    workspaceResourceId: logs.outputs.resourceId
    disableLocalAuth: true
    tags: tags
  }
}

module storage 'br/public:avm/res/storage/storage-account:0.25.0' = {
  name: 'storage'
  scope: resourceGroup
  params: {
    name: storageAccountName
    location: location
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Enabled'
    blobServices: {
      containers: [{ name: deploymentContainerName }]
    }
    queueServices: {}
    tableServices: {
      tables: [{ name: tableName }]
    }
    tags: tags
  }
}

module plan 'br/public:avm/res/web/serverfarm:0.1.1' = {
  name: 'plan'
  scope: resourceGroup
  params: {
    name: 'plan-${environmentName}-${take(token, 8)}'
    location: location
    reserved: true
    zoneRedundant: false
    sku: {
      name: 'FC1'
      tier: 'FlexConsumption'
    }
    tags: tags
  }
}

module functionApp 'br/public:avm/res/web/site:0.16.0' = {
  name: 'function-app'
  scope: resourceGroup
  params: {
    name: functionAppName
    kind: 'functionapp,linux'
    location: location
    serverFarmResourceId: plan.outputs.resourceId
    managedIdentities: {
      systemAssigned: true
    }
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storage.outputs.primaryBlobEndpoint}${deploymentContainerName}'
          authentication: {
            type: 'SystemAssignedIdentity'
          }
        }
      }
      runtime: {
        name: 'python'
        version: '3.12'
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 40
        instanceMemoryMB: instanceMemoryMB
      }
    }
    siteConfig: {
      alwaysOn: false
    }
    configs: [{
      name: 'appsettings'
      properties: {
        AzureWebJobsStorage__credential: 'managedidentity'
        AzureWebJobsStorage__blobServiceUri: storage.outputs.primaryBlobEndpoint
        AzureWebJobsStorage__queueServiceUri: queueEndpoint
        AzureWebJobsStorage__tableServiceUri: tableEndpoint
        APPLICATIONINSIGHTS_CONNECTION_STRING: insights.outputs.connectionString
        APPLICATIONINSIGHTS_AUTHENTICATION_STRING: 'Authorization=AAD'
        WEATHER_STORAGE_BACKEND: 'azure_table'
        WEATHER_TIMER_SCHEDULE: '0 0 * * * *'
        AZURE_STORAGE_ACCOUNT_URL: tableEndpoint
        AZURE_TABLE_NAME: tableName
        WEATHER_LOCATION_NAME: 'Brooklyn, NY 11234'
        WEATHER_ZIP_CODE: '11234'
        WEATHER_LATITUDE: '40.62'
        WEATHER_LONGITUDE: '-73.92'
        WEATHER_TIMEZONE: 'America/New_York'
      }
    }]
    tags: tags
  }
}

module roles './roles.bicep' = {
  name: 'roles'
  scope: resourceGroup
  params: {
    storageAccountResourceId: storage.outputs.resourceId
    applicationInsightsResourceId: insights.outputs.resourceId
    functionPrincipalId: functionApp.outputs.?systemAssignedMIPrincipalId ?? ''
  }
}

output resourceGroupName string = resourceGroup.name
output functionAppName string = functionAppName
output websiteUrl string = 'https://${functionAppName}.azurewebsites.net'
output storageAccountName string = storageAccountName
