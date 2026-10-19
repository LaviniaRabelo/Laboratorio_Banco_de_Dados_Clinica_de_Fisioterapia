# Clínica de Fisioterapia — Clínica Movimento Vital

Projeto Final da disciplina **Laboratório de Banco de Dados (GPE17M40083)**  
Bacharelado em Engenharia de Software — Universidade Católica de Brasília (UCB)

**Professor:** Samuel Novais Moura Júnior  
**Semestre:** 2026/2  

> A aplicação utiliza a identidade visual **Clínica Movimento Vital**. O domínio acadêmico do projeto permanece sendo **Clínica de Fisioterapia**.

---

## Equipe

| Papel principal | Integrante |
|---|---|
| Analista de domínio | Francisco Italo Gomes de Oliveira |
| Modelagem de dados | Lavinia Rabelo de Paiva |
| Modelagem de dados — apoio | João Paulo da Silva Piau |
| Administração do banco | Isabela Dourado Inacio Brito |
| Desenvolvimento da aplicação | Gabriel Paulon da Matta / Lavinia Rabelo de Paiva |

> A divisão acima registra a responsabilidade principal de cada integrante. Todos participaram do projeto e devem conhecer o funcionamento geral do banco e da aplicação.

---

## Sobre o projeto

O projeto modela e implementa o funcionamento de uma clínica de fisioterapia com atendimentos **particulares e conveniados**, contemplando as especialidades ortopédica, neurológica, respiratória e desportiva.

O sistema abrange:

- cadastro de pacientes e profissionais;
- especialização de profissionais em fisioterapeuta, recepcionista e administrativo;
- cadastro de salas, equipamentos, procedimentos e especialidades;
- agendamento de sessões;
- validação de disponibilidade de sala e fisioterapeuta;
- verificação da especialidade exigida pelo procedimento;
- convênios, vínculos e cobertura de procedimentos;
- histórico de evolução clínica;
- rateio financeiro entre convênio e paciente;
- formas de pagamento e registro de pagamentos;
- consultas parametrizadas;
- relatório financeiro consolidado por `VIEW`;
- autenticação da aplicação;
- controle de acesso no banco;
- auditoria de alterações;
- transações, rollback, backup, restauração e estudos de desempenho.

A Etapa 2 evolui o banco desenvolvido na Etapa 1 para uma aplicação web funcional em **Python/Flask**, integrada ao **MySQL 8**.

---

## Principais requisitos atendidos

### Etapa 1

- 20 regras de negócio numeradas e rastreáveis;
- autorrelacionamento de Paciente;
- generalização/especialização de Profissional;
- entidade fraca `EVOLUCAO`;
- relacionamentos N:N com tabelas associativas;
- dicionário de dados;
- modelo lógico relacional;
- análise de normalização até 3FN/BCNF;
- DDL com PK, FK, UNIQUE, CHECK e índices;
- carga de dados fictícios;
- 15 consultas de verificação.

### Etapa 2

- CRUD completo de Pacientes;
- CRUD completo de Salas;
- CRUD completo de Procedimentos;
- CRUD completo de Convênios;
- duas consultas parametrizadas com junção e agregação;
- relatório financeiro alimentado por `vw_financeiro_agendamento`;
- operação de agendamento com alterações em múltiplas tabelas dentro de uma transação;
- tratamento de erros de integridade;
- consultas SQL parametrizadas;
- credenciais fora do código-fonte;
- senha da aplicação armazenada por hash;
- perfis de acesso distintos no MySQL;
- `VIEW` restritiva para acesso controlado;
- gatilhos e tabela de auditoria;
- teste de `COMMIT` e `ROLLBACK`;
- teste de backup e restauração em banco separado;
- estudo de índices e planos de execução.

---

## Correções incorporadas após a Etapa 1

A Etapa 2 também incorpora as correções solicitadas na devolutiva da primeira etapa.

Entre os principais ajustes estão:

- inclusão de `FORMA_PAGAMENTO` no modelo físico e na documentação;
- inclusão das estruturas financeiras `RATEIO_ITEM` e `PAGAMENTO`;
- revisão das cardinalidades mínimas e máximas;
- alinhamento da numeração das regras de negócio;
- correção da implementação/documentação da RN03;
- aprofundamento da análise de 3FN/BCNF;
- inclusão completa dos atributos de endereço de Paciente no modelo lógico;
- aprofundamento da justificativa da entidade fraca `EVOLUCAO`;
- revisão da coerência entre fisioterapeutas, especialidades e procedimentos;
- revisão da coerência dos vínculos de convênio;
- revisão das consultas de verificação.

---

## Tecnologias utilizadas

- **SGBD:** MySQL 8.0+
- **Aplicação:** Python 3 + Flask
- **Acesso ao banco:** PyMySQL
- **Autenticação:** Werkzeug
- **Configuração:** `python-dotenv`
- **Proteção de formulários:** Flask-WTF / CSRF
- **Frontend:** HTML, CSS e JavaScript
- **Ferramentas de desenvolvimento:** VS Code e MySQL Workbench

---

## Estrutura recomendada do repositório

```text
clinica-fisioterapia/
├── README.md
├── .gitignore
├── .env.example
│
├── sql/
│   ├── 01_ddl.sql
│   ├── 02_carga.sql
│   ├── 03_consultas.sql
│   ├── 04_financeiro.sql
│   └── demais scripts da Etapa 2
│
├── app/
│   ├── app.py
│   ├── requirements.txt
│   ├── configurar.py
│   ├── configurar.bat
│   ├── iniciar.bat
│   ├── templates/
│   └── static/
│
└── docs/
    ├── relatorio-final.pdf
    ├── mer-revisado.pdf
    ├── modelo-logico-revisado.pdf
    └── evidencias/
```

> Os scripts de auditoria, segurança, gatilhos e índices podem ser mantidos em arquivos SQL separados dentro de `sql/`, conforme a organização final adotada pela equipe.

---

# Como executar o projeto

## 1. Pré-requisitos

Instale:

- MySQL 8.0 ou superior;
- Python 3;
- MySQL Workbench, DBeaver ou outro cliente compatível;
- Git, caso o repositório seja clonado diretamente.

---

## 2. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
cd clinica-fisioterapia
```

Substitua `URL_DO_REPOSITORIO` pela URL real do repositório no GitHub.

---

## 3. Criar o banco

Execute o script principal em uma instância MySQL:

```bash
mysql -u root -p < sql/01_ddl.sql
```

O script cria o banco `clinica_fisioterapia` e as estruturas principais da Etapa 1.

---

## 4. Carregar os dados iniciais

```bash
mysql -u root -p clinica_fisioterapia < sql/02_carga.sql
```

A carga utiliza dados fictícios preparados para o domínio acadêmico.

---

## 5. Aplicar a estrutura financeira da Etapa 2

```bash
mysql -u root -p clinica_fisioterapia < sql/04_financeiro.sql
```

Esse script cria, entre outras estruturas:

- `forma_pagamento`;
- `rateio_item`;
- `pagamento`;
- `vw_financeiro_agendamento`.

---

## 6. Aplicar os demais scripts da Etapa 2

Execute os scripts adicionais de integridade, auditoria, segurança e índices **na ordem definida na pasta `sql/` do repositório final**.

Esses scripts devem conter, conforme a versão final do projeto:

- regras implementadas por trigger;
- tabela e gatilhos de auditoria;
- usuários e permissões;
- `VIEW` de restrição;
- índices utilizados nos estudos de desempenho.

---

## 7. Executar as consultas de verificação

```bash
mysql -u root -p clinica_fisioterapia < sql/03_consultas.sql
```

O arquivo contém 15 consultas comentadas, divididas em consultas básicas, consultas com junção/agregação e consultas avançadas.

---

# Configuração da aplicação

## 8. Entrar na pasta da aplicação

```bash
cd app
```

---

## 9. Criar e ativar um ambiente virtual

### Windows — PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Windows — Prompt de Comando

```cmd
python -m venv .venv
.venv\Scripts\activate
```

---

## 10. Instalar as dependências

```bash
pip install -r requirements.txt
```

---

## 11. Configurar as variáveis de ambiente

O arquivo `.env` contém informações sensíveis e **não deve ser versionado**.

Use o `.env.example` como referência e crie um arquivo chamado:

```text
.env
```

Exemplo de estrutura:

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=clinica_fisioterapia
DB_USER=SEU_USUARIO_DO_BANCO
DB_PASSWORD=SUA_SENHA_DO_BANCO

APP_USERNAME=admin
APP_PASSWORD_HASH=HASH_DA_SENHA

SECRET_KEY=UMA_CHAVE_SECRETA
```

Não publique senhas reais, hashes de produção ou chaves secretas no GitHub.

---

## 12. Configuração inicial

Quando necessário, execute:

```powershell
.\configurar.bat
```

ou:

```bash
python configurar.py
```

---

## 13. Iniciar a aplicação

No Windows:

```powershell
.\iniciar.bat
```

ou diretamente:

```bash
python app.py
```

A aplicação será disponibilizada localmente no endereço exibido pelo Flask, normalmente:

```text
http://127.0.0.1:5000
```

---

# Segurança

O projeto utiliza duas camadas distintas de autenticação e autorização.

### Aplicação

A interface Flask possui autenticação própria. A senha não é mantida em texto claro no código-fonte; a aplicação trabalha com hash de senha armazenado por variável de ambiente.

### Banco de dados

Foram definidos perfis distintos no MySQL aplicando o princípio do menor privilégio, incluindo:

- recepção;
- fisioterapeuta;
- administrativo.

Esses usuários do MySQL **não são os mesmos usuários da tela de login da aplicação**.

Também foi utilizada uma `VIEW` restritiva para disponibilizar somente os dados necessários a determinado perfil.

---

# Dados pessoais e LGPD

O projeto manipula dados que, em um ambiente real, exigiriam cuidados especiais.

Entre eles estão:

- nome;
- CPF;
- endereço;
- telefone;
- dados de convênio;
- registros de evolução e demais informações clínicas.

Dados referentes à saúde são considerados dados pessoais sensíveis. Por isso, o projeto aplica separação de privilégios, autenticação, controle de acesso e evita o uso de dados pessoais reais de terceiros na carga acadêmica.

---

# Transações

A principal operação transacional é o **agendamento de atendimento**.

A operação pode envolver, em uma única transação:

- criação do registro em `agendamento`;
- inclusão dos procedimentos em `item_agendamento`;
- geração dos rateios em `rateio_item`;
- registro de pagamento, quando aplicável.

A aplicação executa `COMMIT` somente quando todas as operações necessárias são concluídas. Em caso de falha, é executado `ROLLBACK`, preservando a atomicidade.

---

# Relatório financeiro

O relatório consolidado da aplicação utiliza a visão:

```sql
vw_financeiro_agendamento
```

Ela consolida:

- quantidade de itens;
- situação do rateio;
- valor total do atendimento;
- valor atribuído ao convênio;
- valor atribuído ao paciente;
- total já pago;
- saldo do paciente.

---

# Backup e restauração

Foi realizado um teste de backup e restauração em uma base separada.

A validação comparou registros da base original e da base restaurada, confirmando a equivalência dos dados testados.

A política documentada para um ambiente real considera:

- backups regulares;
- retenção por período;
- armazenamento seguro;
- testes periódicos de restauração.

---

# Documentação

O relatório final consolidado incorpora:

- Etapa 1 revisada;
- correções da devolutiva do professor;
- Etapa 2;
- evidências dos testes práticos;
- decisões de segurança;
- transações;
- auditoria;
- otimização;
- projeto físico;
- backup e restauração.

Os documentos finais devem ser mantidos na pasta:

```text
docs/
```

---

# Uso de inteligência artificial

O uso de ferramentas de IA foi declarado no relatório do projeto.

Foram utilizadas como apoio para:

- revisão de documentação;
- organização textual;
- apoio na revisão de SQL;
- apoio no desenvolvimento da aplicação;
- revisão de consistência;
- criação de material de estudo e apresentação.

Todo código, consulta e decisão utilizados na entrega devem ser revisados, executados e compreendidos pela equipe antes da apresentação.

---

## Observação final

Este repositório foi desenvolvido como projeto acadêmico da disciplina **Laboratório de Banco de Dados** da Universidade Católica de Brasília, no semestre **2026/2**.
