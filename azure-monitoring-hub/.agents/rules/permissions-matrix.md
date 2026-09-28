# Matriz de Permissões — Azure Monitoring Hub

## Objetivo

Definir quais capacidades cada agente pode utilizar no projeto, seguindo Least Privilege e segregação de responsabilidades.

| Capacidade | PO | Cloud Architect | Security | Cloud DevOps | QA |
|---|---|---|---|---|---|
| Ler documentação | Sim | Sim | Sim | Sim | Sim |
| Criar documentação | Sim | Sim | Sim | Sim | Sim |
| Alterar Terraform | Não | Não | Não | Sim | Não |
| terraform fmt | Não | Não | Não | Sim | Não |
| terraform validate | Não | Não | Não | Sim | Sim |
| terraform plan | Não | Não | Não | Sim | Leitura |
| terraform apply | Não | Não | Não | Somente com aprovação humana | Não |
| terraform destroy | Não | Não | Não | Somente com autorização humana explícita | Não |
| Azure CLI leitura | Não | Opcional | Opcional | Sim | Sim |
| Azure CLI escrita | Não | Não | Não | Evitar; utilizar Terraform | Não |
| Alterar RBAC | Não | Não | Não | Não | Não |
| Criar credenciais | Não | Não | Não | Não | Não |
| Ler valores de secrets | Não | Não | Não | Não por padrão | Não |
| Acesso fora do RG | Não | Não | Não | Não | Não |

## Escopo Azure

O único Resource Group autorizado para operações de escrita é:

`rg-monhub-dev-brs`

Identidade de automação:

`app-monhub-iac-dev`

Role:

`Contributor`

Scope:

`rg-monhub-dev-brs`

## Aprovação humana

As seguintes operações exigem intervenção humana:

- terraform apply
- terraform destroy
- alterações de RBAC
- criação ou alteração de credenciais
- ampliação de permissões
- operações destrutivas
- alterações fora do escopo previamente aprovado

## Regra de autenticação

Credenciais não deverão ser armazenadas nos arquivos JSON dos agentes.

A autenticação deverá ocorrer fora da definição dos agentes.

Nenhum arquivo em `.agents/` deverá conter:

- Client Secret
- Password
- Access Token
- Refresh Token
- VPN PSK
- Private Key

## Regra de execução

Possuir capacidade técnica para executar um comando não representa autorização para executá-lo.

Os agentes deverão respeitar simultaneamente:

1. RBAC do Azure;
2. SECURITY.md;
3. security-rules.md;
4. esta matriz de permissões;
5. aprovação humana quando exigida.