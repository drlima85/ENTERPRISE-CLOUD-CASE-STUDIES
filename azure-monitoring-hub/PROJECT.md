# Azure Monitoring Hub

## 1. Visão Geral

O Azure Monitoring Hub é um case study de arquitetura Azure inspirado em um cenário corporativo real de uma ferramenta de monitoração LATAM com coletores no Azure, totalmente anonimizado e reconstruído para fins de laboratório, estudo e portfólio.

O projeto implementará uma plataforma de monitoração, centralizada para hospedar collectors de monitoramento dedicados a diferentes clientes, utilizando Microsoft Azure, Terraform e automação orientada por agentes de IA.

Cada cliente possuirá seu próprio collector, mantendo isolamento lógico, conectividade privada e controle de acesso.

---

## 2. Objetivos

- Construir uma arquitetura multi-customer no Microsoft Azure.
- Provisionar a infraestrutura utilizando Terraform.
- Automatizar o onboarding de novos clientes.
- Implementar conectividade privada entre Azure e redes remotas.
- Aplicar princípios de segurança, governança e menor privilégio.
- Evitar exposição direta dos collectors à Internet.
- Validar conflitos e sobreposição de redes antes do provisionamento.
- Documentar decisões arquiteturais e procedimentos operacionais.
- Utilizar agentes de IA especializados durante o ciclo de desenvolvimento.
- Manter aprovação humana para operações privilegiadas ou destrutivas.

---

## 3. Arquitetura Conceitual

A solução será composta por recursos compartilhados e recursos dedicados por cliente.

### Recursos compartilhados

- Azure Virtual Network
- Subnet dedicada aos collectors
- GatewaySubnet
- Network Security Group
- Azure Virtual Network Gateway
- Public IP do Virtual Network Gateway

### Recursos por cliente

Cada cliente deverá possuir:

- 1 Windows Server VM 2019 datacenter dedicada para o collector
- 1 Network Interface
- 1 endereço IP privado estático
- 1 Application Security Group dedicado
- 1 Local Network Gateway
- 1 VPN Connection
- Redes remotas específicas do cliente

Os collectors não deverão possuir Public IP.

---

## 4. Conectividade

A comunicação entre Azure e cada cliente será realizada através de VPN Site-to-Site.

Modelo:

Azure Virtual Network Gateway
        |
        +-- VPN Connection Customer A
        |       |
        |       +-- Local Network Gateway A
        |
        +-- VPN Connection Customer B
        |       |
        |       +-- Local Network Gateway B
        |
        +-- VPN Connection Customer C
                |
                +-- Local Network Gateway C

O Azure Virtual Network Gateway será compartilhado.

Cada cliente possuirá seu próprio Local Network Gateway e sua própria VPN Connection.

As conexões deverão utilizar IKEv2.

---

## 5. Endereçamento

O laboratório utilizará endereçamento fictício e independente de qualquer ambiente corporativo real.

Os ranges Azure e os ranges remotos dos clientes não poderão apresentar sobreposição.

A inclusão de um novo cliente deverá incluir validação de overlap antes do provisionamento.

---

## 6. Segurança

Princípios obrigatórios:

- Least Privilege.
- Nenhuma credencial armazenada no código.
- Nenhum secret armazenado no Git.
- Nenhum collector exposto diretamente à Internet.
- Service Principal limitado ao Resource Group do projeto.
- Nenhum agente deverá possuir Owner ou User Access Administrator.
- Terraform Plan deverá preceder qualquer alteração.
- Terraform Apply deverá possuir controle e aprovação humana.
- Terraform Destroy deverá exigir autorização humana explícita.
- Alterações deverão ser rastreáveis.

As regras detalhadas serão mantidas em SECURITY.md.

---

## 7. Infrastructure as Code

Terraform será utilizado como ferramenta principal de Infrastructure as Code.

A implementação deverá ser:

- modular;
- reutilizável;
- parametrizada;
- versionada;
- documentada.

O onboarding de novos clientes não deverá exigir duplicação manual da infraestrutura Terraform.

---

## 8. Agentes de IA

O projeto utilizará agentes especializados:

- Product Owner
- Cloud Architect
- Security Engineer
- Cloud DevOps Engineer
- QA Engineer

Cada agente possuirá responsabilidades e limites claramente definidos.

Nenhum agente deverá receber credenciais permanentes diretamente em seus arquivos de configuração.

---

## 9. Ambiente

Projeto:

monhub

Ambiente inicial:

dev

Região inicial:

Brazil South

Resource Group:

rg-monhub-dev-brs

Identidade de automação:

app-monhub-iac-dev

A identidade de automação possuirá Contributor exclusivamente no Resource Group do projeto.

---

## 10. Entregáveis

O projeto deverá produzir:

- Arquitetura documentada
- Diagrama da solução
- Terraform modular
- Regras de segurança
- Modelo de agentes
- Documentação de naming convention
- ADRs
- Runbooks
- Scripts de validação
- Evidências do laboratório
- Pipeline de CI/CD
- README final para apresentação do case