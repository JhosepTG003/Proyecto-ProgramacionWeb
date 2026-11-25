CREATE DATABASE maki ENCODING 'UTF8' TEMPLATE template0;

\connect maki

BEGIN;

CREATE SEQUENCE seq_artesano_id   START 1;
CREATE SEQUENCE seq_prenda_codigo START 1;

CREATE TABLE usuarios (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    correo          VARCHAR(254) NOT NULL,
    clave_hash      VARCHAR(255) NOT NULL,
    rol             VARCHAR(20)  NOT NULL,
    artesano_id     VARCHAR(12),
    nombre_publico  VARCHAR(100),
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT uq_usuarios_correo       UNIQUE (correo),
    CONSTRAINT uq_usuarios_artesano_id  UNIQUE (artesano_id),
    CONSTRAINT ck_usuarios_rol          CHECK (rol IN ('comprador', 'artesano')),
    CONSTRAINT ck_usuarios_correo_min   CHECK (correo = lower(correo)),
    CONSTRAINT ck_usuarios_artesano     CHECK (
        (rol = 'artesano'  AND artesano_id ~ '^ART-[0-9]{4,}$' AND nombre_publico IS NOT NULL)
     OR (rol = 'comprador' AND artesano_id IS NULL)
    )
);

CREATE FUNCTION fn_asignar_artesano() RETURNS trigger AS $$
BEGIN
    IF NEW.rol = 'artesano' AND NEW.artesano_id IS NULL THEN
        NEW.artesano_id := 'ART-' || lpad(nextval('seq_artesano_id')::text, 4, '0');
    END IF;
    IF NEW.rol = 'artesano' AND NEW.nombre_publico IS NULL THEN
        NEW.nombre_publico := 'Artesano ' || NEW.artesano_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_usuarios_artesano
    BEFORE INSERT ON usuarios
    FOR EACH ROW EXECUTE FUNCTION fn_asignar_artesano();

CREATE TABLE sesiones (
    token_hash  CHAR(64)    PRIMARY KEY,
    usuario_id  BIGINT      NOT NULL REFERENCES usuarios (id) ON DELETE CASCADE,
    expira_en   TIMESTAMPTZ NOT NULL,
    creada_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_sesiones_usuario ON sesiones (usuario_id);
CREATE INDEX ix_sesiones_expira  ON sesiones (expira_en);

CREATE TABLE fibras (
    id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre  VARCHAR(30) NOT NULL,
    clave   VARCHAR(30) NOT NULL,

    CONSTRAINT uq_fibras_clave        UNIQUE (clave),
    CONSTRAINT ck_fibras_nombre_largo CHECK (char_length(nombre) BETWEEN 3 AND 30),
    CONSTRAINT ck_fibras_clave_min    CHECK (clave = lower(clave))
);

CREATE TABLE prendas (
    id                   VARCHAR(40) PRIMARY KEY
        DEFAULT ('MAKI-' || lpad(nextval('seq_prenda_codigo')::text, 4, '0')),
    nombre               VARCHAR(100) NOT NULL,
    tinte                VARCHAR(100) NOT NULL,
    precio_centavos_usd  INTEGER      NOT NULL,
    stock                INTEGER      NOT NULL,
    foto                 TEXT,
    artesano_id          VARCHAR(12)  NOT NULL REFERENCES usuarios (artesano_id),
    fibra_id             BIGINT       NOT NULL REFERENCES fibras (id),
    creado_en            TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT ck_prendas_precio CHECK (precio_centavos_usd > 0 AND precio_centavos_usd <= 1000000),
    CONSTRAINT ck_prendas_stock  CHECK (stock >= 0 AND stock <= 9999),
    CONSTRAINT ck_prendas_foto   CHECK (foto IS NULL OR foto ~ '^data:image/(jpeg|png|webp);base64,')
);
CREATE INDEX ix_prendas_artesano ON prendas (artesano_id);
CREATE INDEX ix_prendas_fibra    ON prendas (fibra_id);

CREATE TABLE pedidos (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    comprador_id  BIGINT      NOT NULL REFERENCES usuarios (id),
    estado        VARCHAR(20) NOT NULL DEFAULT 'Aprobado',
    moneda        VARCHAR(3)  NOT NULL,
    zona          VARCHAR(10) NOT NULL,
    subtotal      INTEGER     NOT NULL,
    envio         INTEGER     NOT NULL,
    total         INTEGER     NOT NULL,
    plataforma    INTEGER     NOT NULL,
    cooperativa   INTEGER     NOT NULL,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT ck_pedidos_estado  CHECK (estado IN ('Aprobado')),
    CONSTRAINT ck_pedidos_moneda  CHECK (moneda IN ('USD', 'EUR')),
    CONSTRAINT ck_pedidos_zona    CHECK (zona IN ('America', 'Europa', 'Otros')),
    CONSTRAINT ck_pedidos_montos  CHECK (subtotal >= 0 AND envio >= 0 AND total >= 0
                                         AND plataforma >= 0 AND cooperativa >= 0),
    CONSTRAINT ck_pedidos_total   CHECK (total = subtotal + envio),
    CONSTRAINT ck_pedidos_reparto CHECK (plataforma + cooperativa = subtotal)
);
CREATE INDEX ix_pedidos_comprador ON pedidos (comprador_id, creado_en DESC);

CREATE TABLE pedido_items (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pedido_id        BIGINT       NOT NULL REFERENCES pedidos (id) ON DELETE CASCADE,
    prenda_id        VARCHAR(40)  NOT NULL REFERENCES prendas (id),
    artesano_id      VARCHAR(12)  NOT NULL REFERENCES usuarios (artesano_id),
    nombre_prenda    VARCHAR(100) NOT NULL,
    cantidad         INTEGER      NOT NULL,
    precio_unitario  INTEGER      NOT NULL,
    subtotal         INTEGER      NOT NULL,

    CONSTRAINT uq_items_pedido_prenda UNIQUE (pedido_id, prenda_id),
    CONSTRAINT ck_items_cantidad      CHECK (cantidad BETWEEN 1 AND 10),
    CONSTRAINT ck_items_precio        CHECK (precio_unitario > 0),
    CONSTRAINT ck_items_subtotal      CHECK (subtotal = cantidad * precio_unitario)
);
CREATE INDEX ix_items_artesano ON pedido_items (artesano_id);
CREATE INDEX ix_items_prenda   ON pedido_items (prenda_id);

CREATE VIEW v_catalogo AS
SELECT p.id,
       p.nombre,
       u.nombre_publico AS artesano,
       p.artesano_id,
       f.nombre         AS fibra,
       p.tinte,
       p.precio_centavos_usd,
       p.stock,
       p.foto
FROM prendas p
JOIN usuarios u ON u.artesano_id = p.artesano_id
JOIN fibras   f ON f.id = p.fibra_id
ORDER BY p.creado_en, p.id;

CREATE VIEW v_ventas_artesano AS
SELECT i.artesano_id,
       i.pedido_id,
       o.creado_en AS fecha,
       i.prenda_id,
       i.nombre_prenda,
       i.cantidad,
       i.precio_unitario,
       i.subtotal,
       o.moneda
FROM pedido_items i
JOIN pedidos o ON o.id = i.pedido_id
ORDER BY o.creado_en DESC, i.id DESC;

COMMIT;