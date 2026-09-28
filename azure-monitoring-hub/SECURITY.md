# Política de Segurança — Azure Monitoring Hub

## 1. Objetivo

Este documento define os controles de segurança obrigatórios para o projeto Azure Monitoring Hub.

As regras se aplicam aos usuários, agentes de IA, automações, pipelines, Terraform e recursos provisionados no Microsoft Azure.

---

## 2. Princípios

O projeto deverá seguir os seguintes princípios:

- Least Privilege
- Zero Trust
- Segregação de responsabilidades
- Defense in Depth
- Infrastructure as Code
- Rastreabilidade
- Aprovação humana para operações privilegiadas
- Nenhum segredo armazenado em código

---

## 3. Escopo Azure

O projeto utilizará exclusivamente o Resource Group:

`rg-monhub-dev-brs`

A identidade de automação:

`app-monhub-iac-dev`

possuirá a role:

`Contributor`

exclusivamente no Resource Group do projeto.

É proibido conceder à identidade:

- Owner
- User Access Administrator
- Contributor no escopo da Subscription
- permissões administrativas no Microsoft Entra ID

A identidade não deverá modificar recursos fora do Resource Group autorizado.

---

## 4. Credenciais e Secrets

É proibido armazenar credenciais em:

- código Terraform;
- arquivos de agentes;
- prompts;
- documentação;
- repositório Git;
- arquivos `.tfvars` versionados;
- arquivos `.env` versionados;
- outputs Terraform;
- scripts;
- logs.

Exemplos de informações que não deverão ser expostas:

- passwords;
- Client Secrets;
- VPN Pre-Shared Keys;
- tokens;
- certificados privados;
- chaves privadas.

Sempre que possível, deverão ser utilizadas identidades sem credenciais permanentes.

Para automações externas, deverá ser priorizado o uso de Workload Identity Federation/OIDC.

---

## 5. Segurança dos Agentes

Nenhum agente deverá possuir acesso irrestrito ao ambiente Azure.

### Product Owner

Não possui permissão para modificar recursos Azure.

### Cloud Architect

Não possui permissão para modificar recursos Azure.

Responsável apenas por arquitetura e decisões técnicas.

### Security Engineer

Responsável pela revisão de segurança.

Quando acesso ao Azure for necessário, deverá utilizar preferencialmente permissões somente leitura.

### Cloud DevOps Engineer

Responsável pela implementação do Terraform.

Pode:

- criar e alterar arquivos Terraform;
- executar `terraform fmt`;
- executar `terraform validate`;
- executar `terraform plan`;
- executar consultas Azure somente leitura necessárias para validação.

Não deverá executar autonomamente:

- `terraform apply`;
- `terraform destroy`;
- alterações de RBAC;
- criação de credenciais;
- alterações fora do Resource Group autorizado.

### QA Engineer

Responsável por validar a infraestrutura e os requisitos do projeto.

Deverá utilizar acesso somente leitura sempre que possível.

---

## 6. Terraform

Toda alteração de infraestrutura deverá ser declarada através de Infrastructure as Code sempre que tecnicamente aplicável.

Fluxo obrigatório:

Alteração
→ terraform fmt
→ terraform validate
→ terraform plan
→ revisão
→ aprovação humana
→ terraform apply

`terraform apply` não deverá ser executado automaticamente por um agente sem aprovação humana.

`terraform destroy` exige autorização humana explícita.

O Terraform State deverá ser protegido e não poderá ser versionado no Git.

---

## 7. Rede

Collectors deverão utilizar exclusivamente endereços IP privados.

É proibida a criação de Public IP diretamente nas VMs de collector.

O acesso de rede deverá ser controlado através de:

- Network Security Groups
- Application Security Groups
- Subnets
- VPN Site-to-Site

Cada cliente deverá possuir isolamento lógico próprio.

Ranges de rede deverão ser validados para impedir sobreposição.

---

## 8. VPN

Cada cliente deverá possuir:

- Local Network Gateway dedicado;
- VPN Connection dedicada;
- endereço público remoto próprio;
- ranges internos explicitamente declarados.

O Azure Virtual Network Gateway poderá ser compartilhado.

As conexões deverão utilizar IKEv2.

VPN Pre-Shared Keys nunca deverão ser armazenadas no repositório.

---

## 9. Logging e Auditoria

Alterações deverão ser rastreáveis através de:

- Git commits;
- Pull Requests;
- Terraform Plan;
- Pipeline logs;
- Azure Activity Log.

A documentação deverá permitir identificar:

- alteração realizada;
- responsável;
- motivo;
- resultado esperado;
- resultado da validação.

Secrets não deverão aparecer nos logs.

---

## 10. Proteção contra ações destrutivas

São consideradas operações críticas:

- exclusão de Resource Group;
- exclusão de Virtual Network;
- exclusão de Virtual Network Gateway;
- exclusão de VPN Connections;
- exclusão de VMs;
- alterações de RBAC;
- execução de `terraform destroy`.

Essas operações exigem autorização humana explícita.

Nenhum agente poderá decidir autonomamente executar uma operação destrutiva.

---

## 11. Dados do case study

Este projeto é baseado em um cenário anonimizado.

É proibido utilizar:

- nomes reais de clientes;
- nomes internos de empresas;
- Tenant IDs reais na documentação;
- Subscription IDs reais na documentação;
- endereços IP corporativos reais;
- usuários corporativos;
- VPN PSKs reais;
- screenshots contendo informações sensíveis;
- credenciais ou informações proprietárias.

Todos os exemplos públicos deverão utilizar dados fictícios ou sanitizados.

---

## 12. Evolução do modelo de segurança

Na primeira versão do laboratório, a identidade de automação utilizará Contributor no escopo exclusivo do Resource Group.

Após a implementação inicial, as operações Azure efetivamente utilizadas deverão ser analisadas.

Uma versão futura poderá substituir Contributor por uma Custom Role contendo somente as operações necessárias para o projeto.