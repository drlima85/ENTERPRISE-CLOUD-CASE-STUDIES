targetScope = 'resourceGroup'

@description('Nome globalmente único do Storage Account para armazenamento do Terraform State.')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Região Azure onde o Storage Account será provisionado.')
param location string = resourceGroup().location

@description('Tags aplicadas aos recursos de infraestrutura do backend.')
param tags object = {
  Project: 'monhub'
  Environment: 'dev'
  Component: 'tfstate-backend'
  ManagedBy: 'Bicep'
}

@description('Tempo de retenção em dias para o soft delete de blobs.')
@minValue(1)
@maxValue(365)
param blobSoftDeleteRetentionDays int = 7

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    accessTier: 'Hot'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    isVersioningEnabled: true
    deleteRetentionPolicy: {
      enabled: true
      days: blobSoftDeleteRetentionDays
    }
  }
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'tfstate'
  properties: {
    publicAccess: 'None'
  }
}

output storageAccountId string = storageAccount.id
output storageAccountName string = storageAccount.name
output containerName string = container.name
