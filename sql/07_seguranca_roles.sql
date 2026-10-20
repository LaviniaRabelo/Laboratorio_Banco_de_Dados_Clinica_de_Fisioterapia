-- Etapa 2 - B5: perfis de acesso, menor privilegio e view restritiva
-- Executar como administrador do MySQL.
USE clinica_fisioterapia;

CREATE OR REPLACE VIEW vw_agenda_recepcao AS
SELECT
    a.id_agendamento,
    p.nome AS paciente,
    a.data_hora_inicio,
    a.data_hora_fim,
    s.numero_sala,
    a.status
FROM agendamento a
JOIN paciente p ON p.id_paciente = a.id_paciente
JOIN sala s ON s.id_sala = a.id_sala;

DROP USER IF EXISTS 'clinica_recepcao'@'localhost';
DROP USER IF EXISTS 'clinica_fisio'@'localhost';
DROP USER IF EXISTS 'clinica_adm'@'localhost';

-- O MySQL retorna uma senha aleatoria para cada conta. Nao grave essas senhas
-- neste arquivo nem no GitHub; guarde-as somente para os testes locais.
CREATE USER 'clinica_recepcao'@'localhost' IDENTIFIED BY RANDOM PASSWORD;
CREATE USER 'clinica_fisio'@'localhost' IDENTIFIED BY RANDOM PASSWORD;
CREATE USER 'clinica_adm'@'localhost' IDENTIFIED BY RANDOM PASSWORD;

-- Recepcao: operacao cadastral/agenda, sem acesso a EVOLUCAO.
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.paciente
    TO 'clinica_recepcao'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.telefone_paciente
    TO 'clinica_recepcao'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.vinculo_convenio
    TO 'clinica_recepcao'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.agendamento
    TO 'clinica_recepcao'@'localhost';
GRANT SELECT, INSERT ON clinica_fisioterapia.item_agendamento
    TO 'clinica_recepcao'@'localhost';
GRANT SELECT ON clinica_fisioterapia.sala TO 'clinica_recepcao'@'localhost';
GRANT SELECT ON clinica_fisioterapia.procedimento TO 'clinica_recepcao'@'localhost';
GRANT SELECT ON clinica_fisioterapia.convenio TO 'clinica_recepcao'@'localhost';
GRANT SELECT ON clinica_fisioterapia.vw_agenda_recepcao TO 'clinica_recepcao'@'localhost';

-- Demonstracao de REVOKE pedida no trabalho: o privilegio e concedido e
-- retirado na sequencia; o estado final permanece de menor privilegio.
GRANT DELETE ON clinica_fisioterapia.paciente TO 'clinica_recepcao'@'localhost';
REVOKE DELETE ON clinica_fisioterapia.paciente FROM 'clinica_recepcao'@'localhost';

-- Fisioterapeuta: leitura operacional e manutencao da evolucao clinica.
GRANT SELECT ON clinica_fisioterapia.paciente TO 'clinica_fisio'@'localhost';
GRANT SELECT ON clinica_fisioterapia.agendamento TO 'clinica_fisio'@'localhost';
GRANT SELECT ON clinica_fisioterapia.procedimento TO 'clinica_fisio'@'localhost';
GRANT SELECT ON clinica_fisioterapia.especialidade TO 'clinica_fisio'@'localhost';
GRANT SELECT ON clinica_fisioterapia.qualificacao TO 'clinica_fisio'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.evolucao TO 'clinica_fisio'@'localhost';

-- Administrativo: financeiro e convenios; sem acesso a EVOLUCAO.
GRANT SELECT ON clinica_fisioterapia.paciente TO 'clinica_adm'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.convenio TO 'clinica_adm'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.cobertura TO 'clinica_adm'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.forma_pagamento TO 'clinica_adm'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.rateio_item TO 'clinica_adm'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.pagamento TO 'clinica_adm'@'localhost';
GRANT SELECT ON clinica_fisioterapia.vw_financeiro_agendamento TO 'clinica_adm'@'localhost';

-- Evidencias recomendadas:
-- SHOW GRANTS FOR 'clinica_recepcao'@'localhost';
-- SHOW GRANTS FOR 'clinica_fisio'@'localhost';
-- SHOW GRANTS FOR 'clinica_adm'@'localhost';
