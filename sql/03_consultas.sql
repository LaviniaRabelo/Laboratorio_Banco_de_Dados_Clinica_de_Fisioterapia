-- ============================================================================
-- 03_CONSULTAS.SQL — CONSULTAS DE VERIFICAÇÃO
-- Clínica de Fisioterapia | MySQL 8.0+
-- ============================================================================

-- ============================================================================
-- BÁSICAS 
-- ============================================================================

-- Q01 — Pergunta de negócio:
-- Quais são os pacientes cadastrados e suas respectivas datas de nascimento?
SELECT nome, data_nascimento
FROM paciente
ORDER BY nome;

-- Q02 — Pergunta de negócio:
-- Quais pacientes nasceram entre 01/01/1980 e 31/12/2000?
SELECT nome, data_nascimento
FROM paciente
WHERE data_nascimento BETWEEN '1980-01-01' AND '2000-12-31'
ORDER BY data_nascimento;

-- Q03 — Pergunta de negócio:
-- Quais procedimentos cujo nome contém a palavra "Reabilitação" estão cadastrados?
SELECT nome_procedimento, valor_tabela
FROM procedimento
WHERE nome_procedimento LIKE '%Reabilitação%'
ORDER BY nome_procedimento;

-- Q04 — Pergunta de negócio:
-- Quais pacientes possuem vínculo com os convênios Vitalis Saúde ou Saúde Plena?
SELECT DISTINCT p.nome
FROM paciente p
JOIN vinculo_convenio vc ON vc.id_paciente = p.id_paciente
JOIN convenio c ON c.id_convenio = vc.id_convenio
WHERE c.nome_convenio IN ('Vitalis Saúde', 'Saúde Plena')
ORDER BY p.nome;

-- Q05 — Pergunta de negócio:
-- Quais pacientes não possuem convênio ativo no momento?
-- A consulta utiliza LEFT JOIN e tratamento de NULL.
SELECT p.nome AS paciente, c.nome_convenio
FROM paciente p
LEFT JOIN vinculo_convenio vc
       ON vc.id_paciente = p.id_paciente
      AND vc.data_fim IS NULL
LEFT JOIN convenio c ON c.id_convenio = vc.id_convenio
WHERE c.id_convenio IS NULL
ORDER BY p.nome;

-- ============================================================================
-- JUNÇÕES E AGREGAÇÃO 
-- ============================================================================

-- Q06 — Pergunta de negócio:
-- Quais atendimentos estão agendados para 15/06/2026, mostrando paciente,
-- fisioterapeuta e sala?
SELECT a.data_hora_inicio,
       pac.nome AS paciente,
       prof.nome AS fisioterapeuta,
       s.numero_sala
FROM agendamento a
JOIN paciente pac ON pac.id_paciente = a.id_paciente
JOIN profissional prof ON prof.id_profissional = a.id_fisioterapeuta
JOIN sala s ON s.id_sala = a.id_sala
WHERE DATE(a.data_hora_inicio) = '2026-06-15'
ORDER BY a.data_hora_inicio;

-- Q07 — Pergunta de negócio:
-- Qual é o convênio ativo de cada paciente, incluindo quem não possui convênio ativo?
SELECT p.nome AS paciente, c.nome_convenio
FROM paciente p
LEFT JOIN vinculo_convenio vc
       ON vc.id_paciente = p.id_paciente
      AND vc.data_fim IS NULL
LEFT JOIN convenio c ON c.id_convenio = vc.id_convenio
ORDER BY p.nome;

-- Q08 — Pergunta de negócio:
-- Quais fisioterapeutas realizaram mais de 10 atendimentos?
SELECT prof.nome AS fisioterapeuta,
       COUNT(*) AS total_atendimentos
FROM agendamento a
JOIN profissional prof ON prof.id_profissional = a.id_fisioterapeuta
WHERE a.status = 'realizado'
GROUP BY prof.nome
HAVING COUNT(*) > 10
ORDER BY total_atendimentos DESC;

-- Q09 — Pergunta de negócio:
-- Qual foi o faturamento total e a quantidade de procedimentos realizados por procedimento?
SELECT proc.nome_procedimento,
       SUM(ia.valor_cobrado) AS faturamento_total,
       COUNT(*) AS quantidade_realizada
FROM item_agendamento ia
JOIN procedimento proc ON proc.id_procedimento = ia.id_procedimento
JOIN agendamento a ON a.id_agendamento = ia.id_agendamento
WHERE a.status = 'realizado'
GROUP BY proc.nome_procedimento
ORDER BY faturamento_total DESC;

-- Q10 — Pergunta de negócio:
-- Quantos atendimentos realizados ocorreram em cada sala, incluindo salas sem atendimento?
SELECT s.numero_sala,
       COUNT(a.id_agendamento) AS atendimentos_realizados
FROM sala s
LEFT JOIN agendamento a
       ON a.id_sala = s.id_sala
      AND a.status = 'realizado'
GROUP BY s.numero_sala
ORDER BY atendimentos_realizados DESC;

-- ============================================================================
-- AVANÇADAS
-- ============================================================================

-- Q11 — Pergunta de negócio:
-- Quais agendamentos possuem valor total acima da média dos valores dos
-- agendamentos realizados pelo mesmo fisioterapeuta?
-- A subconsulta interna é correlacionada ao fisioterapeuta da consulta externa.
SELECT a.id_agendamento,
       prof.nome AS fisioterapeuta,
       (SELECT SUM(ia.valor_cobrado)
          FROM item_agendamento ia
         WHERE ia.id_agendamento = a.id_agendamento) AS valor_total
FROM agendamento a
JOIN profissional prof ON prof.id_profissional = a.id_fisioterapeuta
WHERE (SELECT SUM(ia.valor_cobrado)
         FROM item_agendamento ia
        WHERE ia.id_agendamento = a.id_agendamento)
      > (SELECT AVG(sub_total.total_item)
           FROM (
                 SELECT ia2.id_agendamento,
                        SUM(ia2.valor_cobrado) AS total_item
                 FROM item_agendamento ia2
                 JOIN agendamento a2 ON a2.id_agendamento = ia2.id_agendamento
                 WHERE a2.id_fisioterapeuta = a.id_fisioterapeuta
                 GROUP BY ia2.id_agendamento
                ) sub_total)
ORDER BY valor_total DESC;

-- Q12 — Pergunta de negócio:
-- Quais convênios possuem pelo menos um procedimento com cobertura integral (100%)?
SELECT c.nome_convenio
FROM convenio c
WHERE EXISTS (
    SELECT 1
    FROM cobertura cob
    WHERE cob.id_convenio = c.id_convenio
      AND cob.percentual_cobertura = 100
)
ORDER BY c.nome_convenio;

-- Q13 — Pergunta de negócio:
-- Quais inconsistências de integridade relacionadas a regras de negócio
-- podem ser identificadas por consulta no cadastro e no histórico?
-- RN03: nascimento futuro;
-- RN05: profissional sem exatamente uma subclasse;
-- RN01: fisioterapeuta sem especialidade;
-- RN11: mais de um convênio ativo;
-- RN15: evolução anterior ao agendamento.
SELECT 'RN03_nascimento_futuro' AS tipo,
       p.id_paciente AS id_registro,
       p.nome AS descricao
FROM paciente p
WHERE p.data_nascimento > CURDATE()

UNION ALL

SELECT 'RN05_profissional_sem_subclasse' AS tipo,
       prof.id_profissional AS id_registro,
       prof.nome AS descricao
FROM profissional prof
WHERE NOT EXISTS (SELECT 1 FROM fisioterapeuta f WHERE f.id_profissional = prof.id_profissional)
  AND NOT EXISTS (SELECT 1 FROM recepcionista r WHERE r.id_profissional = prof.id_profissional)
  AND NOT EXISTS (SELECT 1 FROM administrativo ad WHERE ad.id_profissional = prof.id_profissional)

UNION ALL

SELECT 'RN01_fisioterapeuta_sem_especialidade' AS tipo,
       f.id_profissional AS id_registro,
       prof.nome AS descricao
FROM fisioterapeuta f
JOIN profissional prof ON prof.id_profissional = f.id_profissional
WHERE NOT EXISTS (
    SELECT 1
    FROM qualificacao q
    WHERE q.id_profissional = f.id_profissional
)

UNION ALL

SELECT 'RN11_multiplos_convenios_ativos' AS tipo,
       vc.id_paciente AS id_registro,
       p.nome AS descricao
FROM vinculo_convenio vc
JOIN paciente p ON p.id_paciente = vc.id_paciente
WHERE vc.data_fim IS NULL
GROUP BY vc.id_paciente, p.nome
HAVING COUNT(*) > 1

UNION ALL

SELECT 'RN15_evolucao_antes_do_agendamento' AS tipo,
       e.id_paciente AS id_registro,
       CONCAT('Evolução ', e.num_evolucao, ' / Agendamento ', e.id_agendamento) AS descricao
FROM evolucao e
JOIN agendamento a ON a.id_agendamento = e.id_agendamento
WHERE e.data_evolucao < DATE(a.data_hora_inicio)

ORDER BY tipo, id_registro;

-- Q14 — Pergunta de negócio:
-- Quais procedimentos foram registrados em agendamentos cujo fisioterapeuta
-- não possui qualificação na especialidade exigida pelo procedimento?
SELECT a.id_agendamento,
       ia.id_procedimento
FROM item_agendamento ia
JOIN agendamento a ON a.id_agendamento = ia.id_agendamento
JOIN procedimento p ON p.id_procedimento = ia.id_procedimento
WHERE NOT EXISTS (
    SELECT 1
    FROM qualificacao q
    WHERE q.id_profissional = a.id_fisioterapeuta
      AND q.id_especialidade = p.id_especialidade_exigida
);

-- Q15 — Pergunta de negócio:
-- Existem agendamentos com sobreposição de horário para o mesmo fisioterapeuta
-- ou para a mesma sala?
SELECT 'conflito_fisioterapeuta' AS tipo,
       a1.id_agendamento AS agendamento_1,
       a2.id_agendamento AS agendamento_2
FROM agendamento a1
JOIN agendamento a2
  ON a1.id_fisioterapeuta = a2.id_fisioterapeuta
 AND a1.id_agendamento < a2.id_agendamento
WHERE a1.data_hora_inicio < a2.data_hora_fim
  AND a2.data_hora_inicio < a1.data_hora_fim

UNION ALL

SELECT 'conflito_sala' AS tipo,
       a1.id_agendamento AS agendamento_1,
       a2.id_agendamento AS agendamento_2
FROM agendamento a1
JOIN agendamento a2
  ON a1.id_sala = a2.id_sala
 AND a1.id_agendamento < a2.id_agendamento
WHERE a1.data_hora_inicio < a2.data_hora_fim
  AND a2.data_hora_inicio < a1.data_hora_fim;
 AND a1.id_agendamento < a2.id_agendamento
WHERE a1.data_hora_inicio < a2.data_hora_fim
  AND a2.data_hora_inicio < a1.data_hora_fim;
