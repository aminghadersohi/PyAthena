from sqlalchemy import types

from pyathena.sqlalchemy.base import ischema_names


def test_double_column_type():
    assert ischema_names["double"] is types.DOUBLE
