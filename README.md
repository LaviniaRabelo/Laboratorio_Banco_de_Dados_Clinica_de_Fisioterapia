# Clínica de Fisioterapia — Clínica Movimento Vital

Projeto Final da disciplina **Laboratório de Banco de Dados (GPE17M40083)**  
Bacharelado em Engenharia de Software — Universidade Católica de Brasília (UCB)

**Professor:** Samuel Novais Moura Júnior  
**Semestre:** 2026/2

> A aplicação utiliza a identidade visual **Clínica Movimento Vital**. O domínio acadêmico permanece sendo **Clínica de Fisioterapia**.

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

A aplicação foi desenvolvida em **Python/Flask**, integrada ao **MySQL 8**, e serve como instrumento para demonstrar CRUDs, consultas parametrizadas, relatório por `VIEW`, transações, integridade, segurança, auditoria, concorrência, índices, backup e restauração.

## Principais requisitos atendidos

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

- CRUD completo de Pacientes, Salas, Procedimentos e Convênios;
- duas consultas parametrizadas com junção e agregação;
- relatório financeiro alimentado por `vw_financeiro_agendamento`;
- operação multitabela em transação;
- tratamento de erros de integridade;
- SQL parametrizado e resistência a SQL Injection;
- credenciais fora do código-fonte;
- senha da aplicação armazenada por hash;
- três perfis de acesso no MySQL;
- `VIEW` restritiva;
- auditoria por gatilhos;
- teste de `COMMIT` e `ROLLBACK`;
- backup e restauração em banco separado;
- estudos de desempenho com índices e `EXPLAIN`.

## Correções da Etapa 1 incorporadas

A versão final incorpora as observações recebidas na primeira etapa, incluindo:

- alinhamento de `FORMA_PAGAMENTO` entre MER, dicionário, modelo lógico e banco;
- inclusão de `RATEIO_ITEM` e `PAGAMENTO`;
- cardinalidades mínimas e máximas nos relacionamentos;
- revisão da RN03 e da numeração das regras;
- aprofundamento da análise de 3FN/BCNF;
- inclusão completa dos atributos de endereço de Paciente;
- justificativa da entidade fraca `EVOLUCAO`;
- revisão da coerência entre fisioterapeutas, especialidades, procedimentos e vínculos de convênio.

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

## Estrutura final esperada

```text
clinica-fisioterapia/
├── README.md
├── .gitignore
├── .env.example
├── sql/
│   ├── 01_ddl.sql
│   ├── 02_carga.sql
│   ├── 03_consultas.sql
│   ├── 04_financeiro.sql
│   └── demais scripts da Etapa 2
├── app/
│   ├── app.py
│   ├── requirements.txt
│   ├── configurar.py
│   ├── configurar.bat
│   ├── iniciar.bat
│   ├── templates/
│   └── static/
└── docs/
    ├── relatorio-final.pdf
    ├── mer-revisado.pdf
    ├── modelo-logico-revisado.pdf
    └── evidencias/
```

## Como clonar

```bash
git clone https://github.com/LaviniaRabelo/Laboratorio_Banco_de_Dados_Clinica_de_Fisioterapia.git
cd Laboratorio_Banco_de_Dados_Clinica_de_Fisioterapia
```

## Banco de dados

Execute os scripts na ordem definida na entrega final. A sequência básica é:

```bash
mysql -u root -p < sql/01_ddl.sql
mysql -u root -p clinica_fisioterapia < sql/02_carga.sql
mysql -u root -p clinica_fisioterapia < sql/04_financeiro.sql
mysql -u root -p clinica_fisioterapia < sql/03_consultas.sql
```

Depois, execute os scripts adicionais de triggers, auditoria, segurança e índices usados na Etapa 2.

## Configuração da aplicação

Entre na pasta da aplicação:

```bash
cd app
```

Crie o ambiente virtual e instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crie o arquivo `.env` a partir do `.env.example`. O `.env` real **não deve ser versionado**.

Exemplo:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=clinica_fisioterapia
DB_USER=SEU_USUARIO_DO_BANCO
DB_PASSWORD=SUA_SENHA_DO_BANCO
APP_USERNAME=admin
APP_PASSWORD_HASH=SEU_HASH_DE_SENHA
SECRET_KEY=SUA_CHAVE_SECRETA
```

Inicie a aplicação com:

```powershell
.\iniciar.bat
```

ou:

```bash
python app.py
```

Normalmente a aplicação ficará disponível em:

```text
http://127.0.0.1:5000
```

## Segurança

A aplicação possui autenticação própria e o banco possui perfis separados de acesso. As credenciais reais devem permanecer fora do repositório. O projeto utiliza princípio do menor privilégio, `VIEW` restritiva e auditoria de alterações relevantes.

Dados de saúde são dados pessoais sensíveis. A carga acadêmica utiliza dados fictícios e a documentação discute os cuidados de acesso compatíveis com a LGPD.

## Backup e restauração

Foi realizado teste de backup e restauração em base separada, comparando registros da base original com a restaurada. O relatório final registra a política de retenção e a estratégia de teste de restauração.

## Documentação

A documentação final consolida a Etapa 1 revisada e a Etapa 2, incluindo transações, concorrência, segurança, auditoria, otimização, projeto físico, backup e restauração.

## Uso de inteligência artificial

O uso de ferramentas de IA está declarado no relatório, conforme o enunciado da disciplina. Todo código, consulta e decisão utilizados na entrega devem ser executados, revisados e compreendidos pela equipe.
