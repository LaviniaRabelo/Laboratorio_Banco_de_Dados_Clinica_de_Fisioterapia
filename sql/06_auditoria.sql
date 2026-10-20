-- Etapa 2 - B6: trilha de auditoria
-- Registra alteracoes cadastrais de PACIENTE e operacionais de AGENDAMENTO.
USE clinica_fisioterapia;

CREATE TABLE IF NOT EXISTS auditoria_alteracao (
    id_auditoria BIGINT NOT NULL AUTO_INCREMENT,
    entidade VARCHAR(32) NOT NULL,
    chave_registro VARCHAR(100) NOT NULL,
    operacao VARCHAR(10) NOT NULL,
    autor_banco VARCHAR(288) NOT NULL,
    usuario_aplicacao VARCHAR(128) NULL,
    id_conexao BIGINT UNSIGNED NOT NULL,
    ocorrido_em_utc DATETIME(6) NOT NULL,
    valores_anteriores JSON NOT NULL,
    valores_posteriores JSON NOT NULL,
    CONSTRAINT pk_auditoria_alteracao PRIMARY KEY (id_auditoria)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DELIMITER $$

DROP TRIGGER IF EXISTS trg_auditoria_paciente_update$$
CREATE TRIGGER trg_auditoria_paciente_update
AFTER UPDATE ON paciente
FOR EACH ROW
BEGIN
    INSERT INTO auditoria_alteracao (
        entidade, chave_registro, operacao, autor_banco,
        usuario_aplicacao, id_conexao, ocorrido_em_utc,
        valores_anteriores, valores_posteriores
    )
    VALUES (
        'PACIENTE', CAST(NEW.id_paciente AS CHAR), 'UPDATE', CURRENT_USER(),
        @usuario_aplicacao, CONNECTION_ID(), UTC_TIMESTAMP(6),
        JSON_OBJECT(
            'cpf', OLD.cpf,
            'nome', OLD.nome,
            'data_nascimento', OLD.data_nascimento,
            'logradouro', OLD.logradouro,
            'numero_endereco', OLD.numero_endereco,
            'bairro', OLD.bairro,
            'cidade', OLD.cidade,
            'uf', OLD.uf,
            'cep', OLD.cep,
            'id_paciente_indicador', OLD.id_paciente_indicador
        ),
        JSON_OBJECT(
            'cpf', NEW.cpf,
            'nome', NEW.nome,
            'data_nascimento', NEW.data_nascimento,
            'logradouro', NEW.logradouro,
            'numero_endereco', NEW.numero_endereco,
            'bairro', NEW.bairro,
            'cidade', NEW.cidade,
            'uf', NEW.uf,
            'cep', NEW.cep,
            'id_paciente_indicador', NEW.id_paciente_indicador
        )
    );
END$$

DROP TRIGGER IF EXISTS trg_auditoria_agendamento_update$$
CREATE TRIGGER trg_auditoria_agendamento_update
AFTER UPDATE ON agendamento
FOR EACH ROW
BEGIN
    INSERT INTO auditoria_alteracao (
        entidade, chave_registro, operacao, autor_banco,
        usuario_aplicacao, id_conexao, ocorrido_em_utc,
        valores_anteriores, valores_posteriores
    )
    VALUES (
        'AGENDAMENTO', CAST(NEW.id_agendamento AS CHAR), 'UPDATE', CURRENT_USER(),
        @usuario_aplicacao, CONNECTION_ID(), UTC_TIMESTAMP(6),
        JSON_OBJECT(
            'id_paciente', OLD.id_paciente,
            'id_fisioterapeuta', OLD.id_fisioterapeuta,
            'id_sala', OLD.id_sala,
            'data_hora_inicio', OLD.data_hora_inicio,
            'data_hora_fim', OLD.data_hora_fim,
            'status', OLD.status
        ),
        JSON_OBJECT(
            'id_paciente', NEW.id_paciente,
            'id_fisioterapeuta', NEW.id_fisioterapeuta,
            'id_sala', NEW.id_sala,
            'data_hora_inicio', NEW.data_hora_inicio,
            'data_hora_fim', NEW.data_hora_fim,
            'status', NEW.status
        )
    );
END$$

DELIMITER ;

-- Para evidenciar o usuario da aplicacao em um teste manual, antes do UPDATE:
-- SET @usuario_aplicacao = 'teste_auditoria';
-- SELECT * FROM auditoria_alteracao ORDER BY id_auditoria DESC;
