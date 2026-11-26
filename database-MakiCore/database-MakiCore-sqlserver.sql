IF DB_ID(N'maki') IS NULL
    CREATE DATABASE maki;
GO

USE maki;
GO

CREATE SEQUENCE seq_artesano_id   AS BIGINT START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_prenda_codigo AS BIGINT START WITH 1 INCREMENT BY 1;
GO

CREATE TABLE artesanos (
    artesano_id NVARCHAR(12) NOT NULL
        CONSTRAINT pk_artesanos PRIMARY KEY
);
GO

CREATE TABLE usuarios (
    id              BIGINT         IDENTITY(1,1) NOT NULL
        CONSTRAINT pk_usuarios PRIMARY KEY,
    correo          NVARCHAR(254)  NOT NULL,
    clave_hash      NVARCHAR(255)  NOT NULL,
    rol             NVARCHAR(20)   NOT NULL,
    artesano_id     NVARCHAR(12)   NULL,
    nombre_publico  NVARCHAR(100)  NULL,
    creado_en       DATETIMEOFFSET NOT NULL
        CONSTRAINT df_usuarios_creado DEFAULT SYSDATETIMEOFFSET(),

    CONSTRAINT uq_usuarios_correo     UNIQUE (correo),
    CONSTRAINT fk_usuarios_artesano   FOREIGN KEY (artesano_id)
        REFERENCES artesanos (artesano_id),
    CONSTRAINT ck_usuarios_rol        CHECK (rol IN (N'comprador', N'artesano')),
    CONSTRAINT ck_usuarios_correo_min CHECK (
        correo COLLATE Latin1_General_BIN2 = LOWER(correo) COLLATE Latin1_General_BIN2),
    CONSTRAINT ck_usuarios_artesano   CHECK (
        (rol = N'artesano'
            AND artesano_id COLLATE Latin1_General_BIN2 LIKE N'ART-[0-9][0-9][0-9][0-9]%'
            AND artesano_id COLLATE Latin1_General_BIN2 NOT LIKE N'ART-%[^0-9]%'
            AND nombre_publico IS NOT NULL)
     OR (rol = N'comprador' AND artesano_id IS NULL)
    )
);
GO

CREATE UNIQUE INDEX uq_usuarios_artesano_id
    ON usuarios (artesano_id) WHERE artesano_id IS NOT NULL;
GO

CREATE TRIGGER trg_usuarios_artesano
ON usuarios
INSTEAD OF INSERT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @nuevos TABLE (correo NVARCHAR(254) PRIMARY KEY, n BIGINT NOT NULL);

    INSERT INTO @nuevos (correo, n)
    SELECT correo, NEXT VALUE FOR seq_artesano_id
    FROM inserted
    WHERE rol = N'artesano' AND artesano_id IS NULL;

    INSERT INTO artesanos (artesano_id)
    SELECT N'ART-' + FORMAT(n, '0000') FROM @nuevos;

    INSERT INTO artesanos (artesano_id)
    SELECT i.artesano_id
    FROM inserted i
    WHERE i.rol = N'artesano'
      AND i.artesano_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM artesanos a WHERE a.artesano_id = i.artesano_id);

    INSERT INTO usuarios (correo, clave_hash, rol, artesano_id, nombre_publico, creado_en)
    SELECT i.correo,
           i.clave_hash,
           i.rol,
           CASE WHEN i.rol = N'artesano'
                THEN COALESCE(i.artesano_id, N'ART-' + FORMAT(n.n, '0000')) END,
           CASE WHEN i.rol = N'artesano'
                THEN COALESCE(i.nombre_publico,
                              N'Artesano ' + COALESCE(i.artesano_id, N'ART-' + FORMAT(n.n, '0000'))) END,
           COALESCE(i.creado_en, SYSDATETIMEOFFSET())
    FROM inserted i
    LEFT JOIN @nuevos n ON n.correo = i.correo;
END;
GO

CREATE TABLE sesiones (
    token_hash  CHAR(64)       NOT NULL
        CONSTRAINT pk_sesiones PRIMARY KEY,
    usuario_id  BIGINT         NOT NULL,
    expira_en   DATETIMEOFFSET NOT NULL,
    creada_en   DATETIMEOFFSET NOT NULL
        CONSTRAINT df_sesiones_creada DEFAULT SYSDATETIMEOFFSET(),

    CONSTRAINT fk_sesiones_usuario FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id) ON DELETE CASCADE
);
CREATE INDEX ix_sesiones_usuario ON sesiones (usuario_id);
CREATE INDEX ix_sesiones_expira  ON sesiones (expira_en);
GO

CREATE TABLE fibras (
    id      BIGINT        IDENTITY(1,1) NOT NULL
        CONSTRAINT pk_fibras PRIMARY KEY,
    nombre  NVARCHAR(30)  NOT NULL,
    clave   NVARCHAR(30)  NOT NULL,

    CONSTRAINT uq_fibras_clave        UNIQUE (clave),
    CONSTRAINT ck_fibras_nombre_largo CHECK (LEN(nombre) BETWEEN 3 AND 30),
    CONSTRAINT ck_fibras_clave_min    CHECK (
        clave COLLATE Latin1_General_BIN2 = LOWER(clave) COLLATE Latin1_General_BIN2)
);
GO

CREATE TABLE prendas (
    id                   NVARCHAR(40) NOT NULL
        CONSTRAINT pk_prendas PRIMARY KEY
        CONSTRAINT df_prendas_id
            DEFAULT (N'MAKI-' + FORMAT(NEXT VALUE FOR seq_prenda_codigo, '0000')),
    nombre               NVARCHAR(100)  NOT NULL,
    tinte                NVARCHAR(100)  NOT NULL,
    precio_centavos_usd  INT            NOT NULL,
    stock                INT            NOT NULL,
    foto                 NVARCHAR(MAX)  NULL,
    artesano_id          NVARCHAR(12)   NOT NULL,
    fibra_id             BIGINT         NOT NULL,
    creado_en            DATETIMEOFFSET NOT NULL
        CONSTRAINT df_prendas_creado DEFAULT SYSDATETIMEOFFSET(),

    CONSTRAINT fk_prendas_artesano FOREIGN KEY (artesano_id) REFERENCES artesanos (artesano_id),
    CONSTRAINT fk_prendas_fibra    FOREIGN KEY (fibra_id)    REFERENCES fibras (id),
    CONSTRAINT ck_prendas_precio CHECK (precio_centavos_usd > 0 AND precio_centavos_usd <= 1000000),
    CONSTRAINT ck_prendas_stock  CHECK (stock >= 0 AND stock <= 9999),
    CONSTRAINT ck_prendas_foto   CHECK (
        foto IS NULL
        OR foto LIKE N'data:image/jpeg;base64,%'
        OR foto LIKE N'data:image/png;base64,%'
        OR foto LIKE N'data:image/webp;base64,%')
);
CREATE INDEX ix_prendas_artesano ON prendas (artesano_id);
CREATE INDEX ix_prendas_fibra    ON prendas (fibra_id);
GO

CREATE TABLE pedidos (
    id            BIGINT         IDENTITY(1,1) NOT NULL
        CONSTRAINT pk_pedidos PRIMARY KEY,
    comprador_id  BIGINT         NOT NULL,
    estado        NVARCHAR(20)   NOT NULL
        CONSTRAINT df_pedidos_estado DEFAULT N'Aprobado',
    moneda        NVARCHAR(3)    NOT NULL,
    zona          NVARCHAR(10)   NOT NULL,
    subtotal      INT            NOT NULL,
    envio         INT            NOT NULL,
    total         INT            NOT NULL,
    plataforma    INT            NOT NULL,
    cooperativa   INT            NOT NULL,
    creado_en     DATETIMEOFFSET NOT NULL
        CONSTRAINT df_pedidos_creado DEFAULT SYSDATETIMEOFFSET(),

    CONSTRAINT fk_pedidos_comprador FOREIGN KEY (comprador_id) REFERENCES usuarios (id),
    CONSTRAINT ck_pedidos_estado  CHECK (estado IN (N'Aprobado')),
    CONSTRAINT ck_pedidos_moneda  CHECK (moneda IN (N'USD', N'EUR')),
    CONSTRAINT ck_pedidos_zona    CHECK (zona IN (N'America', N'Europa', N'Otros')),
    CONSTRAINT ck_pedidos_montos  CHECK (subtotal >= 0 AND envio >= 0 AND total >= 0
                                         AND plataforma >= 0 AND cooperativa >= 0),
    CONSTRAINT ck_pedidos_total   CHECK (total = subtotal + envio),
    CONSTRAINT ck_pedidos_reparto CHECK (plataforma + cooperativa = subtotal)
);
CREATE INDEX ix_pedidos_comprador ON pedidos (comprador_id, creado_en DESC);
GO

CREATE TABLE pedido_items (
    id               BIGINT        IDENTITY(1,1) NOT NULL
        CONSTRAINT pk_pedido_items PRIMARY KEY,
    pedido_id        BIGINT        NOT NULL,
    prenda_id        NVARCHAR(40)  NOT NULL,
    artesano_id      NVARCHAR(12)  NOT NULL,
    nombre_prenda    NVARCHAR(100) NOT NULL,
    cantidad         INT           NOT NULL,
    precio_unitario  INT           NOT NULL,
    subtotal         INT           NOT NULL,

    CONSTRAINT fk_items_pedido   FOREIGN KEY (pedido_id)   REFERENCES pedidos (id) ON DELETE CASCADE,
    CONSTRAINT fk_items_prenda   FOREIGN KEY (prenda_id)   REFERENCES prendas (id),
    CONSTRAINT fk_items_artesano FOREIGN KEY (artesano_id) REFERENCES artesanos (artesano_id),
    CONSTRAINT uq_items_pedido_prenda UNIQUE (pedido_id, prenda_id),
    CONSTRAINT ck_items_cantidad      CHECK (cantidad BETWEEN 1 AND 10),
    CONSTRAINT ck_items_precio        CHECK (precio_unitario > 0),
    CONSTRAINT ck_items_subtotal      CHECK (subtotal = cantidad * precio_unitario)
);
CREATE INDEX ix_items_artesano ON pedido_items (artesano_id);
CREATE INDEX ix_items_prenda   ON pedido_items (prenda_id);
GO

CREATE VIEW v_catalogo AS
SELECT p.id,
       p.nombre,
       u.nombre_publico AS artesano,
       p.artesano_id,
       f.nombre         AS fibra,
       p.tinte,
       p.precio_centavos_usd,
       p.stock,
       p.foto,
       p.creado_en
FROM prendas p
JOIN usuarios u ON u.artesano_id = p.artesano_id
JOIN fibras   f ON f.id = p.fibra_id;
GO

CREATE VIEW v_ventas_artesano AS
SELECT i.artesano_id,
       i.pedido_id,
       o.creado_en AS fecha,
       i.prenda_id,
       i.nombre_prenda,
       i.cantidad,
       i.precio_unitario,
       i.subtotal,
       o.moneda,
       i.id AS item_id
FROM pedido_items i
JOIN pedidos o ON o.id = i.pedido_id;
GO

PRINT N'Esquema de Maki Core creado en SQL Server.';
GO