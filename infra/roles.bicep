param storageAccountResourceId string
param applicationInsightsResourceId string
param functionPrincipalId string

var roles = {
  blobOwner: 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
  queueContributor: '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
  tableContributor: '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
  metricsPublisher: '3913510d-42f4-4e42-8a64-420c390055eb'
}

module blobRole 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.2' = {
  name: 'blob-role'
  params: {
    resourceId: storageAccountResourceId
    roleDefinitionId: roles.blobOwner
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
  }
}

module queueRole 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.2' = {
  name: 'queue-role'
  params: {
    resourceId: storageAccountResourceId
    roleDefinitionId: roles.queueContributor
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
  }
}

module tableRole 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.2' = {
  name: 'table-role'
  params: {
    resourceId: storageAccountResourceId
    roleDefinitionId: roles.tableContributor
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
  }
}

module metricsRole 'br/public:avm/ptn/authorization/resource-role-assignment:0.1.2' = {
  name: 'metrics-role'
  params: {
    resourceId: applicationInsightsResourceId
    roleDefinitionId: roles.metricsPublisher
    principalId: functionPrincipalId
    principalType: 'ServicePrincipal'
  }
}
