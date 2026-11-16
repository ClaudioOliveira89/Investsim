-- Cria o usuário e o banco da aplicação no PostgreSQL local.
-- Execute como superusuário (você vai digitar a senha do usuário postgres):
--   psql -U postgres -h localhost -f database/criar_banco.sql
-- Troque a senha abaixo e use a mesma no DATABASE_URL do arquivo .env.

CREATE ROLE investsim WITH LOGIN PASSWORD 'investsim';
CREATE DATABASE investsim OWNER investsim ENCODING 'UTF8' TEMPLATE template0;
-- Banco separado para os testes que validam o schema no PostgreSQL (opcional):
CREATE DATABASE investsim_teste OWNER investsim ENCODING 'UTF8' TEMPLATE template0;
