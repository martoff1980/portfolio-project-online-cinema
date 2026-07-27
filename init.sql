GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cinema_admin;

CREATE DATABASE online_cinema_test_db;
CREATE USER cinema_test_user WITH PASSWORD 'cinema_test_pass';
ALTER DATABASE online_cinema_test_db OWNER TO cinema_test_user;