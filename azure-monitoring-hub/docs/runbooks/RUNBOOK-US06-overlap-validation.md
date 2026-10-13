# Runbook Operacional — Validação Automatizada de Sobreposição de CIDRs (US-06)

- **Código do Projeto**: `monhub`
- **Versão da Arquitetura**: 1.2
- **História Relacionada**: [US-06: Validação Automatizada de Sobreposição de Blocos CIDR](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/docs/backlog/BACKLOG.md#us-06-validação-automatizada-de-sobreposição-de-blocos-cidr-overlap-detection)
- **Documento Técnico de Referência**: [addressing-plan.md v1.2](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/docs/architecture/addressing-plan.md)
- **Pipeline Oficial de Execução**: [`.github/workflows/monhub-terraform.yml`](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/.github/workflows/monhub-terraform.yml)
- **Localização dos Scripts e Testes**: [`scripts/validate_overlap.py`](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/scripts/validate_overlap.py) | [`tests/test_validate_overlap.py`](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/tests/test_validate_overlap.py)
- **Fonte Única de Verdade (SSOT)**: [`data/customers.json`](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/data/customers.json)

---

## 1. Visão Geral

O validador determinístico de sobreposição de CIDR (`scripts/validate_overlap.py`) atua como um *guardrail* automatizado no ciclo de desenvolvimento e integração contínua (CI/CD). Ele impede que blocos de rede conflitantes, IPs privados duplicados ou dados fictícios inapropriados alcancem o planejamento do Terraform (`terraform plan`) ou a aplicação (`terraform apply`).

### Princípios Obrigatórios:
1. **Fonte Única da Verdade (SSOT)**: Todos os clientes residem exclusivamente em `data/customers.json`, consumido diretamente pelo Python e pelo Terraform via `local.customers_data` em `locals.tf`.
2. **Governança Estrita de Ambiente**: A execução exige definição explícita do ambiente (`--environment` ou variável `MONHUB_ENVIRONMENT`). A execução sem definição de ambiente é bloqueada.
3. **Isolamento de Sandbox**: A flag `--allow-testnet` é autorizada **exclusivamente no ambiente protegido `monhub-dev`**. Qualquer tentativa de utilizá-la em ambientes funcionais ou produtivos é bloqueada por segurança.
4. **Integridade Criptográfica Plan-to-Apply**: O hash SHA256 do arquivo `data/customers.json` é validado no Job 1 e checado no Job 3 (Apply), impedindo que alterações nos dados ocorram entre o planejamento e a aplicação.

---

## 2. Pré-requisitos de Execução Local

- **Python**: Versão 3.8 ou superior instalada e acessível no `PATH`.
- **Acesso ao repositório**: Terminal posicionado no diretório `azure-monitoring-hub`.

---

## 3. Instruções de Execução Local

### 3.1 Modo Sandbox / Demonstração (Ambiente `monhub-dev`)
Utilizado para validar o arquivo de clientes atual do laboratório (`cust01`, `cust02`, `cust03`), cujos gateways utilizam a faixa de documentação TEST-NET (`198.51.100.0/24`):

```bash
# Na raiz da pasta azure-monitoring-hub:
python scripts/validate_overlap.py --file data/customers.json --environment monhub-dev --allow-testnet
```

**Saída esperada**:
```text
==============================================================================
AZURE MONITORING HUB — VALIDADOR DETERMINÍSTICO DE CIDR E CONECTIVIDADE (US-06)
==============================================================================
Ambiente Configurado : monhub-dev
Modo de Operação     : SANDBOX / DEMONSTRAÇÃO (--allow-testnet ativo)
Clientes Processados : 3
Prefixos Validados   : 6
------------------------------------------------------------------------------

[AVISOS DETECTADOS]:
  ! [SANDBOX WARNING] Cliente 'cust01': O gateway_ip '198.51.100.10' pertence ao bloco documental RFC 5737 (TEST-NET)...
  ! [SANDBOX WARNING] Cliente 'cust02': O gateway_ip '198.51.100.20' pertence ao bloco documental RFC 5737 (TEST-NET)...
  ! [SANDBOX WARNING] Cliente 'cust03': O gateway_ip '198.51.100.30' pertence ao bloco documental RFC 5737 (TEST-NET)...

STATUS FINAL: [SUCESSO] Todos os blocos CIDR, IPs de coletores e gateways são válidos e disjuntos.
==============================================================================
```
*Código de Retorno (`Exit Code`)*: `0` (Sucesso).

---

### 3.2 Modo Estrito de Produção (Ambiente `monhub-prod` ou `production`)
Executa a validação estrita sem a flag `--allow-testnet`. Se houver qualquer IP da RFC 5737, a execução é abortada:

```bash
python scripts/validate_overlap.py --file data/customers.json --environment monhub-prod
```

**Saída esperada com a baseline documental**:
```text
==============================================================================
AZURE MONITORING HUB — VALIDADOR DETERMINÍSTICO DE CIDR E CONECTIVIDADE (US-06)
==============================================================================
Ambiente Configurado : monhub-prod
Modo de Operação     : PRODUÇÃO / ESTRITO (Padrão de Segurança)
Clientes Processados : 3
Prefixos Validados   : 6
------------------------------------------------------------------------------

[FALHAS DE CONFORMIDADE DETECTADAS]:
  X [PRODUÇÃO BLOQUEIO] Cliente 'cust01': O gateway_ip '198.51.100.10' pertence à faixa documental RFC 5737 (TEST-NET)...
  X [PRODUÇÃO BLOQUEIO] Cliente 'cust02': O gateway_ip '198.51.100.20' pertence à faixa documental RFC 5737 (TEST-NET)...
  X [PRODUÇÃO BLOQUEIO] Cliente 'cust03': O gateway_ip '198.51.100.30' pertence à faixa documental RFC 5737 (TEST-NET)...
------------------------------------------------------------------------------
STATUS FINAL: [FALHA] Validação de sobreposição reprovada. Execução interrompida.
==============================================================================
```
*Código de Retorno (`Exit Code`)*: `1` (Falha bloqueante).

---

### 3.3 Execução da Bateria de Testes Unitários de QA

Para rodar a suíte completa de testes automatizados com `unittest`:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 4. Integração no Pipeline Oficial (`monhub-terraform.yml`)

O workflow oficial está configurado em [`.github/workflows/monhub-terraform.yml`](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/.github/workflows/monhub-terraform.yml):

```
┌────────────────────────────────────────────────────────┐
│ Job 1: validate                                        │
│ - Executa testes unitários de QA (unittest)            │
│ - Valida ambiente explícito                            │
│ - Executa validate_overlap.py (--allow-testnet se dev) │
│ - Gera Checksum SHA256 de data/customers.json          │
└──────────────────────────┬─────────────────────────────┘
                           │ (Sucesso Obrigatório)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Job 2: plan                                            │
│ - needs: [validate]                                    │
│ - Autenticação Azure via OIDC                          │
│ - terraform fmt, init, validate, plan                  │
│ - Upload do plano tfplan                               │
└──────────────────────────┬─────────────────────────────┘
                           │ (Sucesso + inputs.apply == true)
                           ▼
┌────────────────────────────────────────────────────────┐
│ Job 3: apply                                           │
│ - needs: [plan, validate]                              │
│ - Environment: monhub-dev (Aprovação Humana Obrigatória│
│ - Valida imutabilidade de data/customers.json (SHA256) │
│ - terraform apply tfplan                               │
└────────────────────────────────────────────────────────┘
```
