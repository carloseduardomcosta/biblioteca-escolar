-- 001_add_tipo_pessoa.sql
-- Adiciona o papel da pessoa (aluno/professor) à tabela `aluno`.
-- A tabela `aluno` passa a representar "Pessoas"; o empréstimo continua
-- apontando para aluno_id. Registros antigos assumem 'aluno' (default).
--
-- Idempotente: rode via app/run_migration_tipo.py (checa se a coluna já existe).
-- MySQL não suporta "ADD COLUMN IF NOT EXISTS", por isso o guard fica no runner.

ALTER TABLE aluno
  ADD COLUMN tipo ENUM('aluno','professor') NOT NULL DEFAULT 'aluno' AFTER nome;
