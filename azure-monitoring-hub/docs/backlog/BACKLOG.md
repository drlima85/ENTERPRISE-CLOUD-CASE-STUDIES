# Product Backlog — Azure Monitoring Hub (`monhub`)

## 1. Visão Geral do Produto

O **Azure Monitoring Hub** (`monhub`) é uma plataforma centralizada de monitoramento multi-customer no Microsoft Azure. A solução hospeda coletores de monitoramento dedicados por cliente sobre uma infraestrutura compartilhada segura, utilizando Terraform e automação orientada por agentes especializados de IA.

Cada cliente atendido dispõe de isolamento de rede, collector dedicado e conectividade privada via VPN Site-to-Site (IKEv2), garantindo estrita confidencialidade e controle de acesso.

---

## 2. Baseline Aprovada do Projeto

As seguintes premissas e requisitos foram aprovados e compõem a fundação do backlog:

1. **Resource Group Pré-existente**: O Resource Group `rg-monhub-dev-brs` é pré-existente e **deve** ser consumido pelo Terraform exclusivamente via `data source` (`azurerm_resource_group`).
2. **Identidade de Automação e RBAC**: A identidade de automação é `app-monhub-iac-dev`, com papel `Contributor` restrito exclusivamente ao escopo de `rg-monhub-dev-brs`. É proibido privilégio Owner/User Access Administrator ou permissão no escopo da Subscription.
3. **Autenticação OIDC**: A autenticação entre GitHub Actions e Azure utiliza Workload Identity Federation (OIDC), já devidamente configurada e validada.
4. **Governança de Execução de IaC**:
   - `terraform apply` exige aprovação humana obrigatória em ambiente protegido do GitHub (`environment approval`).
   - Nenhum agente de IA está autorizado a executar `terraform apply` autonomamente.
5. **Proteção do Terraform State**: O Terraform State deve residir em backend remoto protegido (Azure Blob Storage com RBAC estrito, TLS e criptografia). Considera-se explicitamente que o atributo `sensitive = true` do Terraform **não impede** que valores sensíveis sejam gravados em texto claro dentro do arquivo de estado (`.tfstate`).
6. **Isolamento e Segurança de Collectors**:
   - Collectors devem operar exclusivamente com endereçamento IP privado.
   - É estritamente proibido associar Public IP aos collectors.
7. **Topologia de Rede Híbrida**:
   - O Azure Virtual Network Gateway (VNG) é um recurso centralizado e compartilhado.
   - Cada cliente possui isolamento dedicado composto por: 1 Collector (VM Windows), 1 Application Security Group (ASG), 1 Local Network Gateway (LNG) e 1 VPN Connection Site-to-Site dedicada.
   - A conectividade Site-to-Site utiliza obrigatoriamente protocolo IKEv2.
8. **Prevenção de Conflitos de Rede**: É obrigatória a validação automatizada de sobreposição de blocos CIDR (overlap) antes do provisionamento de qualquer novo cliente.
9. **Definições Pendentes de Sistema Operacional**: A versão exata, imagem oficial e SKU da máquina virtual Windows Server dos collectors ainda **não estão definidos**. Essa definição técnica é de responsabilidade exclusiva do **Cloud Architect**.
10. **Sanitização de Dados**: O repositório e a documentação devem utilizar exclusivamente dados fictícios e sanitizados. Nenhuma informação real de clientes, credenciais, VPN PSKs ou tokens deve ser persistida.

---

## 3. Matriz de Responsabilidades por Agente

| Papel / Agente | Responsabilidade Principal no Backlog | Limites Estritos |
| :--- | :--- | :--- |
| **Product Owner** | Levantamento de requisitos, priorização, critérios de aceite, gestão do backlog. | Escrita restrita a `docs/backlog/`; não executa comandos nem define parâmetros técnicos detalhados. |
| **Cloud Architect** | Arquitetura técnica, topologia, dimensionamento de SKUs, imagem de SO, ADRs. | Não executa mudanças diretas na nuvem. |
| **Security Engineer** | Modelagem de ameaças, guardrails, políticas de segurança, revisão de NSG e secrets. | Sem permissão de escrita de infraestrutura direta; privilégio preferencial de leitura. |
| **Cloud DevOps** | Implementação de módulos Terraform, automação de CI/CD, execução de plan e testes de IaC. | Não executa `apply` ou `destroy` sem aprovação humana; escopo restrito a `rg-monhub-dev-brs`. |
| **QA Engineer** | Testes de conformidade, validação de conectividade, testes de overlap e validação de requisitos. | Acesso somente leitura para auditoria e teste; não altera configurações produtivas. |

---

## 4. Épicos do Projeto

- **EP-01**: Governança, Segurança e Fundação de IaC
- **EP-02**: Conectividade Centralizada e Rede Compartilhada (Shared Networking)
- **EP-03**: Onboarding de Clientes e Conectividade Dedicada (Customer Onboarding)
- **EP-04**: Provisionamento e Configuração de Collectors (Monitoring Infrastructure)
- **EP-05**: Validação Contínua, Testes e Documentação Operacional (Quality & Delivery)

---

## 5. Histórias de Usuário Detalhadas

### EP-01: Governança, Segurança e Fundação de IaC

#### US-01: Configuração do Backend Remoto Seguro do Terraform
- **ID**: `US-01`
- **Prioridade**: Alta (Bloqueante)
- **Agente Responsável**: Cloud DevOps Engineer
- **Objetivo**: Configurar o backend remoto seguro para armazenamento do estado do Terraform, mitigando riscos de exposição de dados sensíveis.
- **Descrição**: Como engenheiro de DevOps, necessito de um backend remoto seguro no Azure Blob Storage para armazenar o `terraform.tfstate`, ciente de que valores definidos como `sensitive = true` (como VPN PSKs) permanecem legíveis no state.
- **Critérios de Aceite**:
  1. O backend remoto deve utilizar Azure Blob Storage com criptografia em repouso e HTTPS obrigatório.
  2. O acesso ao container do estado deve ser restrito via RBAC à identidade de automação (`app-monhub-iac-dev`) e administradores autorizados.
  3. Nenhum arquivo `.tfstate` local ou com segredos pode ser versionado no repositório Git (`.gitignore` atualizado).
  4. O versionamento de blobs deve estar habilitado na Storage Account para auditoria e rollback de estado.
- **Dependências**: Nenhuma.
- **Pendências / Notas Técnicas**:
  - *Cloud Architect / Security Engineer*: Definir se a Storage Account de backend já existe ou se será provisionada externamente à pipeline principal.

---

#### US-02: Consumo do Resource Group Pré-existente via Data Source e Validação de OIDC
- **ID**: `US-02`
- **Prioridade**: Alta (Bloqueante)
- **Agente Responsável**: Cloud DevOps Engineer
- **Objetivo**: Garantir que o Terraform consuma o Resource Group pré-existente e utilize a identidade federada via OIDC.
- **Descrição**: Como Cloud DevOps, preciso integrar o código Terraform ao Resource Group `rg-monhub-dev-brs` através de data source e assegurar que a execução utilize a autenticação federada validada.
- **Critérios de Aceite**:
  1. O Resource Group `rg-monhub-dev-brs` não pode ser declarado como recurso gerenciado (`azurerm_resource_group` comum), mas obrigatoriamente via `data "azurerm_resource_group"`.
  2. A identidade de automação utilizada deve ser exclusivamente `app-monhub-iac-dev`.
  3. A autenticação com o Azure deve utilizar o OIDC configurado no GitHub Actions sem persistência de client secrets estáticos no repositório.
  4. As validações devem confirmar que a automação opera estritamente dentro do Resource Group `rg-monhub-dev-brs`.
- **Dependências**: US-01.
- **Pendências / Notas Técnicas**:
  - Validação OIDC já realizada; pipeline deve referenciar o `client-id`, `tenant-id` e `subscription-id` via variáveis de repositório/secrets do GitHub.

---

#### US-03: Pipeline de CI/CD com Gate de Aprovação Humana Obrigatória
- **ID**: `US-03`
- **Prioridade**: Alta
- **Agente Responsável**: Cloud DevOps Engineer
- **Objetivo**: Implementar pipeline de integração contínua e entrega contínua com bloqueio de execução autônoma para `terraform apply`.
- **Descrição**: Como Product Owner, preciso que qualquer alteração de infraestrutura passe por revisão de plano e aprovação humana explícita antes de ser aplicada, impedindo execuções autônomas de agentes.
- **Critérios de Aceite**:
  1. A pipeline do GitHub Actions deve executar em etapas segregadas: `terraform fmt`, `terraform validate`, `terraform plan`.
  2. O resultado do `terraform plan` deve ser anexado como evidência/comentário no Pull Request.
  3. O job de `terraform apply` deve ser associado a um GitHub Environment com proteção de revisão humana obrigatória.
  4. Nenhum agente de IA ou execução automática de commit pode disparar o `terraform apply` sem a confirmação de um revisor humano no GitHub.
  5. A execução de `terraform destroy` deve ser desabilitada na automação padrão e condicionada a aprovação especial.
- **Dependências**: US-02.
- **Pendências / Notas Técnicas**:
  - *Security Engineer*: Revisar fluxo de aprovação e branch protection rules.

---

### EP-02: Conectividade Centralizada e Rede Compartilhada (Shared Networking)

#### US-04: Provisionamento da Virtual Network Compartilhada e Subnets
- **ID**: `US-04`
- **Prioridade**: Alta
- **Agente Responsável**: Cloud DevOps Engineer
- **Objetivo**: Provisionar a infraestrutura de rede compartilhada da plataforma dentro do Resource Group de desenvolvimento.
- **Descrição**: Como arquiteto/engenheiro de nuvem, necessito de uma VNet centralizada que comporte a subnet dedicada aos collectors e a subnet obrigatória para o gateway de VPN.
- **Critérios de Aceite**:
  1. Criação da Azure Virtual Network no escopo de `rg-monhub-dev-brs` (região Brazil South).
  2. Criação da `GatewaySubnet` dedicada exclusivamente ao Virtual Network Gateway.
  3. Criação de subnet dedicada aos collectors de monitoramento.
  4. Associação de Network Security Group (NSG) base para controle de tráfego na subnet de collectors.
  5. Uso exclusivo de blocos CIDR fictícios/sanitizados definidos pela arquitetura.
- **Dependências**: US-02, US-03.
- **Pendências / Notas Técnicas**:
  - *Cloud Architect*: Definir oficialmente os blocos CIDR da VNet, `GatewaySubnet` e Subnet de Collectors.

---

#### US-05: Provisionamento do Azure Virtual Network Gateway Compartilhado
- **ID**: `US-05`
- **Prioridade**: Alta
- **Agente Responsável**: Cloud DevOps Engineer
- **Objetivo**: Provisionar o Virtual Network Gateway compartilhado para terminação de túneis VPN Site-to-Site de múltiplos clientes.
- **Descrição**: Como engenheiro de rede/nuvem, necessito de um Virtual Network Gateway provisionado na `GatewaySubnet` para receber as conexões VPN dos clientes utilizando protocolo IKEv2.
- **Critérios de Aceite**:
  1. Provisionamento de 1 Azure Virtual Network Gateway do tipo `Vpn` e `RouteBased`.
  2. O VNG deve ser compartilhado entre todos os clientes atendidos pela plataforma.
  3. Provisionamento de Public IP dedicado para o Virtual Network Gateway.
  4. Suporte e configuração para o protocolo IKEv2.
  5. Os coletores não utilizam este Public IP, que é exclusivo do VNG.
- **Dependências**: US-04.
- **Pendências / Notas Técnicas**:
  - *Cloud Architect*: Definir o SKU do VNG (ex.: `VpnGw1`, `VpnGw2`) com base nos requisitos de custo e performance do laboratório.
  - *Security Engineer*: Especificar políticas criptográficas suportadas (IPsec/IKE policies).

---

#### US-06: Validação Automatizada de Sobreposição de Blocos CIDR (Overlap Detection)
- **ID**: `US-06`
- **Prioridade**: Alta
- **Agente Responsável**: Cloud DevOps Engineer / QA Engineer
- **Objetivo**: Desenvolver mecanismo automatizado para detectar e bloquear sobreposições de faixas CIDR locais e remotas.
- **Descrição**: Como Product Owner, exijo que antes da inclusão de novos clientes haja uma verificação automatizada impedindo que a rede remota do cliente conflite com a VNet Azure ou com redes de outros clientes já cadastrados.
- **Critérios de Aceite**:
  1. Script ou validação pré-provisionamento que compare os blocos CIDR solicitados para o novo cliente contra:
     - Bloco da VNet do Azure Monitoring Hub;
     - Blocos de todos os Local Network Gateways já cadastrados de outros clientes.
  2. Caso seja identificada sobreposição parcial ou total, o pipeline deve falhar imediatamente com erro descritivo antes do `terraform plan`.
  3. Suporte para execução via pipeline e em testes de QA locais.
- **Dependências**: US-04.
- **Pendências / Notas Técnicas**:
  - *QA Engineer*: Criar bateria de testes unitários validando casos de sobreposição (overlap exato, sub-rede contida, super-rede abrangente).

---

### EP-03: Onboarding de Clientes e Conectividade Dedicada (Customer Onboarding)

#### US-07: Módulo Parametrizado de Conectividade VPN por Cliente
- **ID**: `US-07`
- **Prioridade**: Alta
- **Agente Responsável**: Cloud DevOps Engineer
- **Objetivo**: Criar módulo reutilizável de Terraform para provisionar Local Network Gateway e VPN Connection dedicados por cliente.
- **Descrição**: Como engenheiro de DevOps, necessito de um módulo padronizado que receba os parâmetros do cliente e configure a terminação VPN Site-to-Site IKEv2 conectada ao VNG compartilhado.
- **Critérios de Aceite**:
  1. O módulo deve provisionar 1 `azurerm_local_network_gateway` dedicado contendo o IP público remoto e os address spaces da rede do cliente.
  2. O módulo deve provisionar 1 `azurerm_virtual_network_gateway_connection` dedicada vinculando o VNG compartilhado ao LNG do cliente.
  3. O protocolo da conexão deve ser fixado em `IKEv2`.
  4. O segredo compartilhado (PSK) não deve estar gravado estaticamente em código claro no Git, sendo injetado via secret de pipeline/variável protegida.
  5. Suporte ao onboarding de múltiplos clientes via estrutura de dados (map/list) sem duplicação de blocos de infraestrutura.
- **Dependências**: US-05, US-06.
- **Pendências / Notas Técnicas**:
  - *Security Engineer*: Definir diretriz de geração/gerenciamento de Pre-Shared Keys sanitizadas para o laboratório.

---

#### US-08: Módulo de Segurança e Segmentação por Cliente (ASG Dedicado)
- **ID**: `US-08`
- **Prioridade**: Média
- **Agente Responsável**: Cloud DevOps Engineer
- **Objetivo**: Provisionar Application Security Group (ASG) exclusivo por cliente para isolamento granular de tráfego no collector.
- **Descrição**: Como arquiteto/engenheiro de segurança, necessito que cada cliente possua seu próprio ASG para que as regras de firewall no NSG da subnet sejam vinculadas individualmente por cliente.
- **Critérios de Aceite**:
  1. Criação de 1 `azurerm_application_security_group` dedicado por cliente.
  2. Criação de regras de NSG que autorizem apenas o fluxo necessário entre o collector do cliente (vinculado ao seu ASG) e os ranges remotos do respectivo LNG.
  3. Bloqueio explícito de tráfego lateral entre collectors de clientes distintos na mesma subnet.
- **Dependências**: US-04, US-07.
- **Pendências / Notas Técnicas**:
  - *Security Engineer*: Especificar as portas e protocolos estritos permitidos para a ferramenta de monitoramento.

---

### EP-04: Provisionamento e Configuração de Collectors (Monitoring Infrastructure)

#### US-09: Definição Arquitetural do Host Windows Server dos Collectors
- **ID**: `US-09`
- **Prioridade**: Alta
- **Agente Responsável**: Cloud Architect
- **Objetivo**: Definir oficialmente a especificação da máquina virtual Windows Server (SKU, imagem, versão e sizing).
- **Descrição**: Como Cloud Architect, necessito formalizar a escolha da versão do sistema operacional Windows Server, a oferta de imagem oficial no Azure Marketplace e o tamanho da VM (`vm_size`/`sku`), equilibrando performance e custo do case.
- **Critérios de Aceite**:
  1. Produção de ADR ou especificação técnica definindo:
     - Versão exata do SO (ex.: Windows Server 2019 Datacenter / 2022 Datacenter Gen2);
     - Imagem (`publisher`, `offer`, `sku`, `version`);
     - Tamanho/SKU da VM no Azure (ex.: `Standard_B2s`, `Standard_D2s_v5`);
     - Tipo de disco gerenciado do SO (ex.: Standard SSD / Premium SSD).
  2. Validação da disponibilidade do SKU e imagem na região `Brazil South`.
  3. Recomendação de parâmetros de hardening e credenciais temporárias sanitizadas.
- **Dependências**: Nenhuma (estudo de arquitetura).
- **Pendências / Notas Técnicas**:
  - *Decisão Pendente*: Item sob responsabilidade exclusiva do **Cloud Architect**. O PO e o DevOps não devem fixar arbitrariamente estes valores antes da definição da arquitetura.

---

#### US-10: Módulo Terraform de Collector Dedicado por Cliente
- **ID**: `US-10`
- **Prioridade**: Alta
- **Agente Responsável**: Cloud DevOps Engineer
- **Objetivo**: Implementar módulo Terraform para provisionamento do collector Windows Server dedicado por cliente, sem exposição à Internet.
- **Descrição**: Como DevOps, necessito de um módulo reutilizável que provisione a VM do collector, garantindo IP privado estático, ausência de Public IP e associação ao ASG do cliente.
- **Critérios de Aceite**:
  1. Provisionamento de 1 Network Interface (NIC) dedicada com IP privado estático alocado na subnet de collectors.
  2. Proibição absoluta de associação de Public IP à NIC ou VM do collector (`public_ip_address_id = null`).
  3. Associação da NIC ao Application Security Group (ASG) exclusivo do cliente (conforme US-08).
  4. Provisionamento da VM Windows Server utilizando rigorosamente os parâmetros de SO e SKU definidos pelo Cloud Architect na US-09.
  5. Senhas de administrador injetadas de forma parametrizada e protegida, sem expor valores reais em código.
- **Dependências**: US-08, US-09.
- **Pendências / Notas Técnicas**:
  - O módulo deve consumir como input as definições de SO/SKU entregues pelo Cloud Architect.

---

### EP-05: Validação Contínua, Testes e Documentação Operacional (Quality & Delivery)

#### US-11: Suíte de Validação e Testes de Conformidade (QA Guardrails)
- **ID**: `US-11`
- **Prioridade**: Média
- **Agente Responsável**: QA Engineer
- **Objetivo**: Desenvolver rotinas automatizadas para validação de conformidade da infraestrutura com as políticas do projeto.
- **Descrição**: Como engenheiro de QA, necessito validar se a infraestrutura provisionada cumpre todos os requisitos de segurança, ausência de IPs públicos em coletores e consistência de IaC.
- **Critérios de Aceite**:
  1. Teste de conformidade verificando que nenhuma VM de collector possui Public IP associado.
  2. Teste verificando que o Resource Group utilizado é unicamente `rg-monhub-dev-brs` e consumido como data source.
  3. Validação de isolamento de rede entre clientes distintos (regras de ASG/NSG).
  4. Teste de regressão para o validador de CIDR overlap (confirmando falha ao injetar ranges colidentes).
- **Dependências**: US-03, US-06, US-10.
- **Pendências / Notas Técnicas**:
  - Implementação via scripts de teste automatizado (ex.: Pester, Python ou Terratest em modo read-only).

---

#### US-12: Documentação de Arquitetura, Runbooks e Sanitização do Case Study
- **ID**: `US-12`
- **Prioridade**: Média
- **Agente Responsável**: Product Owner / Cloud Architect
- **Objetivo**: Consolidar a documentação final do case study, garantindo anonimização total e manuais de onboarding.
- **Descrição**: Como Product Owner, preciso que o repositório disponha de documentação clara e higienizada para demonstrar o case técnico sem exposição de dados sensíveis.
- **Critérios de Aceite**:
  1. Revisão completa de todos os documentos garantindo o uso exclusivo de dados fictícios (nomes de clientes, IPs, IDs de subscrição).
  2. Runbook operacional de onboarding de novo cliente documentando:
     - Coleta de dados (ranges remotos, IP público do gateway do cliente);
     - Execução da validação de sobreposição de CIDR;
     - Configuração dos parâmetros do cliente no Terraform;
     - Processo de Pull Request e aprovação humana obrigatória.
  3. Atualização do `README.md` principal com diagrama de arquitetura e instruções do laboratório.
- **Dependências**: US-07, US-10, US-11.
- **Pendências / Notas Técnicas**:
  - Validação final de segurança conduzida pelo *Security Engineer*.

---

## 6. Matriz de Priorização e Rastreabilidade

| ID | História de Usuário | Épico | Prioridade | Agente | Dependências |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **US-01** | Backend Remoto Seguro do Terraform | EP-01 | Alta (Bloqueante) | Cloud DevOps | Nenhuma |
| **US-02** | Consumo de RG Pré-existente e OIDC | EP-01 | Alta (Bloqueante) | Cloud DevOps | US-01 |
| **US-03** | Pipeline CI/CD com Gate de Aprovação Humana | EP-01 | Alta | Cloud DevOps | US-02 |
| **US-04** | VNet Compartilhada e Subnets | EP-02 | Alta | Cloud DevOps | US-02, US-03 |
| **US-05** | Virtual Network Gateway Compartilhado (IKEv2) | EP-02 | Alta | Cloud DevOps | US-04 |
| **US-06** | Validação Automatizada de CIDR Overlap | EP-02 | Alta | Cloud DevOps / QA | US-04 |
| **US-07** | Módulo de Conectividade VPN por Cliente (LNG/VPN) | EP-03 | Alta | Cloud DevOps | US-05, US-06 |
| **US-08** | Módulo de Isolamento de Rede por Cliente (ASG) | EP-03 | Média | Cloud DevOps | US-04, US-07 |
| **US-09** | Definição Arquitetural do Host Windows Server | EP-04 | Alta | Cloud Architect | Nenhuma |
| **US-10** | Módulo Terraform de Collector Dedicado | EP-04 | Alta | Cloud DevOps | US-08, US-09 |
| **US-11** | Suíte de Validação e Testes de Conformidade | EP-05 | Média | QA Engineer | US-03, US-06, US-10 |
| **US-12** | Documentação, Runbooks e Sanitização | EP-05 | Média | PO / Architect | US-07, US-10, US-11 |

---

## 7. Registro de Decisões Técnicas Pendentes (Hand-off para Agentes Técnicos)

Para assegurar a estrita separação de papéis, as seguintes decisões técnicas permanecem abertas e foram encaminhadas aos respectivos agentes:

1. **Cloud Architect**:
   - Definição da versão oficial, imagem e SKU da VM Windows Server dos collectors (`US-09`).
   - Dimensionamento do SKU do Virtual Network Gateway (`US-05`).
   - Definição do endereçamento CIDR fictício oficial da VNet e subnets (`US-04`).
2. **Security Engineer**:
   - Especificação das políticas de IPsec/IKE (criptografia, integridade, DH groups) para as conexões VPN (`US-05`, `US-07`).
   - Matriz de regras de NSG e portas específicas requeridas para o serviço de coleta (`US-08`).
   - Revisão das políticas de retenção e proteção do Terraform State (`US-01`).
3. **Cloud DevOps Engineer**:
   - Estruturação do repositório Terraform (módulos reutilizáveis vs. root module) e automação dos workflows do GitHub Actions (`US-03`, `US-07`, `US-10`).
4. **QA Engineer**:
   - Criação da massa de testes de ranges CIDR (conflitantes e não-conflitantes) para validação do script de overlap (`US-06`, `US-11`).
