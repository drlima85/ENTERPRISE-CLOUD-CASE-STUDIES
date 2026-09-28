# Regras de Segurança dos Agentes — Azure Monitoring Hub

## 1. Regra principal

Segurança possui prioridade sobre velocidade, conveniência ou automação.

Nenhum agente poderá remover, contornar ou reduzir um controle de segurança apenas para concluir uma tarefa.

As políticas definidas em `SECURITY.md` são obrigatórias.

---

## 2. Escopo Azure autorizado

O único Resource Group autorizado para alterações deste projeto é: `rg-monhub-dev-brs`

A identidade de automação é:`app-monhub-iac-dev`

Qualquer tentativa de criar, alterar ou excluir recursos fora desse Resource Group deverá ser interrompida.

O agente não deverá solicitar ampliação de permissões automaticamente.

---

## 3. RBAC

É proibido aos agentes:

- atribuir roles;
- remover role assignments;
- criar permissões administrativas;
- conceder Owner;
- conceder User Access Administrator;
- ampliar o escopo do Service Principal;
- alterar permissões no Microsoft Entra ID.

Alterações de RBAC são responsabilidade humana.

---

## 4. Credenciais

Nunca armazenar ou solicitar exposição desnecessária de:

- passwords;
- Client Secrets;
- tokens;
- VPN Pre-Shared Keys;
- private keys;
- certificados privados;
- connection strings contendo credenciais.

Credenciais não deverão aparecer em:

- prompts;
- arquivos dos agentes;
- código Terraform;
- `.tfvars` versionados;
- outputs;
- documentação;
- commits;
- logs.

Quando uma operação exigir um secret, utilizar mecanismo seguro apropriado sem revelar o valor ao agente sempre que possível.

---

## 5. Terraform

Os agentes podem executar automaticamente:

- `terraform fmt`
- `terraform validate`
- `terraform plan`
- `terraform show` para análise de planos previamente gerados

`terraform apply` exige aprovação humana explícita.

`terraform destroy` exige aprovação humana explícita e específica para a destruição.

Nunca utilizar: `terraform apply -auto-approve`  
ou: `terraform destroy -auto-approve` por decisão autônoma do agente.

---

## 6. Azure CLI

Comandos somente leitura podem ser utilizados para discovery, validação e troubleshooting.

Exemplos:

- `az account show`
- `az group show`
- `az resource list`
- comandos `show` e `list` necessários ao projeto

Comandos que criem, alterem ou removam recursos deverão seguir o fluxo de Infrastructure as Code sempre que tecnicamente aplicável.

Não utilizar Azure CLI como forma de contornar Terraform ou os controles de aprovação.

---

## 7. Operações destrutivas

São consideradas operações destrutivas ou de alto impacto:

- exclusão de recursos;
- substituição de recursos críticos;
- exclusão de VNet;
- exclusão de subnet;
- exclusão de Virtual Network Gateway;
- exclusão de VPN Connection;
- exclusão de VM;
- alteração de RBAC;
- `terraform destroy`;
- operações que provoquem perda de conectividade.

Antes dessas operações, o agente deverá:

1. informar claramente o impacto;
2. identificar os recursos afetados;
3. apresentar a ação proposta;
4. aguardar autorização humana explícita.

---

## 8. Networking

É proibido criar Public IP para VMs de collector.

Regras de NSG não deverão utilizar origem irrestrita (`0.0.0.0/0` ou `*`) para portas administrativas ou serviços internos sem justificativa, revisão de segurança e aprovação humana.

Novos ranges deverão ser validados contra:

- VNet Azure;
- subnets existentes;
- redes dos demais clientes;
- redes remotas já cadastradas.

Sobreposição de CIDR deverá bloquear o onboarding até correção.

---

## 9. Dados públicos

O projeto é um case study anonimizado.

Não utilizar dados reais provenientes do ambiente corporativo original.

Utilizar somente:

- nomes fictícios;
- endereçamento de laboratório;
- identificadores sanitizados;
- screenshots sanitizados;
- exemplos genéricos.

Caso um agente detecte informação potencialmente sensível em um arquivo destinado ao Git, deverá sinalizá-la antes do commit.

---

## 10. Git

Antes de sugerir commit, verificar se existem:

- secrets;
- credentials;
- `.tfstate`;
- `.tfvars` sensíveis;
- private keys;
- certificados privados;
- dados corporativos reais.

Nunca incluir esses artefatos em commits.

Commits deverão ser pequenos, rastreáveis e relacionados à tarefa executada.

---

## 11. Falha segura

Quando houver dúvida sobre:

- autorização;
- escopo;
- impacto;
- exposição de credenciais;
- ação destrutiva;
- segurança de rede;

o agente deverá interromper a operação de escrita e solicitar decisão humana.

A ausência de informação não deverá ser interpretada como autorização.