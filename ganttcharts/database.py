"""Module for connecting to the various databases."""

import logging
import os

import sqlalchemy

from . import models


DATABASE_URI_KEY = 'DATABASE_URL'

logger = logging.getLogger(__name__)


_sql_engine = None
_sql_connection = None


def get_sql_database_uri(key=DATABASE_URI_KEY):
    try:
        return os.environ[key]
    except KeyError:
        msg = 'SQL database URI is not configured. ' \
              'Please set {key} environment variable.'.format(key=key)
        raise RuntimeError(msg)


def connect_to_sql():
    global _sql_engine, _sql_connection

    if _sql_engine is not None or \
            (_sql_connection is not None and not _sql_connection.closed):
        raise RuntimeError('Attempted to connect, but already connected.')

    uri = get_sql_database_uri()

    logger.info('Connecting to SQL database.')

    engine = sqlalchemy.create_engine(uri)
    connection = engine.connect()

    models.Base.prepare(engine)
    models.Session.configure(bind=connection)

    _sql_engine = engine
    _sql_connection = connection

    return engine, connection


def get_sql_engine():
    if _sql_engine is None:
        connect_to_sql()
    return _sql_engine


def get_sql_connection():
    if _sql_connection is None or _sql_connection.closed:
        connect_to_sql()
    return _sql_connection


@sqlalchemy.event.listens_for(sqlalchemy.pool.Pool, 'checkout')
def sql_ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        # connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        raise sqlalchemy.exc.DisconnectionError()
    cursor.close()
