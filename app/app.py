"""Etapa 2: autenticação local e CRUDs com SQL parametrizado."""

import os
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path
from zoneinfo import ZoneInfo

import pymysql
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.security import check_password_hash


load_dotenv(Path(__file__).with_name('.env'))

FIELDS = (
    'cpf',
    'nome',
    'data_nascimento',
    'logradouro',
    'numero_endereco',
    'bairro',
    'cidade',
    'uf',
    'cep',
    'id_paciente_indicador',
)

UFS = (
    'AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN '
    'RS RO RR SC SP SE TO'
).split()


def create_app(test_config=None):
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY'),
        DB_HOST=os.getenv('DB_HOST', '127.0.0.1'),
        DB_PORT=int(os.getenv('DB_PORT', '3306')),
        DB_NAME=os.getenv('DB_NAME', 'clinica_fisioterapia'),
        DB_USER=os.getenv('DB_USER'),
        DB_PASSWORD=os.getenv('DB_PASSWORD'),
        APP_USER=os.getenv('APP_USER'),
        APP_PASSWORD_HASH=os.getenv('APP_PASSWORD_HASH'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        MAX_CONTENT_LENGTH=32 * 1024,
    )

    if test_config:
        app.config.update(test_config)

    if not all(
        app.config.get(k)
        for k in ('SECRET_KEY', 'DB_USER', 'APP_USER', 'APP_PASSWORD_HASH')
    ):
        raise RuntimeError(
            'Configure o projeto primeiro: execute python configurar.py.'
        )

    CSRFProtect(app)

    def db():
        if 'db' not in g:
            g.db = pymysql.connect(
                host=app.config['DB_HOST'],
                port=app.config['DB_PORT'],
                user=app.config['DB_USER'],
                password=app.config['DB_PASSWORD'],
                database=app.config['DB_NAME'],
                charset='utf8mb4',
                autocommit=False,
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=5,
                init_command="SET time_zone='-03:00'",
            )

        return g.db

    @app.teardown_appcontext
    def close_db(error=None):
        conn = g.pop('db', None)

        if conn is not None:
            conn.rollback()
            conn.close()

    def protected(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get('user'):
                return redirect(url_for('login'))

            return view(*args, **kwargs)

        return wrapped

    def fetch_patient(patient_id):
        with db().cursor() as cur:
            cur.execute(
                'SELECT * FROM paciente WHERE id_paciente=%s',
                (patient_id,),
            )
            patient = cur.fetchone()

        if patient is None:
            abort(404)

        return patient

    def fetch_room(room_id):
        with db().cursor() as cur:
            cur.execute(
                'SELECT * FROM sala WHERE id_sala=%s',
                (room_id,),
            )
            room = cur.fetchone()

            if room is None:
                abort(404)

            cur.execute(
                'SELECT equipamento '
                'FROM equipamento_sala '
                'WHERE id_sala=%s '
                'ORDER BY equipamento',
                (room_id,),
            )

            room['equipamentos'] = [
                row['equipamento']
                for row in cur.fetchall()
            ]

        return room

    def fetch_procedure(procedure_id):
        with db().cursor() as cur:
            cur.execute(
                'SELECT * FROM procedimento WHERE id_procedimento=%s',
                (procedure_id,),
            )
            procedure = cur.fetchone()

        if procedure is None:
            abort(404)

        return procedure

    def fetch_specialties():
        with db().cursor() as cur:
            cur.execute(
                'SELECT id_especialidade, nome_especialidade '
                'FROM especialidade ORDER BY nome_especialidade'
            )
            return cur.fetchall()

    def fetch_insurance(insurance_id):
        with db().cursor() as cur:
            cur.execute(
                'SELECT * FROM convenio WHERE id_convenio=%s',
                (insurance_id,),
            )
            insurance = cur.fetchone()

        if insurance is None:
            abort(404)

        return insurance

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # Verifica o hash mesmo quando o nome de usuario nao corresponde.
            valid = check_password_hash(
                app.config['APP_PASSWORD_HASH'],
                request.form.get('senha', ''),
            )

            if (
                valid
                and request.form.get('usuario', '')
                == app.config['APP_USER']
            ):
                session.clear()
                session['user'] = app.config['APP_USER']
                return redirect(url_for('patients'))

            flash('Usuário ou senha incorretos.', 'error')
            return render_template('login.html'), 401

        return render_template('login.html')

    @app.post('/sair')
    @protected
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.get('/')
    def index():
        return redirect(url_for('patients'))

    @app.get('/pacientes')
    @protected
    def patients():
        search = request.args.get('busca', '').strip()[:120]

        page = max(
            1,
            request.args.get('pagina', 1, type=int) or 1,
        )

        with db().cursor() as cur:

            # Consulta fixa e totalmente parametrizada.
            # Nenhum valor fornecido pelo usuário é concatenado ao SQL.
            cur.execute(
                """
                SELECT COUNT(*) AS total
                FROM paciente
                WHERE (
                    %s = ''
                    OR LOCATE(%s, nome) > 0
                    OR LOCATE(%s, cpf) > 0
                )
                """,
                (
                    search,
                    search,
                    search,
                ),
            )

            total = cur.fetchone()['total']

            pages = max(
                1,
                (total + 19) // 20,
            )

            page = min(
                page,
                pages,
            )

            cur.execute(
                """
                SELECT
                    id_paciente,
                    nome,
                    cpf,
                    data_nascimento,
                    cidade,
                    uf
                FROM paciente
                WHERE (
                    %s = ''
                    OR LOCATE(%s, nome) > 0
                    OR LOCATE(%s, cpf) > 0
                )
                ORDER BY
                    nome,
                    id_paciente
                LIMIT %s OFFSET %s
                """,
                (
                    search,
                    search,
                    search,
                    20,
                    (page - 1) * 20,
                ),
            )

            rows = cur.fetchall()

        return render_template(
            'pacientes.html',
            patients=rows,
            search=search,
            page=page,
            pages=pages,
            total=total,
        )

    @app.route('/pacientes/novo', methods=['GET', 'POST'])
    @app.route(
        '/pacientes/<int:patient_id>/editar',
        methods=['GET', 'POST'],
    )
    @protected
    def edit_patient(patient_id=None):

        if patient_id:
            patient = fetch_patient(patient_id)

            # Mostra a data no padrão brasileiro ao editar.
            if patient.get('data_nascimento'):
                patient['data_nascimento'] = (
                    patient['data_nascimento'].strftime('%d/%m/%Y')
                )
        else:
            patient = dict.fromkeys(FIELDS, '')

        errors = []

        if request.method == 'POST':
            patient = {
                key: request.form.get(key, '').strip()
                for key in FIELDS
            }

            patient['cpf'] = (
                patient['cpf']
                .replace('.', '')
                .replace('-', '')
            )

            patient['cep'] = patient['cep'].replace('-', '')
            patient['uf'] = patient['uf'].upper()

            errors = validate_patient(patient, patient_id)

            if not errors:

                # Faz uma cópia para enviar ao banco.
                patient_db = patient.copy()

                # DD/MM/AAAA -> objeto date do Python.
                patient_db['data_nascimento'] = datetime.strptime(
                    patient['data_nascimento'],
                    '%d/%m/%Y',
                ).date()

                values = tuple(
                    patient_db[k] or None
                    for k in FIELDS
                )

                try:
                    with db().cursor() as cur:

                        if patient_id:
                            cur.execute(
                                """
                                UPDATE paciente
                                SET cpf=%s,
                                    nome=%s,
                                    data_nascimento=%s,
                                    logradouro=%s,
                                    numero_endereco=%s,
                                    bairro=%s,
                                    cidade=%s,
                                    uf=%s,
                                    cep=%s,
                                    id_paciente_indicador=%s
                                WHERE id_paciente=%s
                                """,
                                values + (patient_id,),
                            )

                        else:
                            cur.execute(
                                """
                                INSERT INTO paciente (
                                    cpf,
                                    nome,
                                    data_nascimento,
                                    logradouro,
                                    numero_endereco,
                                    bairro,
                                    cidade,
                                    uf,
                                    cep,
                                    id_paciente_indicador
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """,
                                values,
                            )

                    db().commit()

                    flash(
                        'Paciente atualizado.'
                        if patient_id
                        else 'Paciente cadastrado.',
                        'success',
                    )

                    return redirect(url_for('patients'))

                except pymysql.IntegrityError as exc:
                    db().rollback()

                    if exc.args[0] == 1062:
                        errors.append(
                            'Já existe um paciente com esse CPF.'
                        )

                    elif exc.args[0] == 1452:
                        errors.append(
                            'O paciente indicador não foi encontrado. '
                            'Confira o ID informado.'
                        )

                    else:
                        errors.append(
                            'Os dados não atendem às regras do banco. '
                            'Confira os campos.'
                        )

                except pymysql.MySQLError:
                    db().rollback()

                    errors.append(
                        'Não foi possível salvar. '
                        'Confira os dados e tente novamente.'
                    )

        return (
            render_template(
                'paciente_form.html',
                patient=patient,
                patient_id=patient_id,
                errors=errors,
                ufs=UFS,
            ),
            422 if errors else 200,
        )


    @app.post('/pacientes/<int:patient_id>/excluir')
    @protected
    def delete_patient(patient_id):
        fetch_patient(patient_id)

        try:
            with db().cursor() as cur:
                cur.execute(
                    'DELETE FROM paciente WHERE id_paciente=%s',
                    (patient_id,),
                )

            db().commit()
            flash('Paciente excluído.', 'success')

        except pymysql.IntegrityError:
            db().rollback()
            flash(
                'Não é possível excluir este paciente porque existem '
                'agendamentos ou outros registros históricos vinculados.',
                'error',
            )

        return redirect(url_for('patients'))


    @app.get('/salas')
    @protected
    def rooms():
        with db().cursor() as cur:
            cur.execute(
                '''
                SELECT
                    s.id_sala,
                    s.numero_sala,
                    s.capacidade,
                    GROUP_CONCAT(
                        es.equipamento
                        ORDER BY es.equipamento
                        SEPARATOR ', '
                    ) AS equipamentos
                FROM sala s
                LEFT JOIN equipamento_sala es
                    ON es.id_sala = s.id_sala
                GROUP BY
                    s.id_sala,
                    s.numero_sala,
                    s.capacidade
                ORDER BY s.numero_sala
                '''
            )
            rows = cur.fetchall()

        return render_template(
            'salas.html',
            rooms=rows,
        )

    @app.route('/salas/nova', methods=['GET', 'POST'])
    @app.route(
        '/salas/<int:room_id>/editar',
        methods=['GET', 'POST'],
    )
    @protected
    def edit_room(room_id=None):
        if room_id:
            room = fetch_room(room_id)
            room['equipamentos_texto'] = ', '.join(
                room['equipamentos']
            )
        else:
            room = {
                'numero_sala': '',
                'capacidade': '',
                'equipamentos_texto': '',
            }

        errors = []

        if request.method == 'POST':
            room = {
                'numero_sala': request.form.get(
                    'numero_sala',
                    '',
                ).strip(),
                'capacidade': request.form.get(
                    'capacidade',
                    '',
                ).strip(),
                'equipamentos_texto': request.form.get(
                    'equipamentos',
                    '',
                ).strip(),
            }

            errors = validate_room(room)

            equipamentos = [
                equipamento.strip()
                for equipamento in room['equipamentos_texto'].split(',')
                if equipamento.strip()
            ]

            if not errors:
                try:
                    with db().cursor() as cur:
                        if room_id:
                            cur.execute(
                                '''
                                UPDATE sala
                                SET numero_sala=%s,
                                    capacidade=%s
                                WHERE id_sala=%s
                                ''',
                                (
                                    room['numero_sala'],
                                    int(room['capacidade']),
                                    room_id,
                                ),
                            )

                            cur.execute(
                                '''
                                DELETE FROM equipamento_sala
                                WHERE id_sala=%s
                                ''',
                                (room_id,),
                            )

                            sala_id = room_id
                        else:
                            cur.execute(
                                '''
                                INSERT INTO sala
                                    (numero_sala, capacidade)
                                VALUES (%s, %s)
                                ''',
                                (
                                    room['numero_sala'],
                                    int(room['capacidade']),
                                ),
                            )

                            sala_id = cur.lastrowid

                        for equipamento in equipamentos:
                            cur.execute(
                                '''
                                INSERT INTO equipamento_sala
                                    (id_sala, equipamento)
                                VALUES (%s, %s)
                                ''',
                                (
                                    sala_id,
                                    equipamento,
                                ),
                            )

                    db().commit()

                    flash(
                        'Sala atualizada.'
                        if room_id
                        else 'Sala cadastrada.',
                        'success',
                    )

                    return redirect(url_for('rooms'))

                except pymysql.IntegrityError as exc:
                    db().rollback()

                    if exc.args[0] == 1062:
                        errors.append(
                            'Já existe uma sala com esse número '
                            'ou um equipamento foi informado duas vezes.'
                        )
                    else:
                        errors.append(
                            'Os dados não atendem às regras do banco.'
                        )

                except pymysql.MySQLError:
                    db().rollback()
                    errors.append(
                        'Não foi possível salvar a sala.'
                    )

        return (
            render_template(
                'sala_form.html',
                room=room,
                room_id=room_id,
                errors=errors,
            ),
            422 if errors else 200,
        )

    @app.post('/salas/<int:room_id>/excluir')
    @protected
    def delete_room(room_id):
        fetch_room(room_id)

        try:
            with db().cursor() as cur:
                cur.execute(
                    'DELETE FROM sala WHERE id_sala=%s',
                    (room_id,),
                )

            db().commit()
            flash(
                'Sala excluída.',
                'success',
            )

        except pymysql.IntegrityError as exc:
            db().rollback()

            if exc.args[0] == 1451:
                flash(
                    'Essa sala não pode ser excluída porque '
                    'já possui agendamentos vinculados.',
                    'error',
                )
            else:
                flash(
                    'Não foi possível excluir a sala.',
                    'error',
                )

        return redirect(url_for('rooms'))

    @app.get('/procedimentos')
    @protected
    def procedures():
        search = request.args.get('busca', '').strip()[:100]

        with db().cursor() as cur:
            cur.execute(
                """
                SELECT
                    p.id_procedimento,
                    p.nome_procedimento,
                    e.nome_especialidade,
                    p.valor_tabela,
                    p.duracao_padrao_min
                FROM procedimento p
                JOIN especialidade e
                    ON e.id_especialidade = p.id_especialidade_exigida
                WHERE (
                    %s = ''
                    OR LOCATE(%s, p.nome_procedimento) > 0
                )
                ORDER BY p.nome_procedimento
                """,
                (search, search),
            )
            rows = cur.fetchall()

        return render_template(
            'procedimentos.html',
            procedures=rows,
            search=search,
        )


    @app.route('/procedimentos/novo', methods=['GET', 'POST'])
    @app.route(
        '/procedimentos/<int:procedure_id>/editar',
        methods=['GET', 'POST'],
    )
    @protected
    def edit_procedure(procedure_id=None):
        specialties = fetch_specialties()

        if procedure_id:
            procedure = fetch_procedure(procedure_id)
            procedure['valor_tabela'] = format(
                Decimal(procedure['valor_tabela']),
                '.2f',
            )
        else:
            procedure = {
                'nome_procedimento': '',
                'id_especialidade_exigida': '',
                'valor_tabela': '',
                'duracao_padrao_min': '',
            }

        errors = []

        if request.method == 'POST':
            procedure = {
                'nome_procedimento': request.form.get(
                    'nome_procedimento',
                    '',
                ).strip(),
                'id_especialidade_exigida': request.form.get(
                    'id_especialidade_exigida',
                    '',
                ).strip(),
                'valor_tabela': request.form.get(
                    'valor_tabela',
                    '',
                ).strip(),
                'duracao_padrao_min': request.form.get(
                    'duracao_padrao_min',
                    '',
                ).strip(),
            }

            errors = validate_procedure(procedure, specialties)

            if not errors:
                valor = Decimal(
                    procedure['valor_tabela'].replace(',', '.')
                ).quantize(Decimal('0.01'))

                try:
                    with db().cursor() as cur:
                        if procedure_id:
                            cur.execute(
                                """
                                UPDATE procedimento
                                SET nome_procedimento=%s,
                                    id_especialidade_exigida=%s,
                                    valor_tabela=%s,
                                    duracao_padrao_min=%s
                                WHERE id_procedimento=%s
                                """,
                                (
                                    procedure['nome_procedimento'],
                                    int(procedure['id_especialidade_exigida']),
                                    valor,
                                    int(procedure['duracao_padrao_min']),
                                    procedure_id,
                                ),
                            )
                        else:
                            cur.execute(
                                """
                                INSERT INTO procedimento (
                                    nome_procedimento,
                                    id_especialidade_exigida,
                                    valor_tabela,
                                    duracao_padrao_min
                                )
                                VALUES (%s, %s, %s, %s)
                                """,
                                (
                                    procedure['nome_procedimento'],
                                    int(procedure['id_especialidade_exigida']),
                                    valor,
                                    int(procedure['duracao_padrao_min']),
                                ),
                            )

                    db().commit()
                    flash(
                        'Procedimento atualizado.'
                        if procedure_id
                        else 'Procedimento cadastrado.',
                        'success',
                    )
                    return redirect(url_for('procedures'))

                except pymysql.IntegrityError as exc:
                    db().rollback()

                    if exc.args[0] == 1452:
                        errors.append(
                            'A especialidade selecionada não existe.'
                        )
                    else:
                        errors.append(
                            'Os dados não atendem às regras do banco.'
                        )

                except pymysql.MySQLError:
                    db().rollback()
                    errors.append(
                        'Não foi possível salvar o procedimento.'
                    )

        return (
            render_template(
                'procedimento_form.html',
                procedure=procedure,
                procedure_id=procedure_id,
                specialties=specialties,
                errors=errors,
            ),
            422 if errors else 200,
        )


    @app.post('/procedimentos/<int:procedure_id>/excluir')
    @protected
    def delete_procedure(procedure_id):
        fetch_procedure(procedure_id)

        try:
            with db().cursor() as cur:
                cur.execute(
                    'DELETE FROM procedimento WHERE id_procedimento=%s',
                    (procedure_id,),
                )

            db().commit()
            flash('Procedimento excluído.', 'success')

        except pymysql.IntegrityError as exc:
            db().rollback()

            if exc.args[0] == 1451:
                flash(
                    'Esse procedimento não pode ser excluído porque '
                    'já está vinculado a um agendamento.',
                    'error',
                )
            else:
                flash(
                    'Não foi possível excluir o procedimento.',
                    'error',
                )

        return redirect(url_for('procedures'))



    @app.get('/convenios')
    @protected
    def insurances():
        search = request.args.get('busca', '').strip()[:100]

        with db().cursor() as cur:
            cur.execute(
                """
                SELECT
                    id_convenio,
                    nome_convenio,
                    registro_ans,
                    telefone_contato
                FROM convenio
                WHERE (
                    %s = ''
                    OR LOCATE(%s, nome_convenio) > 0
                    OR LOCATE(%s, COALESCE(registro_ans, '')) > 0
                )
                ORDER BY nome_convenio, id_convenio
                """,
                (search, search, search),
            )
            rows = cur.fetchall()

        return render_template(
            'convenios.html',
            insurances=rows,
            search=search,
        )


    @app.route('/convenios/novo', methods=['GET', 'POST'])
    @app.route(
        '/convenios/<int:insurance_id>/editar',
        methods=['GET', 'POST'],
    )
    @protected
    def edit_insurance(insurance_id=None):
        if insurance_id:
            insurance = fetch_insurance(insurance_id)
        else:
            insurance = {
                'nome_convenio': '',
                'registro_ans': '',
                'telefone_contato': '',
            }

        errors = []

        if request.method == 'POST':
            insurance = {
                'nome_convenio': request.form.get(
                    'nome_convenio',
                    '',
                ).strip(),
                'registro_ans': request.form.get(
                    'registro_ans',
                    '',
                ).strip(),
                'telefone_contato': request.form.get(
                    'telefone_contato',
                    '',
                ).strip(),
            }

            errors = validate_insurance(insurance)

            if not errors:
                values = (
                    insurance['nome_convenio'],
                    insurance['registro_ans'] or None,
                    insurance['telefone_contato'] or None,
                )

                try:
                    with db().cursor() as cur:
                        if insurance_id:
                            cur.execute(
                                """
                                UPDATE convenio
                                SET nome_convenio=%s,
                                    registro_ans=%s,
                                    telefone_contato=%s
                                WHERE id_convenio=%s
                                """,
                                values + (insurance_id,),
                            )
                        else:
                            cur.execute(
                                """
                                INSERT INTO convenio (
                                    nome_convenio,
                                    registro_ans,
                                    telefone_contato
                                )
                                VALUES (%s, %s, %s)
                                """,
                                values,
                            )

                    db().commit()
                    flash(
                        'Convênio atualizado.'
                        if insurance_id
                        else 'Convênio cadastrado.',
                        'success',
                    )
                    return redirect(url_for('insurances'))

                except pymysql.MySQLError:
                    db().rollback()
                    errors.append(
                        'Não foi possível salvar o convênio.'
                    )

        return (
            render_template(
                'convenio_form.html',
                insurance=insurance,
                insurance_id=insurance_id,
                errors=errors,
            ),
            422 if errors else 200,
        )


    @app.post('/convenios/<int:insurance_id>/excluir')
    @protected
    def delete_insurance(insurance_id):
        fetch_insurance(insurance_id)

        try:
            with db().cursor() as cur:
                cur.execute(
                    'DELETE FROM convenio WHERE id_convenio=%s',
                    (insurance_id,),
                )

            db().commit()
            flash('Convênio excluído.', 'success')

        except pymysql.IntegrityError as exc:
            db().rollback()

            if exc.args[0] == 1451:
                flash(
                    'Esse convênio não pode ser excluído porque '
                    'possui vínculo de paciente ou histórico financeiro associado.',
                    'error',
                )
            else:
                flash(
                    'Não foi possível excluir o convênio.',
                    'error',
                )

        except pymysql.MySQLError:
            db().rollback()
            flash(
                'Não foi possível excluir o convênio.',
                'error',
            )

        return redirect(url_for('insurances'))


    @app.get('/consultas')
    @protected
    def query_menu():
        return render_template('consultas.html')


    @app.get('/consultas/atendimentos')
    @protected
    def query_appointments():
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        start_text = request.args.get('data_inicio', f'01/01/{hoje.year}').strip()
        end_text = request.args.get('data_fim', f'31/12/{hoje.year}').strip()
        status = request.args.get('status', '').strip()
        errors = []

        try:
            start_date = datetime.strptime(start_text, '%d/%m/%Y').date()
            end_date = datetime.strptime(end_text, '%d/%m/%Y').date()
            if start_date > end_date:
                raise ValueError
        except ValueError:
            errors.append(
                'Informe um período válido no formato DD/MM/AAAA, '
                'com a data inicial menor ou igual à final.'
            )
            start_date = end_date = None

        if status not in ('', 'agendado', 'realizado', 'cancelado'):
            errors.append('Selecione um status válido.')

        rows = []

        if not errors:
            with db().cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        a.id_agendamento,
                        a.data_hora_inicio,
                        a.data_hora_fim,
                        a.status,
                        pac.nome AS paciente,
                        prof.nome AS fisioterapeuta,
                        s.numero_sala,
                        COUNT(ia.id_procedimento) AS quantidade_procedimentos,
                        COALESCE(SUM(ia.valor_cobrado), 0) AS valor_total
                    FROM agendamento a
                    JOIN paciente pac
                        ON pac.id_paciente = a.id_paciente
                    JOIN profissional prof
                        ON prof.id_profissional = a.id_fisioterapeuta
                    JOIN sala s
                        ON s.id_sala = a.id_sala
                    LEFT JOIN item_agendamento ia
                        ON ia.id_agendamento = a.id_agendamento
                    WHERE a.data_hora_inicio >= %s
                      AND a.data_hora_inicio < DATE_ADD(%s, INTERVAL 1 DAY)
                      AND (%s = '' OR a.status = %s)
                    GROUP BY
                        a.id_agendamento,
                        a.data_hora_inicio,
                        a.data_hora_fim,
                        a.status,
                        pac.nome,
                        prof.nome,
                        s.numero_sala
                    ORDER BY a.data_hora_inicio, a.id_agendamento
                    """,
                    (start_date, end_date, status, status),
                )
                rows = cur.fetchall()

        return render_template(
            'consulta_atendimentos.html',
            rows=rows,
            data_inicio=start_text,
            data_fim=end_text,
            status=status,
            errors=errors,
        )


    @app.get('/consultas/producao')
    @protected
    def query_productivity():
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        start_text = request.args.get('data_inicio', f'01/01/{hoje.year}').strip()
        end_text = request.args.get('data_fim', f'31/12/{hoje.year}').strip()
        specialty_text = request.args.get('especialidade', '0').strip()
        specialties = fetch_specialties()
        errors = []

        try:
            start_date = datetime.strptime(start_text, '%d/%m/%Y').date()
            end_date = datetime.strptime(end_text, '%d/%m/%Y').date()
            if start_date > end_date:
                raise ValueError
        except ValueError:
            errors.append(
                'Informe um período válido no formato DD/MM/AAAA, '
                'com a data inicial menor ou igual à final.'
            )
            start_date = end_date = None

        try:
            specialty_id = int(specialty_text)
        except ValueError:
            specialty_id = -1

        valid_specialties = {
            int(item['id_especialidade']) for item in specialties
        }

        if specialty_id != 0 and specialty_id not in valid_specialties:
            errors.append('Selecione uma especialidade válida.')

        rows = []

        if not errors:
            with db().cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        prof.id_profissional,
                        prof.nome AS fisioterapeuta,
                        COUNT(DISTINCT a.id_agendamento) AS quantidade_atendimentos,
                        COUNT(ia.id_procedimento) AS quantidade_procedimentos,
                        COALESCE(SUM(ia.valor_cobrado), 0) AS valor_total
                    FROM profissional prof
                    JOIN fisioterapeuta f
                        ON f.id_profissional = prof.id_profissional
                    JOIN agendamento a
                        ON a.id_fisioterapeuta = f.id_profissional
                    JOIN item_agendamento ia
                        ON ia.id_agendamento = a.id_agendamento
                    JOIN procedimento p
                        ON p.id_procedimento = ia.id_procedimento
                    JOIN especialidade e
                        ON e.id_especialidade = p.id_especialidade_exigida
                    WHERE a.data_hora_inicio >= %s
                      AND a.data_hora_inicio < DATE_ADD(%s, INTERVAL 1 DAY)
                      AND a.status = 'realizado'
                      AND (%s = 0 OR e.id_especialidade = %s)
                    GROUP BY prof.id_profissional, prof.nome
                    ORDER BY valor_total DESC, prof.nome
                    """,
                    (start_date, end_date, specialty_id, specialty_id),
                )
                rows = cur.fetchall()

        return render_template(
            'consulta_producao.html',
            rows=rows,
            data_inicio=start_text,
            data_fim=end_text,
            specialty_id=specialty_id,
            specialties=specialties,
            errors=errors,
        )


    @app.get('/relatorios/financeiro')
    @protected
    def financial_report():
        hoje = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        start_text = request.args.get(
            'data_inicio',
            f'01/01/{hoje.year}',
        ).strip()
        end_text = request.args.get(
            'data_fim',
            f'31/12/{hoje.year}',
        ).strip()
        status = request.args.get('status', '').strip()
        errors = []

        try:
            start_date = datetime.strptime(
                start_text,
                '%d/%m/%Y',
            ).date()
            end_date = datetime.strptime(
                end_text,
                '%d/%m/%Y',
            ).date()

            if start_date > end_date:
                raise ValueError

        except ValueError:
            errors.append(
                'Informe um período válido no formato DD/MM/AAAA, '
                'com a data inicial menor ou igual à final.'
            )
            start_date = end_date = None

        if status not in ('', 'agendado', 'realizado', 'cancelado'):
            errors.append('Selecione um status válido.')

        rows = []
        summary = {
            'atendimentos': 0,
            'valor_total': Decimal('0.00'),
            'valor_convenio': Decimal('0.00'),
            'valor_paciente': Decimal('0.00'),
            'total_pago': Decimal('0.00'),
            'saldo_paciente': Decimal('0.00'),
            'rateios_pendentes': 0,
        }

        if not errors:
            with db().cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        v.id_agendamento,
                        p.nome AS paciente,
                        v.data_hora_inicio,
                        v.status_agendamento,
                        v.quantidade_itens,
                        v.quantidade_rateios,
                        v.situacao_rateio,
                        v.valor_total,
                        v.valor_convenio,
                        v.valor_paciente,
                        v.total_pago_paciente,
                        v.saldo_paciente
                    FROM vw_financeiro_agendamento v
                    JOIN paciente p
                        ON p.id_paciente = v.id_paciente
                    WHERE v.data_hora_inicio >= %s
                      AND v.data_hora_inicio < DATE_ADD(%s, INTERVAL 1 DAY)
                      AND (%s = '' OR v.status_agendamento = %s)
                    ORDER BY v.data_hora_inicio, v.id_agendamento
                    """,
                    (start_date, end_date, status, status),
                )
                rows = cur.fetchall()

            summary['atendimentos'] = len(rows)

            for row in rows:
                summary['valor_total'] += (
                    row['valor_total'] or Decimal('0.00')
                )
                summary['valor_convenio'] += (
                    row['valor_convenio'] or Decimal('0.00')
                )
                summary['valor_paciente'] += (
                    row['valor_paciente'] or Decimal('0.00')
                )
                summary['total_pago'] += (
                    row['total_pago_paciente'] or Decimal('0.00')
                )
                summary['saldo_paciente'] += (
                    row['saldo_paciente'] or Decimal('0.00')
                )

                if row['situacao_rateio'] == 'rateio_pendente':
                    summary['rateios_pendentes'] += 1

        return render_template(
            'relatorio_financeiro.html',
            rows=rows,
            summary=summary,
            data_inicio=start_text,
            data_fim=end_text,
            status=status,
            errors=errors,
        )


    @app.get('/agendamentos')
    @protected
    def appointments():
        status = request.args.get('status', '').strip()
        if status not in ('', 'agendado', 'realizado', 'cancelado'):
            status = ''

        with db().cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.id_agendamento,
                    pac.nome AS paciente,
                    prof.nome AS fisioterapeuta,
                    s.numero_sala,
                    a.data_hora_inicio,
                    a.data_hora_fim,
                    a.status,
                    COUNT(ia.id_procedimento) AS quantidade_procedimentos,
                    GROUP_CONCAT(
                        pr.nome_procedimento
                        ORDER BY pr.nome_procedimento
                        SEPARATOR ', '
                    ) AS procedimentos,
                    COALESCE(SUM(ia.valor_cobrado), 0) AS valor_total
                FROM agendamento a
                JOIN paciente pac
                    ON pac.id_paciente = a.id_paciente
                JOIN profissional prof
                    ON prof.id_profissional = a.id_fisioterapeuta
                JOIN sala s
                    ON s.id_sala = a.id_sala
                LEFT JOIN item_agendamento ia
                    ON ia.id_agendamento = a.id_agendamento
                LEFT JOIN procedimento pr
                    ON pr.id_procedimento = ia.id_procedimento
                WHERE (%s = '' OR a.status = %s)
                GROUP BY
                    a.id_agendamento,
                    pac.nome,
                    prof.nome,
                    s.numero_sala,
                    a.data_hora_inicio,
                    a.data_hora_fim,
                    a.status
                ORDER BY a.data_hora_inicio DESC, a.id_agendamento DESC
                LIMIT 200
                """,
                (status, status),
            )
            rows = cur.fetchall()

        return render_template(
            'agendamentos.html',
            appointments=rows,
            status=status,
        )


    @app.route('/agendamentos/novo', methods=['GET', 'POST'])
    @protected
    def new_appointment():
        with db().cursor() as cur:
            cur.execute(
                'SELECT id_paciente, nome, cpf '
                'FROM paciente ORDER BY nome, id_paciente'
            )
            patients_options = cur.fetchall()

            cur.execute(
                """
                SELECT
                    f.id_profissional,
                    p.nome,
                    p.cpf,
                    f.numero_crefito,
                    GROUP_CONCAT(
                        q.id_especialidade
                        ORDER BY q.id_especialidade
                        SEPARATOR ','
                    ) AS especialidades
                FROM fisioterapeuta f
                JOIN profissional p
                    ON p.id_profissional = f.id_profissional
                LEFT JOIN qualificacao q
                    ON q.id_profissional = f.id_profissional
                GROUP BY
                    f.id_profissional,
                    p.nome,
                    p.cpf,
                    f.numero_crefito
                ORDER BY p.nome, f.id_profissional
                """
            )
            physios_options = cur.fetchall()

            cur.execute(
                'SELECT id_sala, numero_sala, capacidade '
                'FROM sala ORDER BY numero_sala, id_sala'
            )
            rooms_options = cur.fetchall()

            cur.execute(
                """
                SELECT
                    pr.id_procedimento,
                    pr.nome_procedimento,
                    pr.id_especialidade_exigida,
                    e.nome_especialidade,
                    pr.valor_tabela,
                    pr.duracao_padrao_min
                FROM procedimento pr
                JOIN especialidade e
                    ON e.id_especialidade = pr.id_especialidade_exigida
                ORDER BY e.nome_especialidade, pr.nome_procedimento
                """
            )
            procedures_options = cur.fetchall()

            cur.execute(
                """
                SELECT
                    vc.id_paciente,
                    vc.id_convenio,
                    c.nome_convenio,
                    vc.numero_carteirinha,
                    vc.data_inicio,
                    vc.data_fim
                FROM vinculo_convenio vc
                JOIN convenio c
                    ON c.id_convenio = vc.id_convenio
                ORDER BY vc.id_paciente, c.nome_convenio, vc.data_inicio DESC
                """
            )
            insurance_links = cur.fetchall()

            cur.execute(
                """
                SELECT
                    id_convenio,
                    nome_convenio,
                    registro_ans
                FROM convenio
                ORDER BY nome_convenio, id_convenio
                """
            )
            all_insurances = cur.fetchall()

            cur.execute(
                """
                SELECT
                    id_forma_pagamento,
                    nome
                FROM forma_pagamento
                WHERE ativo = 1
                ORDER BY id_forma_pagamento
                """
            )
            payment_methods = cur.fetchall()

        form = {
            'id_paciente': request.args.get('paciente', '').strip(),
            'id_fisioterapeuta': request.args.get('fisioterapeuta', '').strip(),
            'id_sala': '',
            'data_atendimento': '',
            'hora_inicio': '',
            'tipo_atendimento': 'particular',
            'id_convenio': '',
            'situacao_pagamento': 'pendente',
            'id_forma_pagamento': '',
        }
        selected_procedures = []
        errors = []

        if request.method == 'POST':
            action = request.form.get('action', 'schedule').strip()

            # Vínculo rápido de convênio com o paciente selecionado.
            # A data de início é o dia do cadastro; data_fim representa a
            # validade do plano/carteirinha.
            if request.form.get('quick_link') == '1':
                patient_text = request.form.get('id_paciente', '').strip()
                insurance_text = request.form.get('qi_id_convenio', '').strip()
                card_number = request.form.get('qi_carteirinha', '').strip()
                expiry_text = request.form.get('qi_data_validade', '').strip()

                quick_errors = []

                valid_patient_ids = {
                    str(item['id_paciente'])
                    for item in patients_options
                }
                valid_insurance_ids = {
                    str(item['id_convenio'])
                    for item in all_insurances
                }

                if patient_text not in valid_patient_ids:
                    quick_errors.append(
                        'Selecione o paciente antes de vincular um convênio.'
                    )

                if insurance_text not in valid_insurance_ids:
                    quick_errors.append('Selecione um convênio válido.')

                if not card_number or len(card_number) > 30:
                    quick_errors.append(
                        'Informe o número da carteirinha, com até 30 caracteres.'
                    )

                today = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
                expiry_date = None
                try:
                    expiry_date = datetime.strptime(
                        expiry_text,
                        '%d/%m/%Y',
                    ).date()
                    if expiry_date < today:
                        raise ValueError
                except ValueError:
                    quick_errors.append(
                        'Informe uma validade do plano/carteirinha igual ou '
                        'posterior à data de hoje, no formato DD/MM/AAAA.'
                    )

                if quick_errors:
                    for message in quick_errors:
                        flash(message, 'error')
                    return redirect(
                        url_for(
                            'new_appointment',
                            paciente=patient_text or None,
                        )
                    )

                try:
                    with db().cursor() as cur:
                        # RN11: não permite dois convênios válidos ao mesmo
                        # tempo para o mesmo paciente.
                        cur.execute(
                            """
                            SELECT id_convenio, numero_carteirinha
                            FROM vinculo_convenio
                            WHERE id_paciente=%s
                              AND data_inicio <= %s
                              AND (data_fim IS NULL OR data_fim >= %s)
                            LIMIT 1
                            """,
                            (int(patient_text), today, today),
                        )
                        active_link = cur.fetchone()

                        if active_link is not None:
                            raise ValueError(
                                'Esse paciente já possui um convênio válido/ativo. '
                                'Finalize ou atualize o vínculo atual antes de '
                                'cadastrar outro.'
                            )

                        cur.execute(
                            """
                            INSERT INTO vinculo_convenio (
                                id_paciente,
                                id_convenio,
                                data_inicio,
                                data_fim,
                                numero_carteirinha
                            )
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                int(patient_text),
                                int(insurance_text),
                                today,
                                expiry_date,
                                card_number,
                            ),
                        )

                    db().commit()
                    flash(
                        'Convênio vinculado ao paciente e marcado como válido '
                        f'até {expiry_date.strftime("%d/%m/%Y")}.',
                        'success',
                    )
                    return redirect(
                        url_for(
                            'new_appointment',
                            paciente=patient_text,
                        )
                    )

                except ValueError as exc:
                    db().rollback()
                    flash(str(exc), 'error')
                    return redirect(
                        url_for(
                            'new_appointment',
                            paciente=patient_text,
                        )
                    )

                except pymysql.IntegrityError:
                    db().rollback()
                    flash(
                        'Não foi possível vincular o convênio. Confira os dados.',
                        'error',
                    )
                    return redirect(
                        url_for(
                            'new_appointment',
                            paciente=patient_text,
                        )
                    )

                except pymysql.MySQLError:
                    db().rollback()
                    flash(
                        'Não foi possível vincular o convênio ao paciente.',
                        'error',
                    )
                    return redirect(
                        url_for(
                            'new_appointment',
                            paciente=patient_text,
                        )
                    )

            # Cadastro rápido de paciente sem sair da tela de agendamento.
            if action == 'quick_patient':
                nome = request.form.get('qp_nome', '').strip()
                cpf = (
                    request.form.get('qp_cpf', '')
                    .replace('.', '')
                    .replace('-', '')
                    .strip()
                )
                nascimento_texto = request.form.get(
                    'qp_data_nascimento',
                    '',
                ).strip()

                quick_errors = []

                if not nome or len(nome) > 120:
                    quick_errors.append(
                        'Informe o nome do paciente, com até 120 caracteres.'
                    )

                if (
                    len(cpf) != 11
                    or not cpf.isascii()
                    or not cpf.isdigit()
                ):
                    quick_errors.append(
                        'Informe o CPF do paciente com 11 dígitos.'
                    )

                nascimento = None
                try:
                    nascimento = datetime.strptime(
                        nascimento_texto,
                        '%d/%m/%Y',
                    ).date()
                    hoje = datetime.now(
                        ZoneInfo('America/Sao_Paulo')
                    ).date()
                    if nascimento > hoje:
                        raise ValueError
                except ValueError:
                    quick_errors.append(
                        'Informe uma data de nascimento válida em DD/MM/AAAA.'
                    )

                if quick_errors:
                    for message in quick_errors:
                        flash(message, 'error')
                    return redirect(url_for('new_appointment'))

                try:
                    with db().cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO paciente (
                                cpf,
                                nome,
                                data_nascimento
                            )
                            VALUES (%s, %s, %s)
                            """,
                            (cpf, nome, nascimento),
                        )
                        new_patient_id = cur.lastrowid

                    db().commit()
                    flash(
                        'Paciente cadastrado e selecionado para o agendamento. '
                        'Os demais dados podem ser completados depois em Pacientes.',
                        'success',
                    )
                    return redirect(
                        url_for(
                            'new_appointment',
                            paciente=new_patient_id,
                        )
                    )

                except pymysql.IntegrityError as exc:
                    db().rollback()
                    if exc.args[0] == 1062:
                        flash('Já existe um paciente com esse CPF.', 'error')
                    else:
                        flash('Não foi possível cadastrar o paciente.', 'error')
                    return redirect(url_for('new_appointment'))

                except pymysql.MySQLError:
                    db().rollback()
                    flash('Não foi possível cadastrar o paciente.', 'error')
                    return redirect(url_for('new_appointment'))

            # Fluxo normal do agendamento.
            form = {
                'id_paciente': request.form.get('id_paciente', '').strip(),
                'id_fisioterapeuta': request.form.get(
                    'id_fisioterapeuta',
                    '',
                ).strip(),
                'id_sala': request.form.get('id_sala', '').strip(),
                'data_atendimento': request.form.get(
                    'data_atendimento',
                    '',
                ).strip(),
                'hora_inicio': request.form.get('hora_inicio', '').strip(),
                'tipo_atendimento': request.form.get(
                    'tipo_atendimento',
                    'particular',
                ).strip(),
                'id_convenio': request.form.get('id_convenio', '').strip(),
                'situacao_pagamento': request.form.get(
                    'situacao_pagamento',
                    'pendente',
                ).strip(),
                'id_forma_pagamento': request.form.get(
                    'id_forma_pagamento',
                    '',
                ).strip(),
            }

            raw_procedures = request.form.getlist('procedimentos')

            try:
                selected_procedures = list(dict.fromkeys(
                    int(value) for value in raw_procedures
                ))
            except ValueError:
                selected_procedures = []
                errors.append('Selecione procedimentos válidos.')

            patient_ids = {
                str(item['id_paciente'])
                for item in patients_options
            }
            physio_ids = {
                str(item['id_profissional'])
                for item in physios_options
            }
            room_ids = {
                str(item['id_sala'])
                for item in rooms_options
            }
            procedure_map = {
                item['id_procedimento']: item
                for item in procedures_options
            }

            if form['id_paciente'] not in patient_ids:
                errors.append('Selecione um paciente válido.')

            if form['id_fisioterapeuta'] not in physio_ids:
                errors.append('Selecione um fisioterapeuta válido.')

            if form['id_sala'] not in room_ids:
                errors.append('Selecione uma sala válida.')

            if form['tipo_atendimento'] not in ('particular', 'convenio'):
                errors.append('Selecione Particular ou Convênio.')

            # Pagamento na tela de agendamento só se aplica a atendimento particular.
            # Em atendimento por convênio, qualquer recebimento do paciente será
            # tratado depois, fora desta tela.
            if form['tipo_atendimento'] == 'convenio':
                form['situacao_pagamento'] = 'pendente'
                form['id_forma_pagamento'] = ''
            else:
                if form['situacao_pagamento'] not in ('pendente', 'pago'):
                    errors.append(
                        'Selecione se o pagamento será feito depois ou se já foi pago.'
                    )

                valid_payment_method_ids = {
                    str(item['id_forma_pagamento'])
                    for item in payment_methods
                }

                if (
                    form['situacao_pagamento'] == 'pago'
                    and form['id_forma_pagamento'] not in valid_payment_method_ids
                ):
                    errors.append('Selecione uma forma de pagamento válida.')

            if not selected_procedures:
                errors.append('Selecione pelo menos um procedimento.')
            elif any(
                procedure_id not in procedure_map
                for procedure_id in selected_procedures
            ):
                errors.append('Um dos procedimentos selecionados não existe.')

            start_at = None
            end_at = None

            try:
                appointment_date = datetime.strptime(
                    form['data_atendimento'],
                    '%d/%m/%Y',
                ).date()
                appointment_time = datetime.strptime(
                    form['hora_inicio'],
                    '%H:%M',
                ).time()
                start_at = datetime.combine(
                    appointment_date,
                    appointment_time,
                )
            except ValueError:
                errors.append(
                    'Informe data e hora válidas. Use DD/MM/AAAA para a data.'
                )

            if start_at is not None:
                now = datetime.now(ZoneInfo('America/Sao_Paulo')).replace(
                    tzinfo=None,
                    second=0,
                    microsecond=0,
                )
                if start_at < now:
                    errors.append(
                        'O novo agendamento deve ser marcado para data e hora futuras.'
                    )

            selected_insurance_id = None
            if form['tipo_atendimento'] == 'convenio':
                try:
                    selected_insurance_id = int(form['id_convenio'])
                except ValueError:
                    errors.append('Selecione um convênio válido para o paciente.')

            if not errors:
                selected_rows = [
                    procedure_map[procedure_id]
                    for procedure_id in selected_procedures
                ]
                total_minutes = sum(
                    int(item['duracao_padrao_min'])
                    for item in selected_rows
                )
                end_at = start_at + timedelta(minutes=total_minutes)

                try:
                    conn = db()
                    conn.begin()

                    with conn.cursor() as cur:
                        # RN07: o fisioterapeuta precisa estar qualificado em
                        # todas as especialidades exigidas pelos procedimentos.
                        cur.execute(
                            'SELECT id_especialidade '
                            'FROM qualificacao '
                            'WHERE id_profissional=%s',
                            (int(form['id_fisioterapeuta']),),
                        )
                        qualified_specialties = {
                            row['id_especialidade']
                            for row in cur.fetchall()
                        }

                        missing_specialties = sorted({
                            item['nome_especialidade']
                            for item in selected_rows
                            if item['id_especialidade_exigida']
                            not in qualified_specialties
                        })

                        if missing_specialties:
                            raise ValueError(
                                'O fisioterapeuta selecionado não possui '
                                'qualificação em: '
                                + ', '.join(missing_specialties)
                                + '.'
                            )

                        # Valida o vínculo do convênio na data do atendimento.
                        if form['tipo_atendimento'] == 'convenio':
                            cur.execute(
                                """
                                SELECT numero_carteirinha
                                FROM vinculo_convenio
                                WHERE id_paciente=%s
                                  AND id_convenio=%s
                                  AND data_inicio <= %s
                                  AND (data_fim IS NULL OR data_fim >= %s)
                                ORDER BY data_inicio DESC
                                LIMIT 1
                                """,
                                (
                                    int(form['id_paciente']),
                                    selected_insurance_id,
                                    appointment_date,
                                    appointment_date,
                                ),
                            )
                            if cur.fetchone() is None:
                                raise ValueError(
                                    'O paciente não possui vínculo ativo com '
                                    'esse convênio na data do atendimento.'
                                )

                        # RN08: bloqueia conflito de sala no mesmo intervalo.
                        cur.execute(
                            """
                            SELECT id_agendamento
                            FROM agendamento
                            WHERE id_sala=%s
                              AND status <> 'cancelado'
                              AND data_hora_inicio < %s
                              AND data_hora_fim > %s
                            FOR UPDATE
                            """,
                            (int(form['id_sala']), end_at, start_at),
                        )
                        if cur.fetchone():
                            raise ValueError(
                                'A sala selecionada já possui atendimento nesse horário.'
                            )

                        # RN09: bloqueia conflito do fisioterapeuta.
                        cur.execute(
                            """
                            SELECT id_agendamento
                            FROM agendamento
                            WHERE id_fisioterapeuta=%s
                              AND status <> 'cancelado'
                              AND data_hora_inicio < %s
                              AND data_hora_fim > %s
                            FOR UPDATE
                            """,
                            (
                                int(form['id_fisioterapeuta']),
                                end_at,
                                start_at,
                            ),
                        )
                        if cur.fetchone():
                            raise ValueError(
                                'O fisioterapeuta selecionado já possui '
                                'atendimento nesse horário.'
                            )

                        cur.execute(
                            """
                            INSERT INTO agendamento (
                                id_paciente,
                                id_fisioterapeuta,
                                id_sala,
                                data_hora_inicio,
                                data_hora_fim,
                                status
                            )
                            VALUES (%s, %s, %s, %s, %s, 'agendado')
                            """,
                            (
                                int(form['id_paciente']),
                                int(form['id_fisioterapeuta']),
                                int(form['id_sala']),
                                start_at,
                                end_at,
                            ),
                        )
                        appointment_id = cur.lastrowid

                        cur.executemany(
                            """
                            INSERT INTO item_agendamento (
                                id_agendamento,
                                id_procedimento,
                                valor_cobrado,
                                duracao_realizada
                            )
                            VALUES (%s, %s, %s, NULL)
                            """,
                            [
                                (
                                    appointment_id,
                                    item['id_procedimento'],
                                    item['valor_tabela'],
                                )
                                for item in selected_rows
                            ],
                        )

                        # Já cria o rateio financeiro. Particular fica 100%
                        # para o paciente; convênio usa a cobertura cadastrada.
                        rateios = []
                        for item in selected_rows:
                            percentual = Decimal('0.00')
                            convenio_id = None

                            if form['tipo_atendimento'] == 'convenio':
                                convenio_id = selected_insurance_id
                                cur.execute(
                                    """
                                    SELECT percentual_cobertura
                                    FROM cobertura
                                    WHERE id_convenio=%s
                                      AND id_procedimento=%s
                                    """,
                                    (
                                        convenio_id,
                                        item['id_procedimento'],
                                    ),
                                )
                                coverage = cur.fetchone()
                                if coverage is not None:
                                    percentual = Decimal(
                                        coverage['percentual_cobertura']
                                    )

                            rateios.append(
                                (
                                    appointment_id,
                                    item['id_procedimento'],
                                    convenio_id,
                                    item['valor_tabela'],
                                    percentual,
                                )
                            )

                        cur.executemany(
                            """
                            INSERT INTO rateio_item (
                                id_agendamento,
                                id_procedimento,
                                id_convenio,
                                valor_base,
                                percentual_cobertura_aplicado
                            )
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            rateios,
                        )

                        cur.execute(
                            """
                            SELECT COALESCE(SUM(valor_paciente), 0.00)
                                   AS valor_devido_paciente
                            FROM rateio_item
                            WHERE id_agendamento = %s
                            """,
                            (appointment_id,),
                        )
                        valor_devido_paciente = Decimal(
                            cur.fetchone()['valor_devido_paciente']
                        )

                        pagamento_registrado = False

                        if (
                            form['tipo_atendimento'] == 'particular'
                            and form['situacao_pagamento'] == 'pago'
                            and valor_devido_paciente > Decimal('0.00')
                        ):
                            cur.execute(
                                """
                                INSERT INTO pagamento (
                                    id_agendamento,
                                    id_forma_pagamento,
                                    valor_pago
                                )
                                VALUES (%s, %s, %s)
                                """,
                                (
                                    appointment_id,
                                    int(form['id_forma_pagamento']),
                                    valor_devido_paciente,
                                ),
                            )
                            pagamento_registrado = True

                    conn.commit()

                    if pagamento_registrado:
                        payment_message = (
                            ' O pagamento do paciente também foi registrado.'
                        )
                    elif form['tipo_atendimento'] == 'convenio':
                        payment_message = (
                            ' O atendimento foi registrado pelo convênio. '
                            'Nenhum pagamento do paciente foi registrado nesta tela.'
                        )
                    elif (
                        form['situacao_pagamento'] == 'pago'
                        and valor_devido_paciente == Decimal('0.00')
                    ):
                        payment_message = (
                            ' Não havia valor do paciente a receber.'
                        )
                    else:
                        payment_message = (
                            ' O pagamento ficou pendente para ser registrado depois.'
                        )

                    flash(
                        'Atendimento agendado com sucesso. '
                        f'Horário final calculado: {end_at.strftime("%H:%M")}. '
                        'O rateio financeiro também foi preparado.'
                        + payment_message,
                        'success',
                    )
                    return redirect(url_for('appointments'))

                except ValueError as exc:
                    db().rollback()
                    errors.append(str(exc))

                except pymysql.IntegrityError:
                    db().rollback()
                    errors.append(
                        'O banco rejeitou o agendamento por uma regra de '
                        'integridade. Nenhuma alteração parcial foi mantida.'
                    )

                except pymysql.MySQLError:
                    db().rollback()
                    errors.append(
                        'Não foi possível concluir o agendamento. '
                        'Nenhuma alteração parcial foi mantida.'
                    )

        return (
            render_template(
                'agendamento_form.html',
                form=form,
                selected_procedures=selected_procedures,
                patients=patients_options,
                physios=physios_options,
                rooms=rooms_options,
                procedures=procedures_options,
                                insurance_links=insurance_links,
                all_insurances=all_insurances,
                payment_methods=payment_methods,
                today_text=datetime.now(
                    ZoneInfo('America/Sao_Paulo')
                ).strftime('%d/%m/%Y'),
                errors=errors,
            ),
            422 if errors else 200,
        )



    @app.get('/api/agendamentos/disponibilidade')
    @protected
    def appointment_availability():
        """Retorna dias e horários livres para o calendário de agendamento.

        A disponibilidade considera simultaneamente a sala e o fisioterapeuta.
        Os horários são oferecidos em intervalos de 30 minutos, entre 08:00 e
        18:00, e a validação definitiva continua sendo repetida na gravação.
        """
        month_text = request.args.get('mes', '').strip()
        physio_id = request.args.get('id_fisioterapeuta', type=int)
        room_id = request.args.get('id_sala', type=int)
        duration = request.args.get('duracao', type=int)

        if not physio_id or not room_id or not duration:
            return jsonify({
                'erro': (
                    'Selecione fisioterapeuta, sala e pelo menos um '
                    'procedimento antes de abrir o calendário.'
                )
            }), 400

        if duration <= 0 or duration > 600:
            return jsonify({'erro': 'Duração do atendimento inválida.'}), 400

        try:
            month_start = datetime.strptime(
                month_text,
                '%Y-%m',
            ).date().replace(day=1)
        except ValueError:
            return jsonify({'erro': 'Mês inválido.'}), 400

        if month_start.month == 12:
            next_month = date(month_start.year + 1, 1, 1)
        else:
            next_month = date(
                month_start.year,
                month_start.month + 1,
                1,
            )

        today = datetime.now(ZoneInfo('America/Sao_Paulo')).date()
        first_allowed_month = today.replace(day=1)
        last_allowed_day = today + timedelta(days=180)
        last_allowed_month = last_allowed_day.replace(day=1)

        if (
            month_start < first_allowed_month
            or month_start > last_allowed_month
        ):
            return jsonify({
                'erro': 'O calendário permite consultar os próximos 180 dias.'
            }), 400

        start_dt = datetime.combine(
            month_start,
            datetime.min.time(),
        )
        end_dt = datetime.combine(
            next_month,
            datetime.min.time(),
        )

        with db().cursor() as cur:
            cur.execute(
                """
                SELECT
                    data_hora_inicio,
                    data_hora_fim
                FROM agendamento
                WHERE status <> 'cancelado'
                  AND data_hora_inicio < %s
                  AND data_hora_fim > %s
                  AND (
                        id_sala = %s
                        OR id_fisioterapeuta = %s
                  )
                ORDER BY data_hora_inicio
                """,
                (end_dt, start_dt, room_id, physio_id),
            )
            occupied = cur.fetchall()

        occupied_ranges = [
            (
                row['data_hora_inicio'],
                row['data_hora_fim'],
            )
            for row in occupied
        ]

        now = datetime.now(ZoneInfo('America/Sao_Paulo')).replace(
            tzinfo=None,
            second=0,
            microsecond=0,
        )

        days = []
        current = month_start

        while current < next_month:
            times = []

            if current >= today and current <= last_allowed_day:
                opening = datetime.combine(
                    current,
                    datetime.strptime('08:00', '%H:%M').time(),
                )
                closing = datetime.combine(
                    current,
                    datetime.strptime('18:00', '%H:%M').time(),
                )

                candidate = opening
                slot_delta = timedelta(minutes=30)
                service_delta = timedelta(minutes=duration)

                while candidate + service_delta <= closing:
                    slot_end = candidate + service_delta

                    is_future = candidate >= now
                    has_conflict = any(
                        candidate < busy_end
                        and slot_end > busy_start
                        for busy_start, busy_end in occupied_ranges
                    )

                    if is_future and not has_conflict:
                        times.append(candidate.strftime('%H:%M'))

                    candidate += slot_delta

            days.append({
                'data': current.isoformat(),
                'disponivel': bool(times),
                'horarios': times,
            })
            current += timedelta(days=1)

        return jsonify({
            'mes': month_text,
            'dias': days,
            'duracao_minutos': duration,
            'limite_dias': 180,
        })


    @app.post('/agendamentos/<int:appointment_id>/cancelar')
    @protected
    def cancel_appointment(appointment_id):
        try:
            with db().cursor() as cur:
                cur.execute(
                    """
                    UPDATE agendamento
                    SET status='cancelado'
                    WHERE id_agendamento=%s
                      AND status='agendado'
                    """,
                    (appointment_id,),
                )
                changed = cur.rowcount

            db().commit()

            if changed:
                flash(
                    'Agendamento cancelado. O histórico foi preservado.',
                    'success',
                )
            else:
                flash(
                    'O agendamento não foi encontrado ou não está mais agendado.',
                    'error',
                )

        except pymysql.MySQLError:
            db().rollback()
            flash('Não foi possível cancelar o agendamento.', 'error')

        return redirect(url_for('appointments'))



    @app.errorhandler(CSRFError)
    def csrf_error(error):
        return (
            render_template(
                'erro.html',
                message=(
                    'O formulário expirou. '
                    'Reabra a página e tente novamente.'
                ),
            ),
            400,
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            render_template(
                'erro.html',
                message='Página ou paciente não encontrado.',
            ),
            404,
        )

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'

        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "style-src 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )

        return response

    @app.errorhandler(pymysql.MySQLError)
    def database_error(error):
        print('\n==============================')
        print('ERRO MYSQL:')
        print(repr(error))
        print('==============================\n')

        return (
            render_template(
                'erro.html',
                message=(
                    'Não foi possível acessar o banco. '
                    'Confira o erro exibido no terminal do VS Code.'
                ),
            ),
            503,
        )

    return app


def validate_patient(p, patient_id=None):
    errors = []

    # CPF
    if (
        len(p['cpf']) != 11
        or not p['cpf'].isascii()
        or not p['cpf'].isdigit()
    ):
        errors.append(
            'Informe um CPF com 11 dígitos.'
        )

    # Nome
    if not p['nome'] or len(p['nome']) > 120:
        errors.append(
            'Informe o nome, com até 120 caracteres.'
        )

    # Data de nascimento no padrão DD/MM/AAAA
    try:
        if not re.fullmatch(
            r'\d{2}/\d{2}/\d{4}',
            p['data_nascimento'],
        ):
            raise ValueError

        birth = datetime.strptime(
            p['data_nascimento'],
            '%d/%m/%Y',
        ).date()

        hoje = datetime.now(
            ZoneInfo('America/Sao_Paulo')
        ).date()

        if birth.year < 1000 or birth > hoje:
            raise ValueError

    except ValueError:
        errors.append(
            'Informe uma data de nascimento válida '
            'no formato DD/MM/AAAA e não futura.'
        )

    # Endereço
    for key, size, label in [
        ('logradouro', 120, 'Logradouro'),
        ('numero_endereco', 10, 'Número'),
        ('bairro', 60, 'Bairro'),
        ('cidade', 60, 'Cidade'),
    ]:
        if len(p[key]) > size:
            errors.append(
                f'{label}: use até {size} caracteres.'
            )

    # UF
    if p['uf'] and p['uf'] not in UFS:
        errors.append(
            'Selecione uma UF válida.'
        )

    # CEP
    if p['cep'] and (
        len(p['cep']) != 8
        or not p['cep'].isascii()
        or not p['cep'].isdigit()
    ):
        errors.append(
            'Informe um CEP com 8 dígitos ou deixe em branco.'
        )

    # Paciente indicador
    if p['id_paciente_indicador']:
        try:
            indicator = int(
                p['id_paciente_indicador']
            )

            if (
                indicator < 1
                or indicator > 2147483647
                or indicator == patient_id
            ):
                raise ValueError

        except ValueError:
            errors.append(
                'Informe o ID de outro paciente indicador '
                'ou deixe em branco.'
            )

    return errors



def validate_room(room):
    errors = []

    numero_sala = room['numero_sala']
    capacidade = room['capacidade']

    if not numero_sala:
        errors.append(
            'Informe o número ou identificação da sala.'
        )
    elif len(numero_sala) > 10:
        errors.append(
            'O número da sala deve possuir no máximo 10 caracteres.'
        )

    try:
        capacidade_int = int(capacidade)

        if capacidade_int <= 0 or capacidade_int > 32767:
            raise ValueError

    except (ValueError, TypeError):
        errors.append(
            'Informe uma capacidade válida entre 1 e 32767.'
        )

    equipamentos = [
        equipamento.strip()
        for equipamento in room['equipamentos_texto'].split(',')
        if equipamento.strip()
    ]

    for equipamento in equipamentos:
        if len(equipamento) > 60:
            errors.append(
                f'O equipamento "{equipamento}" possui mais '
                'de 60 caracteres.'
            )

    nomes_normalizados = [
        equipamento.casefold()
        for equipamento in equipamentos
    ]

    if len(nomes_normalizados) != len(set(nomes_normalizados)):
        errors.append(
            'Não repita o mesmo equipamento na sala.'
        )

    return errors

def validate_procedure(procedure, specialties):
    errors = []

    nome = procedure['nome_procedimento']
    specialty_ids = {
        str(item['id_especialidade'])
        for item in specialties
    }

    if not nome:
        errors.append('Informe o nome do procedimento.')
    elif len(nome) > 100:
        errors.append(
            'O nome do procedimento deve ter no máximo 100 caracteres.'
        )

    if procedure['id_especialidade_exigida'] not in specialty_ids:
        errors.append('Selecione uma especialidade válida.')

    try:
        valor = Decimal(
            procedure['valor_tabela'].replace(',', '.')
        )

        if (
            not valor.is_finite()
            or valor < 0
            or valor > Decimal('99999999.99')
        ):
            raise InvalidOperation

        if valor.as_tuple().exponent < -2:
            errors.append(
                'O valor deve possuir no máximo duas casas decimais.'
            )

    except (InvalidOperation, ValueError):
        errors.append(
            'Informe um valor válido, igual ou maior que zero.'
        )

    try:
        duracao = int(procedure['duracao_padrao_min'])

        if duracao <= 0 or duracao > 32767:
            raise ValueError

    except ValueError:
        errors.append(
            'Informe uma duração válida, em minutos, maior que zero.'
        )

    return errors



def validate_insurance(insurance):
    errors = []

    nome = insurance['nome_convenio']
    registro_ans = insurance['registro_ans']
    telefone = insurance['telefone_contato']

    if not nome:
        errors.append('Informe o nome do convênio.')
    elif len(nome) > 100:
        errors.append(
            'O nome do convênio deve ter no máximo 100 caracteres.'
        )

    if len(registro_ans) > 20:
        errors.append(
            'O registro ANS deve ter no máximo 20 caracteres.'
        )

    if len(telefone) > 20:
        errors.append(
            'O telefone de contato deve ter no máximo 20 caracteres.'
        )

    return errors


if __name__ == '__main__':
    create_app().run(
        host='127.0.0.1',
        port=5000,
        debug=False,
    )
