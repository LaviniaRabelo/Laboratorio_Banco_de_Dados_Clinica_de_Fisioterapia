-- Etapa 2 - usuario tecnico da aplicacao Flask
-- Executar como administrador APOS criar as tabelas/views da Etapa 2.
-- A senha aleatoria retornada pelo CREATE USER deve ser colocada somente no
-- arquivo local app/.env, nunca no GitHub.
USE clinica_fisioterapia;

DROP USER IF EXISTS 'clinica_app'@'localhost';
CREATE USER 'clinica_app'@'localhost' IDENTIFIED BY RANDOM PASSWORD;

-- Leitura necessaria as telas, consultas e relatorio.
GRANT SELECT ON clinica_fisioterapia.paciente TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.sala TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.equipamento_sala TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.procedimento TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.especialidade TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.convenio TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.profissional TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.fisioterapeuta TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.qualificacao TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.agendamento TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.item_agendamento TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.vinculo_convenio TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.cobertura TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.forma_pagamento TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.rateio_item TO 'clinica_app'@'localhost';
GRANT SELECT ON clinica_fisioterapia.vw_financeiro_agendamento TO 'clinica_app'@'localhost';

-- Escritas efetivamente usadas pela aplicacao.
GRANT INSERT, UPDATE, DELETE ON clinica_fisioterapia.paciente TO 'clinica_app'@'localhost';
GRANT INSERT, UPDATE, DELETE ON clinica_fisioterapia.sala TO 'clinica_app'@'localhost';
GRANT INSERT, DELETE ON clinica_fisioterapia.equipamento_sala TO 'clinica_app'@'localhost';
GRANT INSERT, UPDATE, DELETE ON clinica_fisioterapia.procedimento TO 'clinica_app'@'localhost';
GRANT INSERT, UPDATE, DELETE ON clinica_fisioterapia.convenio TO 'clinica_app'@'localhost';
GRANT INSERT ON clinica_fisioterapia.vinculo_convenio TO 'clinica_app'@'localhost';
GRANT INSERT, UPDATE ON clinica_fisioterapia.agendamento TO 'clinica_app'@'localhost';
GRANT INSERT ON clinica_fisioterapia.item_agendamento TO 'clinica_app'@'localhost';
GRANT INSERT ON clinica_fisioterapia.rateio_item TO 'clinica_app'@'localhost';
GRANT INSERT ON clinica_fisioterapia.pagamento TO 'clinica_app'@'localhost';

SHOW GRANTS FOR 'clinica_app'@'localhost';
