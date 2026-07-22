# Instalando um Segundo Azure AD Connect em Modo Staging (e Fazendo o Cutover com Segurança)

> Documentação de uma atividade real: instalação de um segundo servidor Azure AD Connect em modo Staging, atualização do que já estava em produção, e a transição (cutover) entre os dois sem interromper a sincronização do ambiente híbrido.

## O contexto

Se você já mexeu com identidade híbrida, sabe que o Azure AD Connect é uma peça meio "sagrada" do ambiente — é ele quem garante que os usuários do Active Directory local continuem sincronizados com o Azure AD (hoje Entra ID). O problema é: e se você precisa atualizar a versão dele, ou trocar o servidor onde ele roda, sem correr o risco de quebrar a sincronização que está funcionando?

É exatamente pra isso que existe o **modo Staging**. A ideia é simples: você instala um segundo Azure AD Connect, em outro servidor, configurado em modo Staging — ele faz todo o ciclo de sincronização normalmente (lê o AD, calcula o que mudaria), mas **não exporta nada** para o Active Directory nem para o Azure AD. Ou seja, ele "ensaia" a sincronização sem realmente aplicar mudanças. Isso te dá a chance de validar que tudo está configurado certinho antes de assumir a operação de verdade.

## O que eu fiz, na prática

A atividade teve duas partes: instalar esse segundo servidor em Staging, e depois atualizar o servidor que já estava em produção — sem deixar o ambiente sem sincronização em nenhum momento.

## Pré-requisitos que utilizei

Antes de sair instalando, valem alguns pontos de atenção que fazem diferença:

**Servidor e sistema operacional compatíveis**
O novo servidor precisa atender aos mesmos requisitos de sistema operacional e recursos que o Azure AD Connect exige — não dá pra simplesmente reaproveitar qualquer máquina disponível.

**Conectividade com o Active Directory e com o Azure**
O servidor precisa alcançar os Domain Controllers do ambiente (para ler os objetos do AD) e ter saída de internet para se comunicar com o Azure AD — sem isso, a instalação nem completa corretamente.

**Conta de serviço com permissão adequada**
O Azure AD Connect precisa de uma conta com permissão suficiente sobre o Active Directory para ler (e, quando não está em staging, também escrever) os objetos sincronizados. Vale confirmar essa permissão antes de iniciar a instalação, para não travar no meio do processo.

**Mesmas Unidades Organizacionais (OUs) configuradas**
Um ponto que costuma passar despercebido: o novo servidor precisa ser configurado para sincronizar exatamente as mesmas OUs que o servidor de produção já sincroniza. Se a seleção de OUs ficar diferente entre os dois, o comportamento do ambiente muda assim que você fizer a virada — e normalmente não é isso que você quer.

**Instalação em modo customizado, com Staging habilitado**
Na instalação, em vez de seguir o fluxo "Express", é preciso usar a opção de instalação customizada, que permite marcar explicitamente a opção **"Enable staging mode"** — é essa marcação que garante que o novo servidor não vai começar a exportar mudanças por conta própria.

## O processo de virada (cutover)

Depois que o novo servidor estava instalado e configurado em Staging, o processo seguiu mais ou menos assim:

1. **Deixar o novo servidor rodando em Staging por um tempo**, acompanhando os ciclos de sincronização para confirmar que ele estava calculando exatamente o que era esperado — sem exportar nada ainda.
2. **Comparar o "antes" e "depois"** da configuração de sincronização entre os dois servidores, para ter certeza de que estavam alinhados.
3. **Retirar o novo servidor do modo Staging**, tornando-o o servidor ativo (esse é o momento em que ele passa a exportar de fato para o AD e para o Azure AD).
4. **Colocar o servidor antigo em modo Staging** (ou desativá-lo, dependendo do plano), garantindo que só um servidor esteja ativo exportando por vez — ter dois servidores ativos ao mesmo tempo é uma configuração não suportada e pode causar conflito de sincronização.

## Desafios que apareceram no caminho

- **Garantir que nada fosse exportado antes da hora**: o maior cuidado durante todo o processo foi justamente esse — confirmar, seguidamente, que o novo servidor realmente estava em Staging e não ia disparar nenhuma exportação por engano enquanto ainda estava sendo validado.
- **Consistência de configuração entre os dois servidores**: qualquer diferença de escopo (OUs, regras de filtragem) entre o servidor antigo e o novo poderia gerar um comportamento inesperado assim que a virada acontecesse — validar essa consistência tomou boa parte do tempo.
- **Evitar janela de indisponibilidade de sincronização**: o objetivo era que a troca fosse transparente, sem período em que o ambiente ficasse sem nenhum servidor ativo sincronizando.

## O resultado

O ambiente passou a operar com o novo Azure AD Connect como servidor ativo, com a sincronização validada previamente em Staging antes de qualquer mudança real ser aplicada — e sem nenhuma interrupção perceptível na sincronização entre o Active Directory e o Azure AD durante a transição.

## O que eu levo desse projeto

Modo Staging existe justamente para dar segurança em operações desse tipo — a tentação é sempre "só atualizar direto", mas ter um ambiente de validação paralelo, mesmo que dê um pouco mais de trabalho, evita que um erro de configuração vire um incidente de sincronização em produção. Vale o tempo investido.

---
**Autor:** Danilo Lima — Cloud Architect | Senior Cloud Specialist
[LinkedIn](https://linkedin.com/in/danilo-lima-9ba0375a/)

> Nota: esta documentação descreve uma atividade real de identidade híbrida conduzida profissionalmente, com nome de cliente e dados de ambiente removidos por confidencialidade.
