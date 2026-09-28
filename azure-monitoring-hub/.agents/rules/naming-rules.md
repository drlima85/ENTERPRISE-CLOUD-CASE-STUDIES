# Padrão de Nomenclatura — Azure Monitoring Hub

## 1. Objetivo

Todos os recursos do Azure Monitoring Hub deverão seguir uma nomenclatura consistente, previsível e facilmente identificável.

Código do projeto: `monhub`

Ambiente inicial: `dev`

Região inicial:`Brazil South`

Código da região:`brs`

---

## 2. Estrutura geral

Sempre que aplicável: `<tipo>-<identificador>-<ambiente>-<região>`

Exemplo: `vnet-monhub-dev-brs`

Recursos específicos de clientes deverão incluir o identificador fictício do cliente.

Exemplo: `vm-col-cust01-dev-brs`

---

## 3. Recursos compartilhados

Resource Group: `rg-monhub-dev-brs`

Virtual Network: `vnet-monhub-dev-brs`

Subnet de collectors: `snet-collectors-dev-brs`

Gateway Subnet: `GatewaySubnet`

Network Security Group: `nsg-collectors-dev-brs`

Virtual Network Gateway: `vng-monhub-dev-brs`

Public IP do Virtual Network Gateway: `pip-vng-monhub-dev-brs`

---

## 4. Recursos dedicados por cliente

O identificador de cliente deverá utilizar:

`cust01`
`cust02`
`cust03`

Nunca utilizar nomes reais de clientes.

### Collector VM

`vm-col-<cliente>-dev-brs`

Exemplo: `vm-col-cust01-dev-brs`

### Network Interface

`nic-col-<cliente>-dev-brs`

Exemplo:  `nic-col-cust01-dev-brs`

### Application Security Group

`asg-<cliente>-dev-brs`

Exemplo: `asg-cust01-dev-brs`

### Local Network Gateway

`lng-<cliente>-dev-brs`

Exemplo: `lng-cust01-dev-brs`

### VPN Connection

`con-<cliente>-dev-brs`

Exemplo: `con-cust01-dev-brs`

---

## 5. Identidades

App Registration / Service Principal utilizado pela automação: `app-monhub-iac-dev`

Nenhuma identidade deverá utilizar nome de usuário ou nome pessoal.

---

## 6. Terraform

Nomes internos do Terraform deverão ser descritivos e independentes do nome final do recurso Azure.

Exemplos:

`azurerm_virtual_network.main`

`azurerm_network_security_group.collectors`

Recursos por cliente deverão utilizar `for_each` sempre que apropriado.

Exemplo conceitual:

`azurerm_network_interface.collector["cust01"]`

Evitar duplicação manual como:

`collector_customer_a`

`collector_customer_b`

`collector_customer_c`

---

## 7. Tags

Todos os recursos que suportarem tags deverão utilizar, quando aplicável:

`project = "monhub"`

`environment = "dev"`

`managed_by = "terraform"`

`case_study = "azure-monitoring-hub"`

Recursos específicos de cliente poderão adicionar:

`customer = "cust01"`

Nunca utilizar nomes reais de clientes em tags.

---

## 8. Regras obrigatórias

Os nomes deverão:

- utilizar letras minúsculas sempre que suportado pelo recurso;
- evitar espaços;
- evitar caracteres especiais desnecessários;
- utilizar hífen como separador quando suportado;
- permanecer consistentes entre Terraform, Azure e documentação;
- utilizar somente identificadores fictícios para clientes.

Antes de criar um recurso, o agente deverá validar se o nome atende às restrições específicas do serviço Azure.

Caso um serviço Azure não permita o padrão definido neste documento, o agente deverá adaptar o nome preservando o máximo possível da convenção e documentar a exceção.