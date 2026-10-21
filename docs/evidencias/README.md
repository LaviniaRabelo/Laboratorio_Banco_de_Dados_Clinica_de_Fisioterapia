# Evidências finais — Etapa 2

Esta pasta reúne as capturas usadas para comprovar os testes descritos no relatório consolidado da Clínica de Fisioterapia / Clínica Movimento Vital.

## 1. SQL Injection

**Arquivo sugerido:** `evidencia_sql_injection.png`

Teste executado na busca de Pacientes com a entrada clássica:

```text
' OR 1=1 --
```

A aplicação tratou a entrada como texto literal e retornou **0 pacientes**, em vez de transformar o conteúdo em parte executável da consulta SQL. A evidência é compatível com o uso de consultas parametrizadas no código da aplicação.

## 2. Concorrência e bloqueio

**Arquivo sugerido:** `evidencia_concorrencia.png`

O experimento foi realizado com duas sessões independentes do MySQL Workbench e nível de isolamento `REPEATABLE-READ`.

A primeira sessão iniciou uma transação e executou `UPDATE` sobre o agendamento de ID 1, mantendo o bloqueio da linha. Na segunda sessão foi configurado:

```sql
SET SESSION innodb_lock_wait_timeout = 5;
```

Ao tentar atualizar a mesma linha, a segunda sessão ficou aguardando e retornou:

```text
Error Code: 1205. Lock wait timeout exceeded; try restarting transaction
```

Após `COMMIT` na primeira sessão, uma nova tentativa da segunda sessão foi concluída normalmente, comprovando a liberação do lock.

O comando `SET status = status` foi usado para provocar o bloqueio sem alterar o valor de negócio armazenado.

## 3. B4 — Estudo 1

**Arquivo sugerido:** `evidencia_b4_estudo1.png`

Consulta analisada: `AGENDAMENTO` por `status` e intervalo de `data_hora_inicio`.

Índice estudado:

```sql
CREATE INDEX idx_agendamento_status_inicio
ON agendamento (status, data_hora_inicio);
```

Antes do índice, o plano mostrou varredura da tabela para o filtro. Depois da criação, o MySQL passou a considerar/utilizar o índice composto, com acesso do tipo `range` / `index range scan` para o período seletivo.

## 4. B4 — Estudo 2

**Arquivo sugerido:** `evidencia_b4_estudo2.png`

Consulta analisada: `VINCULO_CONVENIO` por paciente e vigência.

Índice estudado:

```sql
CREATE INDEX idx_vinculo_paciente_fim
ON vinculo_convenio (id_paciente, data_fim);
```

A tabela utilizada no teste possui volume reduzido. O plano mostrou que o otimizador ainda pode preferir a chave primária, portanto não foi alegado ganho artificial de desempenho. O resultado foi mantido como exemplo de análise crítica de um índice cujo benefício não é mensurável na base acadêmica atual.

## 5. B4 — Estudo 3

**Arquivo sugerido:** `evidencia_b4_estudo3.png`

O estudo final utiliza `AUDITORIA_ALTERACAO` filtrando por entidade e período.

Índice estudado:

```sql
CREATE INDEX idx_auditoria_entidade_data
ON auditoria_alteracao (entidade, ocorrido_em_utc);
```

Esse estudo substituiu o antigo teste de `AGENDAMENTO` por paciente/período, pois `idx_agendamento_paciente_inicio` já era necessário para suporte a uma chave estrangeira e não podia ser removido para produzir uma comparação válida de antes/depois.

Como a tabela de auditoria possui poucas linhas e já havia outro índice útil, o ganho foi pequeno ou inexistente, o que foi registrado como resultado real.

## 6. Auditoria

**Arquivo sugerido:** `evidencia_auditoria.png`

Os triggers de auditoria registram alterações em `PACIENTE` e `AGENDAMENTO`, contendo entidade, chave do registro, operação, autor do banco, usuário da aplicação, conexão, data/hora UTC e valores anteriores/posteriores.

Na evidência de Paciente foi registrada uma alteração de cidade, permitindo visualizar `cidade_antes` e `cidade_depois` a partir dos campos JSON `valores_anteriores` e `valores_posteriores`.

## Observação

As imagens correspondentes devem permanecer nesta mesma pasta junto ao relatório final. Os scripts reprodutíveis estão em:

- `sql/06_auditoria.sql`
- `sql/08_indices_explain.sql`
- `sql/10_teste_concorrencia.sql`

As capturas documentam resultados reais obtidos no MySQL Workbench e na aplicação web; não devem ser substituídas por resultados simulados.
