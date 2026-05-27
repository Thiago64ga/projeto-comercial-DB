ALTER TABLE comercial.dim_canal_venda
ADD COLUMN IF NOT EXISTS ativo BOOLEAN DEFAULT TRUE;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'comercial'
          AND table_name = 'dim_canal_venda'
          AND column_name = 'status'
    ) THEN
        UPDATE comercial.dim_canal_venda
        SET ativo = COALESCE(
            UPPER(status) NOT IN ('INATIVO', 'INATIVA', 'INACTIVE', 'FALSE', '0'),
            TRUE
        )
        WHERE ativo IS NULL;
    ELSE
        UPDATE comercial.dim_canal_venda
        SET ativo = TRUE
        WHERE ativo IS NULL;
    END IF;
END $$;

ALTER TABLE comercial.dim_canal_venda
ALTER COLUMN ativo SET DEFAULT TRUE;

ALTER TABLE comercial.dim_canal_venda
ALTER COLUMN ativo SET NOT NULL;

