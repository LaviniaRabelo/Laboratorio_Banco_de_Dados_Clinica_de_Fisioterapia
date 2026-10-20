-- Etapa 2 - regras de negocio reforcadas no banco
-- Executar depois de 01_ddl.sql, 02_carga.sql e 04_financeiro.sql.
USE clinica_fisioterapia;

DELIMITER $$

DROP TRIGGER IF EXISTS trg_paciente_data_nasc_bi$$
CREATE TRIGGER trg_paciente_data_nasc_bi
BEFORE INSERT ON paciente
FOR EACH ROW
BEGIN
    IF NEW.data_nascimento > CURRENT_DATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'RN03: data de nascimento nao pode ser futura';
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_paciente_data_nasc_bu$$
CREATE TRIGGER trg_paciente_data_nasc_bu
BEFORE UPDATE ON paciente
FOR EACH ROW
BEGIN
    IF NEW.data_nascimento > CURRENT_DATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'RN03: data de nascimento nao pode ser futura';
    END IF;
END$$

DELIMITER ;

-- RN07, RN08 e RN09 tambem sao validadas pela operacao transacional da
-- aplicacao, que usa consultas parametrizadas e SELECT ... FOR UPDATE.
-- RN05 e RN15 permanecem rastreadas na aplicacao/consultas de verificacao;
-- nao se declara aqui uma garantia que nao tenha sido implementada.
