# Regras do Projeto — Azure Monitoring Hub

## Contexto obrigatório

Antes de realizar qualquer atividade, o agente deverá considerar:

- `PROJECT.md`
- `SECURITY.md`
- `.agents/rules/security-rules.md`
- `.agents/rules/naming-rules.md`

Em caso de conflito, as regras de segurança possuem prioridade.

## Escopo

O projeto possui o código: `monhub`

Ambiente inicial: `dev`

Região inicial: `Brazil South`

Resource Group autorizado: `rg-monhub-dev-brs`

Nenhum recurso deverá ser criado ou alterado fora do escopo autorizado.

## Infrastructure as Code

Recursos Azure deverão ser implementados através de Terraform sempre que tecnicamente aplicável.

Evitar criação manual de recursos que possam ser gerenciados pelo Terraform.

O código deverá ser:

- modular;
- reutilizável;
- parametrizado;
- legível;
- documentado.

Não duplicar código para onboarding de novos clientes.

## Fluxo de alteração

Toda alteração de infraestrutura deverá seguir:

1. Analisar requisito.
2. Avaliar impacto.
3. Alterar código.
4. Executar `terraform fmt`.
5. Executar `terraform validate`.
6. Executar `terraform plan`.
7. Revisar resultado.
8. Solicitar aprovação humana quando necessária.
9. Executar alteração autorizada.
10. Validar resultado.
11. Documentar evidências relevantes.

## Restrições

O agente não deverá:

- inventar requisitos;
- alterar decisões arquiteturais fundamentais sem justificativa;
- remover controles de segurança para facilitar uma implementação;
- utilizar dados reais de clientes;
- utilizar informações proprietárias do ambiente que originou o case;
- criar recursos fora do Resource Group autorizado;
- executar ações destrutivas sem autorização humana explícita.

## Documentação

Decisões arquiteturais relevantes deverão ser registradas como ADR.

Procedimentos operacionais reutilizáveis deverão ser documentados como runbooks.

Evidências públicas deverão ser sanitizadas antes de serem adicionadas ao repositório.