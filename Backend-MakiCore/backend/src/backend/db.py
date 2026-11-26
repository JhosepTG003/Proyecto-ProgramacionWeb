"""Conexion a SQL Server con pyodbc (solo se usa si existe DATABASE_URL).

DATABASE_URL ahora es una cadena de conexion ODBC, por ejemplo:
  DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=maki;
  Trusted_Connection=yes;TrustServerCertificate=yes;

Cada operacion abre una conexion (pyodbc ya reutiliza conexiones con su pool interno de ODBC) y,
al salir del bloque `with conexion()`, se confirma (commit) o se deshace (rollback) si hubo un error.

La conexion que se entrega imita lo que antes daba psycopg: execute(sql, params) devuelve un
cursor con fetchone()/fetchall() que entregan diccionarios, asi los repositorios casi no cambian.
Los parametros de las consultas se escriben con ? (no con %s).
"""

from __future__ import annotations

import struct
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

import pyodbc

from backend import config

# Tipo ODBC de DATETIMEOFFSET: pyodbc no lo entiende solo y lo entrega como bytes.
_SQL_SS_TIMESTAMPOFFSET = -155


def _convertir_datetimeoffset(valor: bytes) -> datetime:
    anio, mes, dia, hora, minuto, segundo, nanos, tz_h, tz_m = struct.unpack("<6hI2h", valor)
    return datetime(
        anio,
        mes,
        dia,
        hora,
        minuto,
        segundo,
        nanos // 1000,
        timezone(timedelta(hours=tz_h, minutes=tz_m)),
    )


class _Cursor:
    """Envuelve un cursor de pyodbc para devolver filas como diccionarios."""

    def __init__(self, cur: pyodbc.Cursor) -> None:
        self._cur = cur

    def _a_dict(self, fila: Any) -> dict[str, Any]:
        nombres = [c[0] for c in self._cur.description]
        return dict(zip(nombres, fila))

    def fetchone(self) -> dict[str, Any] | None:
        fila = self._cur.fetchone()
        return None if fila is None else self._a_dict(fila)

    def fetchall(self) -> list[dict[str, Any]]:
        return [self._a_dict(f) for f in self._cur.fetchall()]

    @property
    def rowcount(self) -> int:
        return self._cur.rowcount


class _Conexion:
    """Envuelve una conexion de pyodbc con la misma forma de uso que tenia la de psycopg."""

    def __init__(self, conn: pyodbc.Connection) -> None:
        self._conn = conn

    def execute(self, sql: str, params: Sequence[Any] = ()) -> _Cursor:
        cur = self._conn.cursor()
        cur.execute(sql, tuple(params))
        return _Cursor(cur)

    def executemany(self, sql: str, filas: Sequence[Sequence[Any]]) -> None:
        cur = self._conn.cursor()
        cur.executemany(sql, [tuple(f) for f in filas])


def _obtener_pool() -> None:
    """Comprueba que se puede conectar (por si main.py la llama al arrancar). Ya no hay pool propio."""
    with conexion() as conn:
        conn.execute("SELECT 1 AS ok").fetchone()


@contextmanager
def conexion() -> Iterator[_Conexion]:
    conn = pyodbc.connect(config.DATABASE_URL, autocommit=False)
    conn.add_output_converter(_SQL_SS_TIMESTAMPOFFSET, _convertir_datetimeoffset)
    try:
        yield _Conexion(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def cerrar_pool() -> None:
    """No hay nada que cerrar: cada conexion se cierra al terminar su bloque. Se deja por compatibilidad."""
    return None
