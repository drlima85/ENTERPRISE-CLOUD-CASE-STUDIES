using '../main.bicep'

param storageAccountName = 'stmonhubtfstatedevbrs'
param location = 'brazilsouth'
param tags = {
  Project: 'monhub'
  Environment: 'dev'
  Component: 'tfstate-backend'
  ManagedBy: 'Bicep'
}
param blobSoftDeleteRetentionDays = 7
