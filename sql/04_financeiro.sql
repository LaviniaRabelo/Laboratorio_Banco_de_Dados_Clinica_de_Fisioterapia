-- Etapa 2: estrutura inicial de cobranca e pagamento do paciente.
-- Executar UMA VEZ, depois de 01_ddl.sql e 02_carga.sql.
-- Nao recria o banco nem atribui coberturas atuais ao historico existente.
-- MySQL 8.0.16+: CHECK precisa ser efetivamente aplicado.
USE clinica_fisioterapia;

CREATE TABLE forma_pagamento (
    id_forma_pagamento INT NOT NULL AUTO_INCREMENT,
    nome VARCHAR(40) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_forma_pagamento PRIMARY KEY (id_forma_pagamento),
    CONSTRAINT uq_forma_pagamento_nome UNIQUE (nome),
    CONSTRAINT ck_forma_pagamento_ativo CHECK (ativo IN (0, 1))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE rateio_item (
    id_agendamento INT NOT NULL,
    id_procedimento INT NOT NULL,
    id_convenio INT NULL,
    valor_base DECIMAL(10,2) NOT NULL,
    percentual_cobertura_aplicado DECIMAL(5,2) NOT NULL DEFAULT 0,
    valor_convenio DECIMAL(10,2)
        GENERATED ALWAYS AS
        (ROUND(valor_base * percentual_cobertura_aplicado / 100, 2)) STORED,
    valor_paciente DECIMAL(10,2)
        GENERATED ALWAYS AS
        (valor_base - ROUND(valor_base * percentual_cobertura_aplicado / 100, 2)) STORED,
    registrado_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT pk_rateio_item PRIMARY KEY (id_agendamento, id_procedimento),
    CONSTRAINT fk_rateio_item_item FOREIGN KEY (id_agendamento, id_procedimento)
        REFERENCES item_agendamento (id_agendamento, id_procedimento)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_rateio_item_convenio FOREIGN KEY (id_convenio)
        REFERENCES convenio (id_convenio)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_rateio_item_base CHECK (valor_base >= 0),
    CONSTRAINT ck_rateio_item_percentual CHECK
        (percentual_cobertura_aplicado BETWEEN 0 AND 100),
    CONSTRAINT ck_rateio_item_particular CHECK
        (id_convenio IS NOT NULL OR percentual_cobertura_aplicado = 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE pagamento (
    id_pagamento BIGINT NOT NULL AUTO_INCREMENT,
    id_agendamento INT NOT NULL,
    id_forma_pagamento INT NOT NULL,
    valor_pago DECIMAL(10,2) NOT NULL,
    pago_em DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT pk_pagamento PRIMARY KEY (id_pagamento),
    CONSTRAINT fk_pagamento_agendamento FOREIGN KEY (id_agendamento)
        REFERENCES agendamento (id_agendamento)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_pagamento_forma FOREIGN KEY (id_forma_pagamento)
        REFERENCES forma_pagamento (id_forma_pagamento)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_pagamento_valor CHECK (valor_pago > 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

INSERT INTO forma_pagamento (nome) VALUES
    ('Pix'), ('Dinheiro'), ('Cartão de débito'), ('Cartão de crédito');

CREATE VIEW vw_financeiro_agendamento AS
SELECT a.id_agendamento,
       a.id_paciente,
       a.data_hora_inicio,
       a.status AS status_agendamento,
       COALESCE(i.quantidade_itens, 0) AS quantidade_itens,
       COALESCE(r.quantidade_rateios, 0) AS quantidade_rateios,
       CASE
           WHEN COALESCE(i.quantidade_itens, 0) = 0 THEN 'sem_itens'
           WHEN COALESCE(r.quantidade_rateios, 0) <> i.quantidade_itens
               THEN 'rateio_pendente'
           ELSE 'rateio_completo'
       END AS situacao_rateio,
       r.valor_total,
       r.valor_convenio,
       r.valor_paciente,
       COALESCE(p.total_pago, 0.00) AS total_pago_paciente,
       CASE WHEN i.quantidade_itens > 0
                  AND r.quantidade_rateios = i.quantidade_itens
            THEN r.valor_paciente - COALESCE(p.total_pago, 0.00)
            ELSE NULL
       END AS saldo_paciente
FROM agendamento a
LEFT JOIN (
    SELECT id_agendamento, COUNT(*) AS quantidade_itens
    FROM item_agendamento GROUP BY id_agendamento
) i ON i.id_agendamento = a.id_agendamento
LEFT JOIN (
    SELECT id_agendamento, COUNT(*) AS quantidade_rateios,
           SUM(valor_base) AS valor_total,
           SUM(valor_convenio) AS valor_convenio,
           SUM(valor_paciente) AS valor_paciente
    FROM rateio_item GROUP BY id_agendamento
) r ON r.id_agendamento = a.id_agendamento
LEFT JOIN (
    SELECT id_agendamento, SUM(valor_pago) AS total_pago
    FROM pagamento GROUP BY id_agendamento
) p ON p.id_agendamento = a.id_agendamento;
