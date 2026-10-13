#!/usr/bin/env python3
"""
Mecanismo Automatizado de Detecção de Sobreposição de CIDRs (US-06)
Azure Monitoring Hub (monhub) - Versão 1.2

Este script realiza a validação matemática determinística de blocos de rede
para onboarding de clientes em topologia Route-Based no Azure VPN Gateway:
1. Validação de formato IPv4 estrito (sem bits de host no endereço base) e máscara (/8 a /29).
2. Validação de conformidade RFC 1918 para redes remotas.
3. Detecção de sobreposição com a Virtual Network do Azure (10.240.0.0/20).
4. Detecção de sobreposição entre redes de clientes distintos (Customer-to-Customer).
5. Validação de unicidade e validade dos IPs dos coletores na subnet snet-collectors-dev-brs.
6. Validação de unicidade e roteabilidade dos IPs públicos dos gateways remotos (LNG).
   - Suporta modo sandbox (--allow-testnet) EXCLUSIVAMENTE para o ambiente 'monhub-dev'.
   - Rejeita estritamente blocos RFC 5737 e não-globais em qualquer ambiente funcional/produção.
   - Falha imediatamente se a configuração do ambiente estiver ausente ou inconsistente.
"""

import argparse
import ipaddress
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Constantes da Baseline Arquitetural Oficial (ARCHITECTURE.md / addressing-plan.md)
DEFAULT_VNET_CIDR = "10.240.0.0/20"
DEFAULT_COLLECTORS_SUBNET = "10.240.1.0/24"
DEFAULT_GATEWAY_SUBNET = "10.240.0.0/26"

# Ambientes autorizados para execução em modo Sandbox/Mock
AUTHORIZED_SANDBOX_ENVIRONMENTS = ["monhub-dev"]
KNOWN_ENVIRONMENTS = ["monhub-dev", "monhub-prod", "production", "staging"]

# Blocos RFC 1918 para validação de redes privadas
RFC1918_BLOCKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]

# Blocos RFC 5737 (TEST-NET) exclusivos para documentação e simulação sintética
RFC5737_TESTNET_BLOCKS = [
    ipaddress.ip_network("192.0.2.0/24"),    # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"), # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
]

MIN_PREFIX_LENGTH = 8
MAX_PREFIX_LENGTH = 29


@dataclass
class ValidationReport:
    """Relatório estruturado de validação de conectividade e CIDRs."""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    customers_count: int = 0
    cidrs_count: int = 0
    environment: str = ""
    allow_testnet_mode: bool = False

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


def is_rfc1918(net: ipaddress.IPv4Network) -> bool:
    """Verifica se uma sub-rede IPv4 pertence integralmente à RFC 1918."""
    return any(net.subnet_of(rfc) for rfc in RFC1918_BLOCKS)


def is_rfc5737(ip: ipaddress.IPv4Address) -> bool:
    """Verifica se um endereço IPv4 pertence a qualquer bloco RFC 5737 (TEST-NET)."""
    return any(ip in block for block in RFC5737_TESTNET_BLOCKS)


def validate_environment_configuration(
    environment: Optional[str],
    allow_testnet_requested: bool,
) -> Tuple[bool, str, List[str]]:
    """
    Valida a configuração do ambiente de execução.
    Regras:
    1. O ambiente não pode ser vazio, nulo ou inconsistente.
    2. A flag --allow-testnet é autorizada EXCLUSIVAMENTE para 'monhub-dev'.
    3. Em qualquer outro ambiente, o modo sandbox é rejeitado com erro.
    Retorna: (allow_testnet_efetivo, ambiente_sanitizado, erros)
    """
    errors: List[str] = []
    env_clean = (environment or "").strip().lower()

    if not env_clean:
        errors.append(
            "[ERRO DE GOVERNANÇA]: A configuração do ambiente está ausente. "
            "Informe explicitamente o ambiente via argumento '--environment' ou variável 'MONHUB_ENVIRONMENT'. "
            "Execução sem definição explícita de ambiente é proibida."
        )
        return False, "", errors

    if env_clean not in KNOWN_ENVIRONMENTS:
        errors.append(
            f"[ERRO DE GOVERNANÇA]: O ambiente '{env_clean}' é inválido ou inconsistente. "
            f"Ambientes homologados: {', '.join(KNOWN_ENVIRONMENTS)}."
        )
        return False, env_clean, errors

    # Verificação estrita de autorização para o modo Sandbox
    if allow_testnet_requested:
        if env_clean not in AUTHORIZED_SANDBOX_ENVIRONMENTS:
            errors.append(
                f"[PRODUÇÃO BLOQUEIO]: A flag '--allow-testnet' é terminantemente proibida no ambiente '{env_clean}'. "
                f"O uso de IPs fictícios RFC 5737 é autorizado exclusivamente no ambiente protegido "
                f"'{AUTHORIZED_SANDBOX_ENVIRONMENTS[0]}' para fins de demonstração/laboratório. "
                f"Ambientes funcionais ou produtivos exigem validação estrita de IPv4 público global."
            )
            return False, env_clean, errors
        return True, env_clean, errors

    return False, env_clean, errors


def validate_cidr_syntax(cidr_str: str, customer_id: str) -> Optional[ipaddress.IPv4Network]:
    """
    Valida sintaxe canônica IPv4, ausência de bits de host ativos e máscara permitida.
    Retorna o objeto IPv4Network se válido, ou lança ValueError explicativo.
    """
    if not isinstance(cidr_str, str) or not cidr_str.strip():
        raise ValueError(f"Cliente '{customer_id}': Formato de CIDR vazio ou inválido.")

    try:
        net = ipaddress.ip_network(cidr_str.strip(), strict=True)
    except ValueError as exc:
        raise ValueError(
            f"Cliente '{customer_id}': O prefixo '{cidr_str}' não é um endereço de rede IPv4 canônico "
            f"(bits de host podem estar ativos no endereço base ou sintaxe incorreta). Detalhe: {exc}"
        ) from exc

    if net.version != 4:
        raise ValueError(f"Cliente '{customer_id}': O prefixo '{cidr_str}' não é IPv4.")

    if net.prefixlen < MIN_PREFIX_LENGTH or net.prefixlen > MAX_PREFIX_LENGTH:
        raise ValueError(
            f"Cliente '{customer_id}': O prefixo '{cidr_str}' possui máscara /{net.prefixlen}. "
            f"A política do projeto aceita apenas máscaras entre /{MIN_PREFIX_LENGTH} e /{MAX_PREFIX_LENGTH}."
        )

    if not is_rfc1918(net):
        raise ValueError(
            f"Cliente '{customer_id}': O prefixo '{cidr_str}' não pertence às faixas privadas RFC 1918 "
            f"(10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)."
        )

    return net


def validate_customer_dataset(
    data: Dict[str, Any],
    environment: str,
    allow_testnet: bool = False,
    vnet_cidr: str = DEFAULT_VNET_CIDR,
    collectors_subnet_cidr: str = DEFAULT_COLLECTORS_SUBNET,
    azure_public_ips: Optional[List[str]] = None,
) -> ValidationReport:
    """
    Executa a suíte determinística completa de validações de sobreposição e conformidade.
    """
    # 1. Validação prévia e estrita do ambiente
    effective_allow_testnet, env_clean, env_errors = validate_environment_configuration(
        environment=environment,
        allow_testnet_requested=allow_testnet,
    )

    report = ValidationReport(
        environment=env_clean,
        allow_testnet_mode=effective_allow_testnet,
    )

    for env_err in env_errors:
        report.add_error(env_err)

    if not report.is_valid:
        return report

    azure_public_ips = azure_public_ips or []

    # 2. Validação da própria VNet e Subnet do Azure Hub
    try:
        hub_vnet = ipaddress.ip_network(vnet_cidr, strict=True)
    except Exception as exc:
        report.add_error(f"Configuração do Hub: VNet CIDR inválida '{vnet_cidr}': {exc}")
        return report

    try:
        col_subnet = ipaddress.ip_network(collectors_subnet_cidr, strict=True)
    except Exception as exc:
        report.add_error(f"Configuração do Hub: Subnet de collectors inválida '{collectors_subnet_cidr}': {exc}")
        return report

    # 3. Extração dos clientes
    customers_map = data.get("customers", {})
    if not isinstance(customers_map, dict) or not customers_map:
        report.add_error("Dataset inválido: Nenhuma chave 'customers' com clientes cadastrados foi encontrada.")
        return report

    report.customers_count = len(customers_map)

    # Estruturas para checagens de unicidade e colisão
    all_remote_cidrs: List[Tuple[str, ipaddress.IPv4Network]] = []
    seen_collector_ips: Dict[ipaddress.IPv4Address, str] = {}
    seen_gateway_ips: Dict[ipaddress.IPv4Address, str] = {}

    for cust_key, cust_info in customers_map.items():
        customer_id = cust_info.get("customer_id", cust_key)

        # ----------------------------------------------------------------------
        # A. Validação do IP do Coletor Privado
        # ----------------------------------------------------------------------
        collector_ip_str = cust_info.get("collector_ip")
        if not collector_ip_str:
            report.add_error(f"Cliente '{customer_id}': Parâmetro obrigatório 'collector_ip' não informado.")
        else:
            try:
                col_ip = ipaddress.ip_address(collector_ip_str)
                if col_ip.version != 4:
                    report.add_error(f"Cliente '{customer_id}': 'collector_ip' deve ser IPv4.")
                elif col_ip not in col_subnet:
                    report.add_error(
                        f"Cliente '{customer_id}': O IP do coletor '{col_ip}' está fora da "
                        f"subnet autorizada de collectors '{col_subnet}'."
                    )
                else:
                    first_usable = col_subnet.network_address + 4  # Azure reserva .0, .1, .2, .3
                    if col_ip < first_usable or col_ip == col_subnet.broadcast_address:
                        report.add_error(
                            f"Cliente '{customer_id}': O IP '{col_ip}' é reservado pela infraestrutura Azure "
                            f"(faixa utilizável para coletores inicia em {first_usable})."
                        )

                    if col_ip in seen_collector_ips:
                        report.add_error(
                            f"Cliente '{customer_id}': O IP de coletor '{col_ip}' colide com o cliente "
                            f"'{seen_collector_ips[col_ip]}'."
                        )
                    else:
                        seen_collector_ips[col_ip] = customer_id
            except ValueError as exc:
                report.add_error(f"Cliente '{customer_id}': 'collector_ip' inválido '{collector_ip_str}': {exc}")

        # ----------------------------------------------------------------------
        # B. Validação do IP do Gateway Remoto (LNG)
        # ----------------------------------------------------------------------
        gateway_ip_str = cust_info.get("gateway_ip")
        if not gateway_ip_str:
            report.add_error(f"Cliente '{customer_id}': Parâmetro obrigatório 'gateway_ip' não informado.")
        else:
            try:
                gw_ip = ipaddress.ip_address(gateway_ip_str)
                if gw_ip.version != 4:
                    report.add_error(f"Cliente '{customer_id}': 'gateway_ip' deve ser IPv4.")
                else:
                    # Unicidade entre clientes
                    if gw_ip in seen_gateway_ips:
                        report.add_error(
                            f"Cliente '{customer_id}': O IP público de gateway '{gw_ip}' já está em uso pelo cliente "
                            f"'{seen_gateway_ips[gw_ip]}'. Gateways remotos devem possuir IPs exclusivos."
                        )
                    else:
                        seen_gateway_ips[gw_ip] = customer_id

                    # Colisão com Public IP do VNG Azure
                    if str(gw_ip) in azure_public_ips:
                        report.add_error(
                            f"Cliente '{customer_id}': O gateway IP '{gw_ip}' coincide com o IP público "
                            f"do Virtual Network Gateway do Azure Hub."
                        )

                    # Avaliação de RFC 5737 vs Roteabilidade Real
                    if is_rfc5737(gw_ip):
                        if effective_allow_testnet:
                            report.add_warning(
                                f"[SANDBOX WARNING] Cliente '{customer_id}': O gateway_ip '{gw_ip}' pertence ao bloco "
                                f"documental RFC 5737 (TEST-NET). Autorizado estritamente no ambiente protegido 'monhub-dev'. "
                                f"Túneis IPsec reais não negociarão conectividade sobre a Internet pública."
                            )
                        else:
                            report.add_error(
                                f"[PRODUÇÃO BLOQUEIO] Cliente '{customer_id}': O gateway_ip '{gw_ip}' pertence à faixa "
                                f"documental RFC 5737 (TEST-NET). Endereços fictícios são proibidos no ambiente '{env_clean}'. "
                                f"É mandatório um endereço IPv4 público globalmente roteável."
                            )
                    else:
                        # Validação estrita de IPv4 Público Global
                        if gw_ip.is_loopback:
                            report.add_error(f"Cliente '{customer_id}': O gateway_ip '{gw_ip}' é endereço de loopback.")
                        elif gw_ip.is_link_local:
                            report.add_error(f"Cliente '{customer_id}': O gateway_ip '{gw_ip}' é endereço link-local (APIPA).")
                        elif gw_ip.is_multicast:
                            report.add_error(f"Cliente '{customer_id}': O gateway_ip '{gw_ip}' é endereço multicast.")
                        elif gw_ip.is_reserved or gw_ip.is_unspecified:
                            report.add_error(f"Cliente '{customer_id}': O gateway_ip '{gw_ip}' é um endereço reservado ou não especificado.")
                        elif gw_ip.is_private:
                            report.add_error(
                                f"Cliente '{customer_id}': O gateway_ip '{gw_ip}' é um endereço privado RFC 1918. "
                                f"Gateways remotos Site-to-Site exigem endereço IPv4 público."
                            )
                        elif not gw_ip.is_global:
                            report.add_error(
                                f"Cliente '{customer_id}': O gateway_ip '{gw_ip}' não é um endereço IPv4 globalmente roteável."
                            )
            except ValueError as exc:
                report.add_error(f"Cliente '{customer_id}': 'gateway_ip' inválido '{gateway_ip_str}': {exc}")

        # ----------------------------------------------------------------------
        # C. Validação das Redes Remotas do Cliente (CIDRs)
        # ----------------------------------------------------------------------
        remote_spaces = cust_info.get("remote_address_spaces", [])
        if not isinstance(remote_spaces, list) or not remote_spaces:
            report.add_error(
                f"Cliente '{customer_id}': Nenhuma rede remota declarada em 'remote_address_spaces'."
            )
        else:
            cust_cidrs: List[ipaddress.IPv4Network] = []
            for cidr_str in remote_spaces:
                try:
                    net = validate_cidr_syntax(cidr_str, customer_id)
                    if net is not None:
                        # 1. Colisão com VNet Azure Hub
                        if net.overlaps(hub_vnet):
                            if net == hub_vnet:
                                desc = "sobreposição exata com o super-bloco da VNet"
                            elif net.subnet_of(hub_vnet):
                                desc = "sub-rede contida dentro do espaço da VNet"
                            elif hub_vnet.subnet_of(net):
                                desc = "super-rede englobando a VNet"
                            else:
                                desc = "interseção parcial com a VNet"
                            report.add_error(
                                f"[CONFLITO VNET AZURE] Cliente '{customer_id}': O bloco '{net}' colide com a "
                                f"Virtual Network Hub '{hub_vnet}' ({desc})."
                            )

                        # 2. Colisão interna no próprio cliente
                        for prev_net in cust_cidrs:
                            if net.overlaps(prev_net):
                                report.add_error(
                                    f"[COLISÃO INTERNA] Cliente '{customer_id}': O bloco '{net}' sobrepõe o bloco "
                                    f"'{prev_net}' do próprio cliente."
                                )

                        cust_cidrs.append(net)
                        all_remote_cidrs.append((customer_id, net))
                        report.cidrs_count += 1
                except ValueError as exc:
                    report.add_error(str(exc))

    # --------------------------------------------------------------------------
    # D. Validação Cruzada Inter-Clientes (Customer-to-Customer Overlap)
    # --------------------------------------------------------------------------
    total_cidrs = len(all_remote_cidrs)
    for i in range(total_cidrs):
        cust_a, net_a = all_remote_cidrs[i]
        for j in range(i + 1, total_cidrs):
            cust_b, net_b = all_remote_cidrs[j]
            if cust_a != cust_b and net_a.overlaps(net_b):
                if net_a == net_b:
                    overlap_type = "overlap exato"
                elif net_b.subnet_of(net_a):
                    overlap_type = f"sub-rede contida em '{net_a}' de '{cust_a}'"
                elif net_a.subnet_of(net_b):
                    overlap_type = f"super-rede contendo '{net_a}' de '{cust_a}'"
                else:
                    overlap_type = "interseção parcial de blocos"

                report.add_error(
                    f"[COLISÃO INTER-CLIENTES] Cliente '{cust_a}' ({net_a}) colide com "
                    f"Cliente '{cust_b}' ({net_b}) -> {overlap_type}."
                )

    return report


def load_customers_file(file_path: Path) -> Dict[str, Any]:
    """Carrega e decodifica arquivo JSON de clientes."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Arquivo de clientes não encontrado: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def print_report(report: ValidationReport, quiet: bool = False) -> None:
    """Apresenta o relatório de validação no console com formatação clara."""
    if not quiet:
        print("=" * 78)
        print("AZURE MONITORING HUB — VALIDADOR DETERMINÍSTICO DE CIDR E CONECTIVIDADE (US-06)")
        print("=" * 78)
        mode_str = "SANDBOX / DEMONSTRAÇÃO (--allow-testnet ativo)" if report.allow_testnet_mode else "PRODUÇÃO / ESTRITO (Padrão de Segurança)"
        print(f"Ambiente Configurado : {report.environment or '[NÃO DEFINIDO]'}")
        print(f"Modo de Operação     : {mode_str}")
        print(f"Clientes Processados : {report.customers_count}")
        print(f"Prefixos Validados   : {report.cidrs_count}")
        print("-" * 78)

    if report.warnings:
        print("\n[AVISOS DETECTADOS]:")
        for warn in report.warnings:
            print(f"  ! {warn}")

    if not report.is_valid:
        print("\n[FALHAS DE CONFORMIDADE DETECTADAS]:")
        for err in report.errors:
            print(f"  X {err}")
        print("-" * 78)
        print("STATUS FINAL: [FALHA] Validação de sobreposição reprovada. Execução interrompida.")
        print("=" * 78)
    else:
        if not quiet:
            print("\nSTATUS FINAL: [SUCESSO] Todos os blocos CIDR, IPs de coletores e gateways são válidos e disjuntos.")
            print("=" * 78)


def main() -> int:
    """Ponto de entrada de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Validador determinístico de sobreposição de CIDRs e conectividade (US-06)."
    )
    parser.add_argument(
        "--file", "-f",
        type=Path,
        default=Path("data/customers.json"),
        help="Caminho do arquivo JSON canônico contendo os dados dos clientes (Padrão: data/customers.json).",
    )
    parser.add_argument(
        "--environment", "-e",
        type=str,
        default=os.getenv("MONHUB_ENVIRONMENT", ""),
        help="Ambiente de execução (obrigatório: 'monhub-dev' para sandbox, 'monhub-prod'/'production' para estrito).",
    )
    parser.add_argument(
        "--vnet-cidr",
        type=str,
        default=DEFAULT_VNET_CIDR,
        help=f"Bloco CIDR da Virtual Network Azure do Hub (Padrão: {DEFAULT_VNET_CIDR}).",
    )
    parser.add_argument(
        "--collectors-subnet",
        type=str,
        default=DEFAULT_COLLECTORS_SUBNET,
        help=f"Subnet de Collectors (Padrão: {DEFAULT_COLLECTORS_SUBNET}).",
    )
    parser.add_argument(
        "--allow-testnet",
        action="store_true",
        help="Permite o uso de IPs documentais RFC 5737 (TEST-NET). Autorizado EXCLUSIVAMENTE para 'monhub-dev'.",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Modo silencioso, suprime cabeçalhos e exibe apenas erros/warnings.",
    )

    args = parser.parse_args()

    # Validação adicional de proteção contra execução acidental em CI com flag indevida:
    strict_prod_env = os.getenv("CI_STRICT_PROD", "").lower() in ("true", "1", "yes")
    allow_testnet_requested = args.allow_testnet and not strict_prod_env

    try:
        customers_data = load_customers_file(args.file)
    except Exception as exc:
        print(f"ERRO FATAL: Falha ao carregar dados dos clientes: {exc}", file=sys.stderr)
        return 1

    report = validate_customer_dataset(
        data=customers_data,
        environment=args.environment,
        allow_testnet=allow_testnet_requested,
        vnet_cidr=args.vnet_cidr,
        collectors_subnet_cidr=args.collectors_subnet,
    )

    print_report(report, quiet=args.quiet)
    return 0 if report.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
