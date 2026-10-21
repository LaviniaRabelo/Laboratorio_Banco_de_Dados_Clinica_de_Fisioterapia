-- Etapa 2 - B4: estudos de desempenho com EXPLAIN / EXPLAIN ANALYZE
-- Clinica de Fisioterapia | MySQL 8.0+
--
-- Este roteiro foi alinhado aos testes finais executados no MySQL Workbench.
-- Os tres estudos devem ser executados em ambiente de teste, registrando:
--   1) volume de dados;
--   2) EXPLAIN antes;
--   3) EXPLAIN ANALYZE antes;
--   4) criacao do indice proposto;
--   5) EXPLAIN depois;
--   6) EXPLAIN ANALYZE depois;
--   7) interpretacao do ganho ou da ausencia de ganho.
--
-- IMPORTANTE: em bases pequenas o otimizador pode preferir outro indice ou
-- uma varredura simples. Isso deve ser registrado como resultado real, sem
-- inventar melhora de desempenho.

USE clinica_fisioterapia;

-- ==========================================================================
-- VOLUME DA BASE USADO NA INTERPRETACAO
-- ==========================================================================
SELECT COUNT(*) AS linhas_agendamento
FROM agendamento;

SELECT COUNT(*) AS linhas_vinculo_convenio
FROM vinculo_convenio;

SELECT COUNT(*) AS linhas_auditoria
FROM auditoria_alteracao;

-- ==========================================================================
-- ESTUDO 1 - AGENDAMENTO POR STATUS E INTERVALO DE DATA
-- Indice proposto: idx_agendamento_status_inicio(status, data_hora_inicio)
-- ==========================================================================
SET @inicio = '2026-10-01 00:00:00';
SET @fim    = '2026-11-01 00:00:00';

-- Conferencia dos dados do periodo.
SELECT status,
       COUNT(*) AS quantidade,
       MIN(data_hora_inicio) AS primeira_data,
       MAX(data_hora_inicio) AS ultima_data
FROM agendamento
GROUP BY status;

-- ANTES DO INDICE
EXPLAIN
SELECT id_agendamento,
       id_paciente,
       data_hora_inicio,
       status
FROM agendamento
WHERE status = 'agendado'
  AND data_hora_inicio >= @inicio
  AND data_hora_inicio < @fim;

EXPLAIN ANALYZE
SELECT id_agendamento,
       id_paciente,
       data_hora_inicio,
       status
FROM agendamento
WHERE status = 'agendado'
  AND data_hora_inicio >= @inicio
  AND data_hora_inicio < @fim;

-- Execute apenas se o indice ainda nao existir.
-- SHOW INDEX FROM agendamento WHERE Key_name = 'idx_agendamento_status_inicio';
CREATE INDEX idx_agendamento_status_inicio
    ON agendamento (status, data_hora_inicio);

-- DEPOIS DO INDICE
EXPLAIN
SELECT id_agendamento,
       id_paciente,
       data_hora_inicio,
       status
FROM agendamento
WHERE status = 'agendado'
  AND data_hora_inicio >= @inicio
  AND data_hora_inicio < @fim;

EXPLAIN ANALYZE
SELECT id_agendamento,
       id_paciente,
       data_hora_inicio,
       status
FROM agendamento
WHERE status = 'agendado'
  AND data_hora_inicio >= @inicio
  AND data_hora_inicio < @fim;

-- Resultado observado no teste final: o plano passou a utilizar o indice
-- composto com acesso do tipo range / index range scan para o filtro seletivo.

-- ==========================================================================
-- ESTUDO 2 - VINCULO_CONVENIO POR PACIENTE E VIGENCIA
-- Indice proposto: idx_vinculo_paciente_fim(id_paciente, data_fim)
-- ==========================================================================
SET @paciente = 1;
SET @data_referencia = '2026-10-21';

-- Conferencia da distribuicao dos vinculos ativos/vigentes.
SELECT id_paciente,
       COUNT(*) AS quantidade_vinculos
FROM vinculo_convenio
WHERE data_fim IS NULL
   OR data_fim >= @data_referencia
GROUP BY id_paciente
ORDER BY quantidade_vinculos DESC, id_paciente
LIMIT 5;

-- Verifique se o indice existe. Para repetir o estudo desde o estado "antes",
-- remova-o somente se ele nao for exigido por outra restricao.
-- SHOW INDEX FROM vinculo_convenio
-- WHERE Key_name = 'idx_vinculo_paciente_fim';
-- DROP INDEX idx_vinculo_paciente_fim ON vinculo_convenio;

-- ANTES DO INDICE
EXPLAIN
SELECT id_convenio,
       numero_carteirinha,
       data_inicio,
       data_fim
FROM vinculo_convenio
WHERE id_paciente = @paciente
  AND (data_fim IS NULL OR data_fim >= @data_referencia);

EXPLAIN ANALYZE
SELECT id_convenio,
       numero_carteirinha,
       data_inicio,
       data_fim
FROM vinculo_convenio
WHERE id_paciente = @paciente
  AND (data_fim IS NULL OR data_fim >= @data_referencia);

-- Execute apenas se o indice ainda nao existir.
CREATE INDEX idx_vinculo_paciente_fim
    ON vinculo_convenio (id_paciente, data_fim);

-- DEPOIS DO INDICE
EXPLAIN
SELECT id_convenio,
       numero_carteirinha,
       data_inicio,
       data_fim
FROM vinculo_convenio
WHERE id_paciente = @paciente
  AND (data_fim IS NULL OR data_fim >= @data_referencia);

EXPLAIN ANALYZE
SELECT id_convenio,
       numero_carteirinha,
       data_inicio,
       data_fim
FROM vinculo_convenio
WHERE id_paciente = @paciente
  AND (data_fim IS NULL OR data_fim >= @data_referencia);

-- No conjunto pequeno usado no trabalho, o otimizador pode continuar
-- preferindo a PRIMARY KEY. Isso e um resultado valido e deve ser explicado.

-- ==========================================================================
-- ESTUDO 3 - AUDITORIA POR ENTIDADE E PERIODO
-- Indice proposto: idx_auditoria_entidade_data(entidade, ocorrido_em_utc)
--
-- Este estudo substitui o antigo teste de AGENDAMENTO por paciente/periodo.
-- O indice idx_agendamento_paciente_inicio ja era necessario a uma FK e nao
-- podia ser removido para produzir uma comparacao valida de antes/depois.
-- ==========================================================================
SET @auditoria_inicio = '2026-10-19 00:00:00';
SET @auditoria_fim    = '2026-10-22 00:00:00';

-- Conferencia do volume por entidade.
SELECT entidade,
       COUNT(*) AS quantidade,
       MIN(ocorrido_em_utc) AS primeiro_registro,
       MAX(ocorrido_em_utc) AS ultimo_registro
FROM auditoria_alteracao
GROUP BY entidade;

-- Verifique se o indice do estudo ainda existe.
-- SHOW INDEX FROM auditoria_alteracao
-- WHERE Key_name = 'idx_auditoria_entidade_data';
-- Para repetir o estudo desde o estado "antes", remova apenas este indice de
-- teste, caso ele exista:
-- DROP INDEX idx_auditoria_entidade_data ON auditoria_alteracao;

-- ANTES DO INDICE
EXPLAIN
SELECT id_auditoria,
       entidade,
       operacao,
       usuario_aplicacao,
       ocorrido_em_utc
FROM auditoria_alteracao
WHERE entidade = 'PACIENTE'
  AND ocorrido_em_utc >= @auditoria_inicio
  AND ocorrido_em_utc < @auditoria_fim;

EXPLAIN ANALYZE
SELECT id_auditoria,
       entidade,
       operacao,
       usuario_aplicacao,
       ocorrido_em_utc
FROM auditoria_alteracao
WHERE entidade = 'PACIENTE'
  AND ocorrido_em_utc >= @auditoria_inicio
  AND ocorrido_em_utc < @auditoria_fim;

-- Execute apenas se o indice ainda nao existir.
CREATE INDEX idx_auditoria_entidade_data
    ON auditoria_alteracao (entidade, ocorrido_em_utc);

-- DEPOIS DO INDICE
EXPLAIN
SELECT id_auditoria,
       entidade,
       operacao,
       usuario_aplicacao,
       ocorrido_em_utc
FROM auditoria_alteracao
WHERE entidade = 'PACIENTE'
  AND ocorrido_em_utc >= @auditoria_inicio
  AND ocorrido_em_utc < @auditoria_fim;

EXPLAIN ANALYZE
SELECT id_auditoria,
       entidade,
       operacao,
       usuario_aplicacao,
       ocorrido_em_utc
FROM auditoria_alteracao
WHERE entidade = 'PACIENTE'
  AND ocorrido_em_utc >= @auditoria_inicio
  AND ocorrido_em_utc < @auditoria_fim;

-- Interpretacao esperada para a base atual: como a tabela de auditoria possui
-- poucas linhas e ja pode ter outro indice util, o ganho pode ser nulo ou muito
-- pequeno. O valor deste estudo e demonstrar a analise critica do plano real.
