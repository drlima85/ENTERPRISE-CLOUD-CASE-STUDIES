# Arquitetura Técnica — Azure Monitoring Hub (`monhub`)

## 1. Visão Geral da Arquitetura de Rede V1 (US-04)

Este documento estabelece a baseline oficial da arquitetura de rede V1 para o projeto **Azure Monitoring Hub** (`monhub`), atendendo aos requisitos funcionais e não funcionais descritos na **US-04** do [BACKLOG.md](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/docs/backlog/BACKLOG.md) e aderindo às diretrizes de segurança de [SECURITY.md](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/SECURITY.md) e aos padrões de [naming-rules.md](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/.agents/rules/naming-rules.md).

A topologia adota o modelo de conectividade híbrida centralizada (*Hub Network*), onde recursos compartilhados de trânsito e segurança hospedam coletores de monitoramento dedicados por cliente, com isolamento lógico estrito e terminação de túneis VPN Site-to-Site (IKEv2).

---

## 2. Especificação de Endereçamento e Subnetting

O projeto adota exclusivamente faixas privadas fictícias (RFC 1918), preservando total anonimização e isolamento em relação a ambientes corporativos reais.

### 2.1 Bloco CIDR Oficial da Virtual Network

- **Nome do Recurso**: `vnet-monhub-dev-brs`
- **Resource Group**: `rg-monhub-dev-brs`
- **Região**: Brazil South (`brs`)
- **Address Space Oficial**: `10.240.0.0/20` (Total de 4.096 endereços IP: `10.240.0.0` a `10.240.15.255`)

### 2.2 Estrutura de Subnets da VNet

| Subnet | Bloco CIDR | IPs Totais | IPs Disponíveis Azure (Total - 5) | Finalidade e Associação |
| :--- | :--- | :--- | :--- | :--- |
| `GatewaySubnet` | `10.240.0.0/26` | 64 | 59 | Subnet reservada exclusivamente para o Azure Virtual Network Gateway (`vng-monhub-dev-brs`). Sem NSG associado. |
| `snet-collectors-dev-brs` | `10.240.1.0/24` | 256 | 251 | Hospedagem das Network Interfaces (NICs) dos coletores Windows dedicados por cliente. Associada a `nsg-collectors-dev-brs`. |
| *Reserva de Expansão (Serviços Compartilhados)* | `10.240.2.0/24` | 256 | 251 | Reserva arquitetural para expansão futura de serviços compartilhados. |
| *Reserva de Expansão Futura* | `10.240.4.0/22` | 1.024 | 1.019 | Bloco contíguo livre para spokes adicionais, novos pools de coletores ou migração de ambiente. |
| *Reserva de Longo Prazo* | `10.240.8.0/21` | 2.048 | 2.043 | Espaço de reserva não alocado dentro do `/20`. |

> [!NOTE]
> A plataforma Azure reserva automaticamente 5 endereços IP em qualquer subnet:
> 1. `x.x.x.0`: Endereço de rede.
> 2. `x.x.x.1`: Gateway padrão da subnet.
> 3. `x.x.x.2`: DNS mapping do Azure.
> 4. `x.x.x.3`: DNS mapping do Azure.
> 5. `x.x.x.255`: Broadcast da rede.

---

## 3. Justificativa do Dimensionamento e Capacidade de Crescimento

### 3.1 Dimensionamento da `GatewaySubnet` (`/26`)
- **Decisão**: Adoção do bloco `10.240.0.0/26` (64 IPs totais, sendo 59 utilizáveis pelo Azure).
- **Justificativa**: A escolha do prefixo `/26` foi definida como margem adicional de endereçamento e capacidade para evolução futura da infraestrutura de gateway sem necessidade de recriação ou redimensionamento de subnet, garantindo folga operacional adequada.

### 3.2 Dimensionamento da Subnet de Collectors (`/24`)
- **Capacidade**: Cada cliente recebe 1 VM dedicada de collector com 1 IP privado estático alocado em sua NIC (`nic-col-<cliente>-dev-brs`).
- **Escala Prevista**: Com um `/24` (`10.240.1.0/24`), dispõe-se de 251 endereços IPs utilizáveis, o que permite escalar a plataforma para atender confortavelmente até 250 clientes distintos no mesmo pool de collectors sem exaustão de IPs.
- **Previsibilidade**: O uso de IPs privados estáticos a partir de `10.240.1.10` permite fácil mapeamento operacional e inventário.

### 3.3 Capacidade Global da VNet (`/20`)
- A reserva do super-bloco `10.240.0.0/20` (4.096 IPs) consome apenas 320 IPs no provisionamento inicial (somando a `GatewaySubnet` e a `snet-collectors-dev-brs`), deixando mais de 92% da faixa disponível para a evolução futura da infraestrutura de monitoramento sem requerer reendereçamento ou complexidade de roteamento entre VNets secundárias.

---

## 4. Estratégia de Prevenção de Conflitos e Sobreposição de CIDRs (Overlap Detection)

A plataforma conecta múltiplos clientes remotos via VPN Site-to-Site terminadas no mesmo Virtual Network Gateway compartilhado. Em uma arquitetura Route-Based sem NAT no gateway, a sobreposição de faixas IP entre redes remotas ou entre uma rede remota e a VNet Azure causa colisão de tabelas de rotas e falha de roteamento.

### 4.1 Diretrizes de Isolamento de Endereçamento
1. **Inviolabilidade da VNet**: Nenhuma rede remota de cliente (definida no Local Network Gateway) poderá utilizar qualquer bloco contido no super-bloco da VNet (`10.240.0.0/20`).
2. **Não-Sobreposição Inter-Clientes**: Cada cliente (`cust01`, `cust02`, `cust03`, ...) deve possuir blocos remotos estritamente disjuntos. Caso o `cust01` utilize `192.168.10.0/24`, nenhum outro cliente poderá cadastrar faixas que interceptem ou contenham este bloco.
3. **Escopo Fictício do Laboratório**: Os clientes do laboratório utilizarão faixas fictícias segregadas (ex.: `cust01` em `192.168.10.0/24`, `cust02` em `192.168.20.0/24`, `cust03` em `192.168.30.0/24`).

### 4.2 Mecanismo Preventivo (Pré-Requisito para US-06)
- O onboarding de um cliente exigirá a declaração de suas faixas remotas em arquivo de parâmetros parametrizado.
- Um script de validação de overlap (conforme [US-06](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/docs/backlog/BACKLOG.md#us-06-validação-automatizada-de-sobreposição-de-blocos-cidr-overlap-detection)) deverá ser executado antes de qualquer comando de planejamento do Terraform (`terraform plan`), validando interseções matemáticas de CIDR entre o novo cliente, a VNet do hub e todos os LNGs já cadastrados.
- Qualquer sobreposição identificada bloqueará imediatamente a execução da pipeline de integração contínua.

---

## 5. Relação entre Componentes de Rede e Segurança

A segregação multi-tenant na camada de rede compartilhada é garantida pelo relacionamento coordenado entre VNet, Subnets, Network Security Group (NSG), Application Security Groups (ASGs) e o Virtual Network Gateway (VNG).

```mermaid
flowchart TD
    subgraph Azure_VNet["Azure Virtual Network: vnet-monhub-dev-brs (10.240.0.0/20)"]
        subgraph GWSnet["GatewaySubnet (10.240.0.0/26)"]
            VNG["Virtual Network Gateway: vng-monhub-dev-brs\n(Route-Based, IKEv2)\nIP Público: pip-vng-monhub-dev-brs"]
        end

        subgraph ColSnet["snet-collectors-dev-brs (10.240.1.0/24)"]
            NSG["NSG: nsg-collectors-dev-brs"]

            subgraph Customer01["Isolamento Lógico: Cliente 01"]
                ASG1["ASG: asg-cust01-dev-brs"]
                VM1["VM: vm-col-cust01-dev-brs\n(Sem IP Público)\nIP Privado: 10.240.1.10"]
                VM1 --- ASG1
            end

            subgraph Customer02["Isolamento Lógico: Cliente 02"]
                ASG2["ASG: asg-cust02-dev-brs"]
                VM2["VM: vm-col-cust02-dev-brs\n(Sem IP Público)\nIP Privado: 10.240.1.11"]
                VM2 --- ASG2
            end

            NSG -. Protege .- ColSnet
        end
    end

    subgraph Client01_Remote["Rede Remota Cliente 01 (ex.: 192.168.10.0/24)"]
        LNG1["Local Network Gateway: lng-cust01-dev-brs"]
    end

    subgraph Client02_Remote["Rede Remota Cliente 02 (ex.: 192.168.20.0/24)"]
        LNG2["Local Network Gateway: lng-cust02-dev-brs"]
    end

    VNG <== "VPN Connection: con-cust01-dev-brs (IKEv2)" ==> LNG1
    VNG <== "VPN Connection: con-cust02-dev-brs (IKEv2)" ==> LNG2
    VNG <-->|"Roteamento Privado Interno"| ColSnet
```

### 5.1 Regras de Associação dos Componentes

1. **Virtual Network Gateway (`vng-monhub-dev-brs`)**:
   - Provisionado exclusivamente dentro de `GatewaySubnet`.
   - Vinculado a um endereço IP público dedicado (`pip-vng-monhub-dev-brs`).
   - Não possui associação direta com NSG (em conformidade com as melhores práticas da Microsoft, que desaconselham NSG em `GatewaySubnet` para evitar interrupção de planos de controle do gateway).
   - Termina conexões VPN Site-to-Site IKEv2 dedicadas (`con-cust<ID>-dev-brs`) com cada cliente.

2. **Network Security Group (`nsg-collectors-dev-brs`)**:
   - Associado à subnet `snet-collectors-dev-brs`.
   - Controla todo o tráfego de entrada e saída dos coletores.
   - Aplica a política de *Default Deny* para comunicação lateral não autorizada.

3. **Application Security Groups (`asg-cust<ID>-dev-brs`)**:
   - Cada cliente possui 1 ASG dedicado criado no mesmo Resource Group.
   - A NIC do coletor (`nic-col-cust<ID>-dev-brs`) é associada ao respectivo ASG.
   - O NSG utiliza o ASG como destino/origem nas regras de firewall, garantindo que o coletor do `cust01` receba e envie tráfego estritamente autorizado para os blocos IP de `lng-cust01-dev-brs`.
   - Impede que collectors de clientes distintos na mesma subnet se comuniquem diretamente (mitigação de tráfego lateral / *lateral movement*).

4. **Coletores de Monitoramento**:
   - Baseline oficial da VM aprovada para V1: Windows Server 2022 Datacenter Gen2, SKU `Standard_B2s` (2 vCPUs, 4 GiB RAM), OS Disk `StandardSSD_LRS` de 127 GiB, conforme [ADR-002](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/docs/architecture/adr/ADR-002-collector-vm.md).
   - Operam sem qualquer interface pública (`public_ip_address_id = null`).
   - Recebem endereço IP estático configurado na interface privada vinculada à subnet `snet-collectors-dev-brs`.
   - Associados ao ASG exclusivo de cada cliente (`asg-cust<ID>-dev-brs`).
   - Comunicação com alvos monitorados ocorre exclusivamente através do túnel VPN IPsec/IKEv2 via VNG.

---

## 6. Matriz de Decisões e Pendências por Agente (Handoffs)

Para preservar a governança do projeto, respeitar a separação de papéis e evitar a assunção indevida de requisitos, as responsabilidades e pendências de entrega técnica para a conclusão das histórias do Épico 02 e Épico 04 estão mapeadas a seguir:

| Item / Decisão | Agente Responsável | Status Arquitetural | Descrição da Entrega Esperada |
| :--- | :--- | :--- | :--- |
| **Definição de CIDRs e Subnets da VNet** | Cloud Architect | **Concluído (V1)** | Definidos: VNet `10.240.0.0/20`, GatewaySubnet `10.240.0.0/26`, Collectors `10.240.1.0/24`. |
| **Implementação Terraform da VNet e Subnets (US-04)** | Cloud DevOps Engineer | **Pendente** | Desenvolver módulo Terraform em `terraform/` consumindo data source do RG e os blocos definidos nesta especificação. |
| **Matriz de Regras e Portas do NSG (US-04 / US-08)** | Security Engineer | **Pendente** | Especificar as portas estritas de entrada/saída (ex.: WMI, WinRM, SNMP, ICMP) e a regra de bloqueio lateral entre coletores. |
| **Dimensionamento de SKU do VNG (US-05)** | Cloud Architect | **Concluído (V1)** | VpnGw1AZ / Generation1 — decisão arquitetural V1 documentada no [ADR-001](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/docs/architecture/adr/ADR-001-vng-sku.md). |
| **Políticas Criptográficas IPsec/IKE (US-05 / US-07)** | Security Engineer | **Pendente** | Especificar parâmetros de criptografia Phase 1 / Phase 2 (IKE encryption, integrity, DH Group, PFS) e gestão de PSK. |
| **Algoritmo de Overlap Detection (US-06)** | Cloud DevOps / QA | **Pendente** | Implementar script automatizado pré-plan para validação matemática de sobreposição de CIDR. |
| **Especificação da VM dos Collectors (US-09)** | Cloud Architect | **Concluído (V1)** | Baseline oficial (WS 2022 Gen2, `Standard_B2s`, StandardSSD 127 GiB) documentada no [ADR-002](file:///C:/Users/drlim/ENTERPRISE-CLOUD-CASE-STUDIES/azure-monitoring-hub/docs/architecture/adr/ADR-002-collector-vm.md). |
