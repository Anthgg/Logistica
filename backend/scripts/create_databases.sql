-- Ejecute como administrador de PostgreSQL y sustituya la contraseña.
CREATE USER continuous_auth_user WITH PASSWORD 'replace-this-password';

CREATE DATABASE continuous_authentication OWNER continuous_auth_user;
GRANT ALL PRIVILEGES ON DATABASE continuous_authentication TO continuous_auth_user;

CREATE DATABASE continuous_authentication_test OWNER continuous_auth_user;
GRANT ALL PRIVILEGES ON DATABASE continuous_authentication_test TO continuous_auth_user;

-- Comprobación desde psql:
-- \c continuous_authentication continuous_auth_user
-- SELECT current_database(), current_user;
