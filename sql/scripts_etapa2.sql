USE clinica_fisioterapia;

-- criando os perfis de acesso
DROP USER IF EXISTS 'admin_clinica'@'localhost';
DROP USER IF EXISTS 'fisioterapeuta'@'localhost';
DROP USER IF EXISTS 'recepcionista'@'localhost';

-- IMPORTANTE: substitua as senhas de exemplo localmente antes de executar.
-- Não versionar senhas reais no GitHub.
CREATE USER 'admin_clinica'@'localhost' IDENTIFIED BY 'ALTERE_ESTA_SENHA_ADMIN';
CREATE USER 'fisioterapeuta'@'localhost' IDENTIFIED BY 'ALTERE_ESTA_SENHA_FISIO';
CREATE USER 'recepcionista'@'localhost' IDENTIFIED BY 'ALTERE_ESTA_SENHA_RECEPCAO';

-- view para esconder os dados da evolucao clinica (LGPD)
DROP VIEW IF EXISTS vw_historico_pacientes;
CREATE VIEW vw_historico_pacientes AS
SELECT 
    p.nome AS paciente, 
    e.data_evolucao, 
    f.nome AS fisio_responsavel, 
    e.descricao_evolucao
FROM evolucao e
JOIN paciente p ON e.id_paciente = p.id_paciente
JOIN profissional f ON e.id_fisioterapeuta_responsavel = f.id_profissional;

-- permissoes da recepcao (nao pode ver a evolucao)
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.paciente TO 'recepcionista'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.agendamento TO 'recepcionista'@'localhost';
GRANT SELECT ON clinica_fisioterapia.procedimento TO 'recepcionista'@'localhost';

-- permissoes do fisioterapeuta (acessa a view no lugar da tabela original)
GRANT SELECT ON clinica_fisioterapia.paciente TO 'fisioterapeuta'@'localhost';
GRANT SELECT ON clinica_fisioterapia.agendamento TO 'fisioterapeuta'@'localhost';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.vw_historico_pacientes TO 'fisioterapeuta'@'localhost';

-- permissao total pro admin
GRANT ALL PRIVILEGES ON clinica_fisioterapia.* TO 'admin_clinica'@'localhost';

-- tabela pra guardar historico de preco de procedimento
DROP TABLE IF EXISTS audita_procedimento;
CREATE TABLE audita_procedimento (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    id_procedimento INT,
    valor_antigo DECIMAL(10,2),
    valor_novo DECIMAL(10,2),
    data_mudanca DATETIME,
    usuario VARCHAR(50)
);

-- trigger de quando alterar o valor do procedimento
DELIMITER $$
DROP TRIGGER IF EXISTS trg_preco_procedimento $$
CREATE TRIGGER trg_preco_procedimento
AFTER UPDATE ON procedimento
FOR EACH ROW
BEGIN
    IF OLD.valor_tabela <> NEW.valor_tabela THEN
        INSERT INTO audita_procedimento (id_procedimento, valor_antigo, valor_novo, data_mudanca, usuario)
        VALUES (OLD.id_procedimento, OLD.valor_tabela, NEW.valor_tabela, NOW(), USER());
    END IF;
END $$
DELIMITER ;

-- tabela pra auditar agendamento cancelado
DROP TABLE IF EXISTS audita_cancelamento;
CREATE TABLE audita_cancelamento (
    id_log INT AUTO_INCREMENT PRIMARY KEY,
    id_agendamento INT,
    status_velho VARCHAR(15),
    status_novo VARCHAR(15),
    data_cancelamento DATETIME,
    usuario VARCHAR(50)
);

-- trigger de agendamento cancelado
DELIMITER $$
DROP TRIGGER IF EXISTS trg_cancela_agendamento $$
CREATE TRIGGER trg_cancela_agendamento
AFTER UPDATE ON agendamento
FOR EACH ROW
BEGIN
    IF OLD.status <> 'cancelado' AND NEW.status = 'cancelado' THEN
        INSERT INTO audita_cancelamento (id_agendamento, status_velho, status_novo, data_cancelamento, usuario)
        VALUES (OLD.id_agendamento, OLD.status, NEW.status, NOW(), USER());
    END IF;
END $$
DELIMITER ;
