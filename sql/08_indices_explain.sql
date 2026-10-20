-- Etapa 2 - B4: roteiro reprodutivel dos tres estudos de desempenho
-- IMPORTANTE: nao inventa resultados. Execute no Workbench e registre os
-- planos/tempos reais antes e depois, junto com o volume de linhas.
USE clinica_fisioterapia;

SET @inicio = '2026-01-01 00:00:00';
SET @fim = '2027-01-01 00:00:00';
SET @paciente = 1;

-- Volume usado na interpretacao.
SELECT COUNT(*) AS linhas_agendamento FROM agendamento;
SELECT COUNT(*) AS linhas_vinculo_convenio FROM vinculo_convenio;

-- ---------------------------------------------------------------------------
-- ESTUDO 1 - AGENDAMENTO por status e intervalo de data
-- Antes de criar idx_agendamento_status_inicio, execute e capture:
EXPLAIN
SELECT id_agendamento, id_paciente, data_hora_inicio, status
FROM agendamento
WHERE status = 'agendado'
  AND data_hora_inicio >= @inicio
  AND data_hora_inicio < @fim;

EXPLAIN ANALYZE
SELECT id_agendamento, id_paciente, data_hora_inicio, status
FROM agendamento
WHERE status = 'agendado'
  AND data_hora_inicio >= @inicio
  AND data_hora_inicio < @fim;

CREATE INDEX idx_agendamento_status_inicio
    ON agendamento (status, data_hora_inicio);

-- Depois do indice: execute novamente os dois EXPLAIN acima e compare.

-- ---------------------------------------------------------------------------
-- ESTUDO 2 - VINCULO_CONVENIO por paciente e vigencia
-- Capture o plano antes de criar idx_vinculo_paciente_fim:
EXPLAIN
SELECT id_convenio, numero_carteirinha, data_inicio, data_fim
FROM vinculo_convenio
WHERE id_paciente = @paciente
  AND (data_fim IS NULL OR data_fim >= CURRENT_DATE());

EXPLAIN ANALYZE
SELECT id_convenio, numero_carteirinha, data_inicio, data_fim
FROM vinculo_convenio
WHERE id_paciente = @paciente
  AND (data_fim IS NULL OR data_fim >= CURRENT_DATE());

CREATE INDEX idx_vinculo_paciente_fim
    ON vinculo_convenio (id_paciente, data_fim);

-- Depois do indice: execute novamente os dois EXPLAIN acima e compare.

-- ---------------------------------------------------------------------------
-- ESTUDO 3 - AGENDAMENTO por paciente e periodo
-- Capture o plano antes de criar idx_agendamento_paciente_inicio:
EXPLAIN
SELECT id_agendamento, data_hora_inicio, data_hora_fim, status
FROM agendamento
WHERE id_paciente = @paciente
  AND data_hora_inicio >= @inicio
  AND data_hora_inicio < @fim;

EXPLAIN ANALYZE
SELECT id_agendamento, data_hora_inicio, data_hora_fim, status
FROM agendamento
WHERE id_paciente = @paciente
  AND data_hora_inicio >= @inicio
  AND data_hora_inicio < @fim;

CREATE INDEX idx_agendamento_paciente_inicio
    ON agendamento (id_paciente, data_hora_inicio);

-- Depois do indice: execute novamente os dois EXPLAIN acima e compare.
-- Se o banco for pequeno e nao houver ganho mensuravel, registre isso no
-- relatorio em vez de afirmar uma melhora que os dados nao mostram.
