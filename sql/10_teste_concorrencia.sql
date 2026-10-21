-- Etapa 2 - B3: experimento final de concorrencia
-- Clinica de Fisioterapia | MySQL 8.0+
--
-- ESTE ARQUIVO NAO DEVE SER EXECUTADO INTEIRO DE UMA VEZ.
-- Use duas abas/sessoes independentes do MySQL Workbench.
-- O objetivo e demonstrar bloqueio de linha, espera/timeout e liberacao apos
-- COMMIT, registrando conexoes diferentes e o nivel de isolamento real.

USE clinica_fisioterapia;

-- ==========================================================================
-- PREPARACAO - execute em AMBAS as sessoes
-- ==========================================================================
SELECT
    CONNECTION_ID() AS conexao,
    @@transaction_isolation AS isolamento;

-- No experimento final foram observadas conexoes diferentes e isolamento
-- REPEATABLE-READ.

-- ==========================================================================
-- SESSAO 1
-- ==========================================================================
-- Execute somente na primeira aba e mantenha a transacao aberta.

START TRANSACTION;

UPDATE agendamento
SET status = status
WHERE id_agendamento = 1;

-- Nao execute COMMIT ainda.
-- Mesmo sem alterar o valor de status, o UPDATE adquire bloqueio exclusivo
-- sobre a linha do agendamento 1 ate COMMIT ou ROLLBACK.

-- ==========================================================================
-- SESSAO 2
-- ==========================================================================
-- Em outra aba/conexao, execute:

-- SET SESSION innodb_lock_wait_timeout = 5;
-- START TRANSACTION;
--
-- UPDATE agendamento
-- SET status = status
-- WHERE id_agendamento = 1;
--
-- Enquanto a SESSAO 1 permanecer aberta, este UPDATE aguardara o bloqueio.
-- No experimento realizado, apos o limite configurado, o MySQL retornou:
-- Error Code: 1205. Lock wait timeout exceeded; try restarting transaction
--
-- Depois do erro, finalize a tentativa:
-- ROLLBACK;

-- ==========================================================================
-- LIBERACAO DO BLOQUEIO - volte para a SESSAO 1
-- ==========================================================================
COMMIT;

-- ==========================================================================
-- NOVA TENTATIVA - volte para a SESSAO 2
-- ==========================================================================
-- Depois do COMMIT da SESSAO 1, execute novamente:
--
-- START TRANSACTION;
--
-- UPDATE agendamento
-- SET status = status
-- WHERE id_agendamento = 1;
--
-- COMMIT;
--
-- A segunda tentativa deve concluir normalmente, demonstrando que o bloqueio
-- foi liberado pelo COMMIT da primeira sessao.

-- ==========================================================================
-- EVIDENCIA A REGISTRAR
-- ==========================================================================
-- A captura final deve mostrar, sempre que possivel:
--   * CONNECTION_ID() diferentes nas duas sessoes;
--   * @@transaction_isolation;
--   * START TRANSACTION da Sessao 1;
--   * UPDATE da mesma linha nas duas sessoes;
--   * erro 1205 / espera por bloqueio na Sessao 2;
--   * COMMIT da Sessao 1;
--   * nova tentativa bem-sucedida na Sessao 2.
--
-- O comando SET status = status foi usado de proposito para provocar o lock
-- sem modificar o valor de negocio armazenado.
