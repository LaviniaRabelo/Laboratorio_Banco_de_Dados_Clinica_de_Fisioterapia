# Clínica de Fisioterapia — Clínica Movimento Vital

Projeto Final da disciplina **Laboratório de Banco de Dados (GPE17M40053)**  
Bacharelado em Engenharia de Software — Universidade Católica de Brasília (UCB)

**Professor:** Samuel Novais Moura Júnior  
**Semestre:** 2026/2

## Equipe

| Papel principal | Integrante |
|---|---|
| Analista de domínio | Francisco Italo Gomes de Oliveira |
| Modelagem de dados | Lavinia Rabelo de Paiva |
| Modelagem de dados — apoio | João Paulo da Silva Piau |
| Administração do banco | Isabela Dourado Inacio Brito |
| Desenvolvimento da aplicação | Gabriel Paulon da Matta / Lavinia Rabelo de Paiva |

## Sobre o projeto

O sistema modela e implementa uma clínica de fisioterapia com atendimentos particulares e conveniados. O domínio inclui pacientes, profissionais, especialidades, salas, procedimentos, agendamentos, convênios, coberturas, evolução clínica e, na Etapa 2, rateio financeiro e pagamentos.

A aplicação foi desenvolvida em **Python/Flask**, integrada ao **MySQL 8**, e é utilizada para demonstrar CRUDs, consultas parametrizadas, relatório por `VIEW`, transações, integridade, segurança, auditoria, concorrência, índices, backup e restauração.

A identidade visual da aplicação é **Clínica Movimento Vital**; o domínio acadêmico do projeto permanece **Clínica de Fisioterapia**.

## Principais artefatos

### Etapa 1

- 20 regras de negócio;
- MER em notação Chen;
- dicionário de dados;
- modelo lógico relacional;
- normalização até 3FN/BCNF;
- DDL com restrições nomeadas;
- carga de dados fictícios;
- 15 consultas de verificação.

### Etapa 2

- aplicação web em Python/Flask;
- CRUDs de Pacientes, Salas, Procedimentos e Convênios;
- duas consultas parametrizadas com junção e agregação;
- relatório financeiro alimentado por `vw_financeiro_agendamento`;
- operação multitabela em transação;
- tratamento de erros de integridade;
- SQL parametrizado e teste clássico de resistência a SQL Injection;
- credenciais fora do código-fonte;
- senha da aplicação armazenada por hash;
- três perfis de acesso no MySQL e `VIEW` restritiva;
- auditoria de Paciente e Agendamento;
- testes de `COMMIT` e `ROLLBACK`;
- experimento de concorrência com duas sessões independentes, bloqueio de linha e timeout 1205;
- três estudos de desempenho com `EXPLAIN` e `EXPLAIN ANALYZE`;
- backup e restauração em banco separado.

## Correções da Etapa 1 incorporadas

A revisão contempla as observações recebidas na primeira etapa, incluindo:

- alinhamento de `FORMA_PAGAMENTO` entre MER, dicionário, modelo lógico e banco;
- inclusão de `RATEIO_ITEM` e `PAGAMENTO`;
- cardinalidades mínimas e máximas nos relacionamentos;
- revisão da RN03 e da numeração das regras;
- aprofundamento da análise de 3FN/BCNF;
- inclusão completa dos atributos de endereço de Paciente;
- justificativa da entidade fraca `EVOLUCAO`;
- revisão da coerência entre fisioterapeutas, especialidades, procedimentos e vínculos de convênio;
- substituição da antiga Q07 por uma consulta distinta da Q05.

## Tecnologias

- MySQL 8.0+
- Python 3
- Flask
- PyMySQL
- Werkzeug
- python-dotenv
- Flask-WTF / CSRF
- HTML, CSS e JavaScript
- VS Code
- MySQL Workbench

## Estrutura do repositório

```text
Laboratorio_Banco_de_Dados_Clinica_de_Fisioterapia/
├── README.md
├── .gitignore
├── .env.example
├── sql/
│   ├── 01_ddl.sql
│   ├── 02_carga.sql
│   ├── 03_consultas.sql
│   ├── 04_financeiro.sql
│   ├── 05_triggers_regras.sql
│   ├── 06_auditoria.sql
│   ├── 07_seguranca_roles.sql
│   ├── 08_indices_explain.sql
│   ├── 09_acesso_aplicacao.sql
│   └── 10_teste_concorrencia.sql
├── app/
│   ├── app.py
│   ├── requirements.txt
│   ├── configurar.py
│   ├── configurar.bat
│   ├── iniciar.bat
│   ├── templates/
│   └── static/
└── docs/
    ├── MER.jpg
    ├── Relatorio Clinica de Fisioterapia.pdf
    ├── relatorio-etapa1.pdf
    └── evidencias/
        └── README.md
```

O relatório consolidado registra a Etapa 1 revisada e a Etapa 2. A versão final em PDF deve permanecer sincronizada com os scripts, o MER e as evidências versionadas no repositório.

## Como clonar

```bash
git clone https://github.com/LaviniaRabelo/Laboratorio_Banco_de_Dados_Clinica_de_Fisioterapia.git
cd Laboratorio_Banco_de_Dados_Clinica_de_Fisioterapia
```

## Reconstrução do banco

Os scripts de construção devem ser executados nesta ordem:

```bash
mysql -u root -p < sql/01_ddl.sql
mysql -u root -p clinica_fisioterapia < sql/02_carga.sql
mysql -u root -p clinica_fisioterapia < sql/04_financeiro.sql
mysql -u root -p clinica_fisioterapia < sql/05_triggers_regras.sql
mysql -u root -p clinica_fisioterapia < sql/06_auditoria.sql
mysql -u root -p clinica_fisioterapia < sql/07_seguranca_roles.sql
mysql -u root -p clinica_fisioterapia < sql/09_acesso_aplicacao.sql
mysql -u root -p clinica_fisioterapia < sql/03_consultas.sql
```

Os arquivos abaixo documentam e permitem reproduzir testes executados na Etapa 2; eles não fazem parte da reconstrução básica:

- `sql/08_indices_explain.sql` — três estudos de desempenho com volume, `EXPLAIN` e `EXPLAIN ANALYZE` antes/depois dos índices. O terceiro estudo utiliza `AUDITORIA_ALTERACAO`, substituindo o antigo teste de `AGENDAMENTO` por paciente/período porque o índice já existente era necessário a uma restrição de chave estrangeira.
- `sql/10_teste_concorrencia.sql` — experimento com duas sessões independentes, bloqueio da mesma linha de `AGENDAMENTO`, `innodb_lock_wait_timeout = 5`, erro 1205 e nova tentativa após `COMMIT`.

Os comandos que criam usuários utilizam `IDENTIFIED BY RANDOM PASSWORD`; guarde as senhas retornadas apenas localmente e não as versione.

## Configuração da aplicação

Entre na pasta da aplicação:

```bash
cd app
```

### Opção recomendada no Windows

Execute:

```powershell
.\configurar.bat
```

O script cria `.venv`, instala as dependências e chama `configurar.py`, que cria o arquivo local `app/.env` com a conexão do MySQL, hash da senha da aplicação e uma `SECRET_KEY` aleatória.

Depois, inicie com:

```powershell
.\iniciar.bat
```

### Configuração manual

Se quiser que o próprio projeto gere o `.env` e o hash da senha:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python configurar.py
```

Como alternativa, copie o modelo e preencha o arquivo manualmente:

```powershell
copy ..\.env.example .env
```

Nesse segundo caso, edite `app/.env` com valores válidos. Não execute `configurar.py` depois de criar manualmente o `.env`, pois ele não sobrescreve um arquivo já existente.

O `.env` real **não deve ser versionado**. O arquivo público `.env.example` contém apenas placeholders.

A aplicação normalmente ficará disponível em:

```text
http://127.0.0.1:5000
```

## Acesso à aplicação usado na demonstração da equipe

**Usuário:** `admin`  
**Senha:** `Clinica@2026`

Essas credenciais são apenas do login da aplicação acadêmica. Em uma reconstrução nova, `configurar.py` permite escolher outro usuário e outra senha. Elas não substituem as credenciais do MySQL.

## Segurança

A aplicação possui autenticação própria e o banco possui perfis separados de acesso. Credenciais reais do MySQL devem permanecer somente no arquivo local `app/.env`. O repositório ignora `.env`, ambientes virtuais, caches, backups e logs.

Dados de saúde são dados pessoais sensíveis. A carga acadêmica utiliza dados fictícios e a documentação discute menor privilégio, `VIEW` restritiva, hash de senha, auditoria e cuidados compatíveis com a LGPD.

## Backup e restauração

Foi realizado teste de backup e restauração em base separada, comparando registros da base original com a restaurada. O relatório registra a política de retenção, a estimativa de crescimento e a estratégia de teste de restauração.

## Evidências concluídas

Os testes finais já foram executados. O arquivo `docs/evidencias/README.md` descreve o que cada captura comprova e os nomes sugeridos para as imagens:

- `evidencia_sql_injection.png`;
- `evidencia_concorrencia.png`;
- `evidencia_b4_estudo1.png`;
- `evidencia_b4_estudo2.png`;
- `evidencia_b4_estudo3.png`;
- `evidencia_auditoria.png`.

As imagens devem ser mantidas junto ao relatório final para que a entrega preserve tanto os resultados escritos quanto as evidências visuais reais obtidas no Workbench e na aplicação.

## Uso de inteligência artificial

O uso de ferramentas de IA deve ser declarado no relatório conforme o enunciado da disciplina, incluindo todas as ferramentas efetivamente utilizadas. Todo código, consulta e decisão incluídos na entrega deve ser executado, revisado e compreendido pela equipe.
