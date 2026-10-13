#!/usr/bin/env python3
"""
Suíte de Testes Unitários: Validador de Sobreposição de CIDRs (US-06)
Azure Monitoring Hub (monhub) - Versão 1.2

Testes positivos e negativos cobrindo:
- Baseline oficial dos clientes fictícios cust01, cust02 e cust03
- Modo sandbox com RFC 5737 restrito a 'monhub-dev' vs. Produção estrita
- Governança estrita de ambiente (ambiente ausente ou inconsistente deve falhar)
- Tentativa de bypass de --allow-testnet em ambientes de produção
- Colisão com a VNet Azure (exata, contida e englobante)
- Colisão inter-clientes e colisão interna
- Sintaxe estrita de rede IPv4 (host bits ativos)
- Conformidade RFC 1918 e limites de máscara (/8 a /29)
- Validação e unicidade de IPs de coletores e gateways
- Integridade e Fonte Única de Verdade (SSOT) de customers.json
"""

import copy
import json
import os
import sys
import unittest
from pathlib import Path

# Adiciona o diretório scripts ao path para importação modular
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_overlap import (
    DEFAULT_COLLECTORS_SUBNET,
    DEFAULT_VNET_CIDR,
    load_customers_file,
    validate_customer_dataset,
)


class TestEnvironmentGovernance(unittest.TestCase):
    """Testes de governança estrita de configuração de ambiente."""

    def setUp(self):
        self.baseline_file = REPO_ROOT / "data" / "customers.json"
        self.baseline_data = load_customers_file(self.baseline_file)

    def test_missing_environment_fails(self):
        """Execução com ambiente ausente (vazio/None) deve falhar imediatamente."""
        report = validate_customer_dataset(self.baseline_data, environment="", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[ERRO DE GOVERNANÇA]" in e and "ambiente está ausente" in e for e in report.errors))

    def test_inconsistent_environment_fails(self):
        """Execução com ambiente desconhecido/inválido deve falhar imediatamente."""
        report = validate_customer_dataset(self.baseline_data, environment="staging-custom", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[ERRO DE GOVERNANÇA]" in e and "inválido ou inconsistente" in e for e in report.errors))

    def test_allow_testnet_blocked_in_production_environment(self):
        """Tentativa de usar --allow-testnet em ambiente de produção (monhub-prod) deve ser bloqueada."""
        report = validate_customer_dataset(self.baseline_data, environment="monhub-prod", allow_testnet=True)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[PRODUÇÃO BLOQUEIO]" in e and "terminantemente proibida" in e for e in report.errors))

    def test_allow_testnet_authorized_in_monhub_dev_only(self):
        """A flag --allow-testnet é autorizada exclusivamente no ambiente protegido 'monhub-dev'."""
        report = validate_customer_dataset(self.baseline_data, environment="monhub-dev", allow_testnet=True)
        self.assertTrue(report.is_valid, f"Falhou no ambiente monhub-dev: {report.errors}")
        self.assertTrue(report.allow_testnet_mode)


class TestValidateOverlapBaseline(unittest.TestCase):
    """Testes com a baseline oficial aprovada do projeto."""

    def setUp(self):
        self.baseline_file = REPO_ROOT / "data" / "customers.json"
        self.assertTrue(
            self.baseline_file.is_file(),
            f"Arquivo de baseline não encontrado: {self.baseline_file}",
        )
        self.baseline_data = load_customers_file(self.baseline_file)

    def test_baseline_passes_in_sandbox_mode(self):
        """A baseline aprovada com IPs RFC 5737 deve passar com sucesso no modo sandbox ('monhub-dev')."""
        report = validate_customer_dataset(self.baseline_data, environment="monhub-dev", allow_testnet=True)
        self.assertTrue(report.is_valid, f"Baseline falhou no modo sandbox: {report.errors}")
        self.assertEqual(report.customers_count, 3)
        self.assertEqual(report.cidrs_count, 6)
        self.assertEqual(len(report.warnings), 3)
        for warn in report.warnings:
            self.assertIn("RFC 5737", warn)

    def test_baseline_is_rejected_in_production_mode(self):
        """A baseline com IPs RFC 5737 deve ser rejeitada no modo padrão de produção (monhub-prod)."""
        report = validate_customer_dataset(self.baseline_data, environment="monhub-prod", allow_testnet=False)
        self.assertFalse(report.is_valid, "Baseline com RFC 5737 não deveria ser aceita em modo produção.")
        self.assertEqual(len(report.errors), 3)
        for err in report.errors:
            self.assertIn("[PRODUÇÃO BLOQUEIO]", err)

    def test_baseline_with_real_public_ips_passes_in_production_mode(self):
        """Quando configurada com IPs públicos globais legítimos, a baseline passa em produção sem warnings."""
        prod_data = copy.deepcopy(self.baseline_data)
        prod_data["customers"]["cust01"]["gateway_ip"] = "200.100.50.10"
        prod_data["customers"]["cust02"]["gateway_ip"] = "200.100.50.20"
        prod_data["customers"]["cust03"]["gateway_ip"] = "200.100.50.30"

        report = validate_customer_dataset(prod_data, environment="monhub-prod", allow_testnet=False)
        self.assertTrue(report.is_valid, f"Falha com IPs públicos legítimos: {report.errors}")
        self.assertEqual(len(report.warnings), 0)
        self.assertEqual(len(report.errors), 0)


class TestVNetOverlap(unittest.TestCase):
    """Testes de colisão contra o super-bloco da Virtual Network do Hub Azure (10.240.0.0/20)."""

    def setUp(self):
        self.base_data = {
            "customers": {
                "cust01": {
                    "customer_id": "cust01",
                    "collector_ip": "10.240.1.10",
                    "gateway_ip": "200.10.10.1",
                    "remote_address_spaces": ["192.168.10.0/24"],
                }
            }
        }

    def test_exact_vnet_overlap_is_blocked(self):
        """Cliente solicitando exatamente o mesmo bloco da VNet (10.240.0.0/20) deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["remote_address_spaces"] = ["10.240.0.0/20"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[CONFLITO VNET AZURE]" in e and "sobreposição exata" in e for e in report.errors))

    def test_contained_subnet_overlap_is_blocked(self):
        """Cliente solicitando faixa interna à VNet (ex.: 10.240.1.0/24 ou 10.240.5.0/24) deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["remote_address_spaces"] = ["10.240.1.0/24"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[CONFLITO VNET AZURE]" in e and "sub-rede contida" in e for e in report.errors))

    def test_supernet_encompassing_vnet_is_blocked(self):
        """Cliente solicitando super-rede englobando a VNet (ex.: 10.0.0.0/8 ou 10.240.0.0/16) deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["remote_address_spaces"] = ["10.0.0.0/8"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[CONFLITO VNET AZURE]" in e and "super-rede englobando" in e for e in report.errors))


class TestCustomerToCustomerOverlap(unittest.TestCase):
    """Testes de colisão entre redes de clientes concorrentes."""

    def setUp(self):
        self.base_data = {
            "customers": {
                "cust01": {
                    "customer_id": "cust01",
                    "collector_ip": "10.240.1.10",
                    "gateway_ip": "200.10.10.1",
                    "remote_address_spaces": ["192.168.10.0/24"],
                },
                "cust02": {
                    "customer_id": "cust02",
                    "collector_ip": "10.240.1.11",
                    "gateway_ip": "200.10.10.2",
                    "remote_address_spaces": ["192.168.20.0/24"],
                },
            }
        }

    def test_exact_inter_customer_overlap_is_blocked(self):
        """Dois clientes utilizando exatamente o mesmo range remoto devem ser bloqueados."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust02"]["remote_address_spaces"] = ["192.168.10.0/24"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[COLISÃO INTER-CLIENTES]" in e and "overlap exato" in e for e in report.errors))

    def test_subnet_inter_customer_overlap_is_blocked(self):
        """Cliente cadastrando sub-rede contida em range de outro cliente deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust02"]["remote_address_spaces"] = ["192.168.10.128/25"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[COLISÃO INTER-CLIENTES]" in e and "sub-rede contida" in e for e in report.errors))

    def test_supernet_inter_customer_overlap_is_blocked(self):
        """Cliente cadastrando super-rede que abranja range de outro cliente deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust02"]["remote_address_spaces"] = ["192.168.0.0/16"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[COLISÃO INTER-CLIENTES]" in e and "super-rede contendo" in e for e in report.errors))

    def test_internal_customer_overlap_is_blocked(self):
        """Um mesmo cliente cadastrando ranges conflitantes entre si deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["remote_address_spaces"] = [
            "192.168.10.0/24",
            "192.168.10.0/25",
        ]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("[COLISÃO INTERNA]" in e for e in report.errors))


class TestCIDRSyntaxAndCompliance(unittest.TestCase):
    """Testes de sintaxe canônica e conformidade com RFC 1918."""

    def setUp(self):
        self.base_data = {
            "customers": {
                "cust01": {
                    "customer_id": "cust01",
                    "collector_ip": "10.240.1.10",
                    "gateway_ip": "200.10.10.1",
                    "remote_address_spaces": ["192.168.10.0/24"],
                }
            }
        }

    def test_host_bits_set_is_blocked(self):
        """Endereço de rede com bits de host ativos (ex.: 192.168.10.15/24) deve ser rejeitado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["remote_address_spaces"] = ["192.168.10.15/24"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("bits de host podem estar ativos" in e for e in report.errors))

    def test_public_ip_in_remote_spaces_is_blocked(self):
        """Endereço IP público (não RFC 1918) como range remoto deve ser rejeitado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["remote_address_spaces"] = ["8.8.8.0/24"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("não pertence às faixas privadas RFC 1918" in e for e in report.errors))

    def test_mask_smaller_than_8_is_blocked(self):
        """Máscara menor que /8 deve ser rejeitada."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["remote_address_spaces"] = ["10.0.0.0/7"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("aceita apenas máscaras entre /8 e /29" in e for e in report.errors))

    def test_mask_greater_than_29_is_blocked(self):
        """Máscara maior que /29 (ex.: /30 ou /32) deve ser rejeitada."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["remote_address_spaces"] = ["192.168.10.0/30"]

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("aceita apenas máscaras entre /8 e /29" in e for e in report.errors))


class TestCollectorAndGatewayIPs(unittest.TestCase):
    """Testes de validação dos IPs dos coletores e gateways remotos."""

    def setUp(self):
        self.base_data = {
            "customers": {
                "cust01": {
                    "customer_id": "cust01",
                    "collector_ip": "10.240.1.10",
                    "gateway_ip": "200.10.10.1",
                    "remote_address_spaces": ["192.168.10.0/24"],
                },
                "cust02": {
                    "customer_id": "cust02",
                    "collector_ip": "10.240.1.11",
                    "gateway_ip": "200.10.10.2",
                    "remote_address_spaces": ["192.168.20.0/24"],
                },
            }
        }

    def test_duplicate_collector_ip_is_blocked(self):
        """Dois coletores compartilhando o mesmo endereço IP privado devem ser bloqueados."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust02"]["collector_ip"] = "10.240.1.10"

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("IP de coletor '10.240.1.10' colide" in e for e in report.errors))

    def test_collector_ip_outside_subnet_is_blocked(self):
        """IP de coletor fora da subnet 10.240.1.0/24 deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["collector_ip"] = "10.240.2.10"

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("fora da subnet autorizada de collectors" in e for e in report.errors))

    def test_collector_ip_in_azure_reserved_range_is_blocked(self):
        """IPs reservados pelo Azure (.0 a .3 e .255) devem ser bloqueados para coletores."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["collector_ip"] = "10.240.1.1"

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("reservado pela infraestrutura Azure" in e for e in report.errors))

    def test_duplicate_gateway_ip_is_blocked(self):
        """Dois clientes com o mesmo IP público de gateway devem ser bloqueados."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust02"]["gateway_ip"] = "200.10.10.1"

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=False)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("já está em uso pelo cliente" in e for e in report.errors))

    def test_private_ip_as_gateway_is_blocked(self):
        """IP privado RFC 1918 configurado como gateway público deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["gateway_ip"] = "192.168.1.1"

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=True)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("endereço privado RFC 1918" in e for e in report.errors))

    def test_loopback_ip_as_gateway_is_blocked(self):
        """IP de loopback como gateway público deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        data["customers"]["cust01"]["gateway_ip"] = "127.0.0.1"

        report = validate_customer_dataset(data, environment="monhub-dev", allow_testnet=True)
        self.assertFalse(report.is_valid)
        self.assertTrue(any("endereço de loopback" in e for e in report.errors))

    def test_azure_vng_public_ip_collision_is_blocked(self):
        """IP de gateway de cliente colidindo com o IP do Azure VNG deve ser bloqueado."""
        data = copy.deepcopy(self.base_data)
        azure_vng_pip = "20.201.50.10"
        data["customers"]["cust01"]["gateway_ip"] = azure_vng_pip

        report = validate_customer_dataset(
            data,
            environment="monhub-dev",
            allow_testnet=False,
            azure_public_ips=[azure_vng_pip],
        )
        self.assertFalse(report.is_valid)
        self.assertTrue(any("coincide com o IP público do Virtual Network Gateway" in e for e in report.errors))


class TestSingleSourceOfTruth(unittest.TestCase):
    """Testes de conformidade do princípio Single Source of Truth (SSOT)."""

    def test_canonical_customers_file_exists(self):
        """O arquivo canônico data/customers.json deve existir na raiz do projeto."""
        canonical = REPO_ROOT / "data" / "customers.json"
        self.assertTrue(canonical.is_file(), f"Arquivo canônico {canonical} não encontrado.")

    def test_customers_json_contains_all_approved_customers(self):
        """O arquivo canônico deve conter exatamente os 3 clientes aprovados cust01, cust02, cust03."""
        canonical = REPO_ROOT / "data" / "customers.json"
        data = load_customers_file(canonical)
        customers = data.get("customers", {})
        self.assertIn("cust01", customers)
        self.assertIn("cust02", customers)
        self.assertIn("cust03", customers)
        self.assertEqual(len(customers), 3)


if __name__ == "__main__":
    unittest.main()
