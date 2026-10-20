-- Etapa 2 - B3: roteiro do experimento de concorrencia
-- ESTE ARQUIVO NAO DEVE SER EXECUTADO INTEIRO DE UMA VEZ.
-- Use duas abas/sessoes independentes no MySQL Workbench.
USE clinica_fisioterapia;

-- Em AMBAS as sessoes, registre:
SELECT CONNECTION_ID() AS conexao, @@transaction_isolation AS isolamento;

-- SESSAO 1
-- START TRANSACTION;
-- SELECT id_agendamento, status
-- FROM agendamento
-- WHERE id_agendamento = 1
-- FOR UPDATE;
-- Mantenha a transacao aberta enquanto executa a Sessao 2.

-- SESSAO 2
-- START TRANSACTION;
-- SELECT id_agendamento, status
-- FROM agendamento
-- WHERE id_agendamento = 1
-- FOR UPDATE;
-- A consulta deve aguardar o bloqueio da Sessao 1 ser liberado.

-- Volte a SESSAO 1 e execute:
-- COMMIT;

-- Observe a SESSAO 2 prosseguir; depois finalize:
-- COMMIT;

-- Capture em uma unica evidencia os CONNECTION_ID() distintos, o nivel de
-- isolamento e o comportamento de espera/desbloqueio. Se usar outro ID de
-- agendamento, registre o valor escolhido no relatorio.
