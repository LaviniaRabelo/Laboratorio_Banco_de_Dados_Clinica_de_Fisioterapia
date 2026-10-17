import streamlit as st
import mysql.connector
import json
import pandas as pd

# pegando as credenciais do json pra nao deixar a senha solta no codigo
with open('db_config.json') as f:
    config = json.load(f)

def conectar():
    return mysql.connector.connect(**config)

st.set_page_config(page_title="Clínica Fisio", layout="wide")
st.sidebar.title("Menu")

menu = st.sidebar.radio("Navegação:", [
    "Fazer Agendamento", 
    "Buscar Agendamentos", 
    "Ver Evoluções (Restrito)",
    "Pacientes"
])

if menu == "Fazer Agendamento":
    st.header("Novo Agendamento")
    
    with st.form("form_agendamento"):
        id_pac = st.number_input("ID Paciente", min_value=1, step=1)
        id_fisio = st.number_input("ID Fisioterapeuta", min_value=1, step=1)
        id_sala = st.number_input("ID Sala", min_value=1, step=1)
        data_ini = st.text_input("Início (AAAA-MM-DD HH:MM:SS)", value="2026-11-20 14:00:00")
        data_fim = st.text_input("Fim (AAAA-MM-DD HH:MM:SS)", value="2026-11-20 15:00:00")
        
        st.subheader("Procedimento")
        id_proc = st.number_input("ID Procedimento", min_value=1, step=1)
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        
        forcar_erro = st.checkbox("Forçar erro pra testar o rollback")
        
        if st.form_submit_button("Salvar Tudo"):
            conn = conectar()
            cursor = conn.cursor()
            try:
                # comecando a transacao
                conn.start_transaction()
                
                # prepared statement usando %s pra evitar sql injection
                sql1 = "INSERT INTO agendamento (id_paciente, id_fisioterapeuta, id_sala, data_hora_inicio, data_hora_fim, status) VALUES (%s, %s, %s, %s, %s, 'agendado')"
                cursor.execute(sql1, (id_pac, id_fisio, id_sala, data_ini, data_fim))
                
                # pegando o id do agendamento que acabou de ser criado
                id_gerado = cursor.lastrowid 
                
                if forcar_erro:
                    raise Exception("Erro forcado! Testando rollback do banco.")
                
                sql2 = "INSERT INTO item_agendamento (id_agendamento, id_procedimento, valor_cobrado, duracao_realizada) VALUES (%s, %s, %s, 60)"
                cursor.execute(sql2, (id_gerado, id_proc, valor))
                
                # se deu tudo certo nas duas tabelas, confirma
                conn.commit()
                st.success("Agendamento e procedimento salvos juntos!")
                
            except Exception as erro:
                # se deu erro em qualquer um, desfaz tudo
                conn.rollback()
                st.error(f"Erro ao salvar. O banco desfez a transação. Detalhe: {erro}")
            finally:
                cursor.close()
                conn.close()

elif menu == "Buscar Agendamentos":
    st.header("Busca de Agendamentos por Data")
    dia = st.date_input("Selecione o dia")
    
    if st.button("Buscar"):
        conn = conectar()
        # consulta parametrizada
        sql = "SELECT a.id_agendamento, p.nome, a.status FROM agendamento a JOIN paciente p ON a.id_paciente = p.id_paciente WHERE DATE(a.data_hora_inicio) = %s"
        df = pd.read_sql(sql, conn, params=(dia,))
        st.dataframe(df)
        conn.close()

elif menu == "Ver Evoluções (Restrito)":
    st.header("Histórico de Pacientes")
    st.write("Visualizando através da VIEW por causa da LGPD.")
    
    if st.button("Carregar Dados"):
        conn = conectar()
        # puxando da view em vez das tabelas originais pra mostrar pro professor
        df = pd.read_sql("SELECT * FROM vw_historico_pacientes", conn)
        st.dataframe(df)
        conn.close()

elif menu == "Pacientes":
    st.header("Lista de Pacientes")
    
    conn = conectar()
    df_pac = pd.read_sql("SELECT id_paciente, cpf, nome, data_nascimento FROM paciente", conn)
    st.dataframe(df_pac)
    conn.close()
    
    st.subheader("Novo Paciente")
    with st.form("form_paciente"):
        nome = st.text_input("Nome")
        cpf = st.text_input("CPF")
        nascimento = st.date_input("Nascimento")
        
        if st.form_submit_button("Cadastrar"):
            try:
                conn = conectar()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO paciente (nome, cpf, data_nascimento) VALUES (%s, %s, %s)", (nome, cpf, nascimento))
                conn.commit()
                st.success("Cadastrado com sucesso!")
            except Exception as e:
                # tratando erro de banco na interface pra ele nao estourar feio na tela (ex: cpf repetido)
                st.error(f"Erro ao cadastrar (Verifique se o CPF já existe). Erro: {e}")