"""Configura apenas o arquivo local .env; nao modifica o banco."""
import getpass
import secrets
from pathlib import Path
from dotenv import set_key
from werkzeug.security import generate_password_hash


def main():
    target = Path(__file__).with_name('.env')
    if target.exists():
        print('Já existe um .env. Edite esse arquivo para ajustar a configuração existente.')
        return
    print('Conexão com o MySQL já utilizado no Workbench:')
    host = input('Servidor [127.0.0.1]: ').strip() or '127.0.0.1'
    port = input('Porta [3306]: ').strip() or '3306'
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise SystemExit('Porta inválida.')
    db_user = input('Usuário do MySQL: ').strip()
    db_password = getpass.getpass('Senha do MySQL (não aparece ao digitar): ')
    print('\nCrie o acesso à tela do sistema:')
    app_user = input('Usuário do sistema [admin]: ').strip() or 'admin'
    app_password = getpass.getpass('Nova senha do sistema (mínimo 10 caracteres): ')
    confirm = getpass.getpass('Repita a nova senha: ')
    if not db_user or len(app_password) < 10 or app_password != confirm:
        raise SystemExit('Confira o usuário, o tamanho e a confirmação da senha. Nada foi salvo.')
    values = dict(DB_HOST=host, DB_PORT=port, DB_NAME='clinica_fisioterapia',
                  DB_USER=db_user, DB_PASSWORD=db_password, APP_USER=app_user,
                  APP_PASSWORD_HASH=generate_password_hash(app_password), SECRET_KEY=secrets.token_hex(32))
    target.touch(mode=0o600)
    for key, value in values.items():
        set_key(str(target), key, value)
    print('Configuração salva. Agora execute: python app.py')


if __name__ == '__main__':
    main()
