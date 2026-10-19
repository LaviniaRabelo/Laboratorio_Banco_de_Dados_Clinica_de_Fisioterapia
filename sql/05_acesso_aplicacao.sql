-- Executar UMA VEZ como administrador. MySQL 8.0.18 ou superior.
-- Nao modifica os registros da clinica.
-- O CREATE USER retorna a senha aleatoria: guarde-a para configurar a aplicacao.
CREATE ROLE IF NOT EXISTS 'perfil_cadastro_paciente';
GRANT SELECT, INSERT, UPDATE ON clinica_fisioterapia.paciente TO 'perfil_cadastro_paciente';
CREATE USER 'clinica_app'@'localhost' IDENTIFIED BY RANDOM PASSWORD;
GRANT 'perfil_cadastro_paciente' TO 'clinica_app'@'localhost';
SET DEFAULT ROLE 'perfil_cadastro_paciente' TO 'clinica_app'@'localhost';
-- Sem DELETE, acesso a evolucao clinica ou alteracao direta da agenda.
-- Os demais acessos serao concedidos conforme os proximos modulos.
