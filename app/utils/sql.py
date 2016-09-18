import collections

from django.db import models, connection as django_connection
from django.utils import timezone


def get_table(model):
    assert issubclass(model, models.Model)

    return model._meta.db_table


def get_column(model, field):
    assert issubclass(model, models.Model)

    return model._meta.get_field_by_name(field)[0].get_attname_column()[1]


def get_primary_column(model):
    assert issubclass(model, models.Model)

    primary_key = next(field for field in model._meta.fields
                       if field.primary_key)
    return primary_key.get_attname_column()[1]


class MCL(object):
    """Model column list specification."""

    TYPE_REPLACEMENTS = {
        'serial': 'integer',
    }

    def __init__(self, model, fields=None, exclude=None, connection=None):
        self.model = model
        self.fields = [field for field in model._meta.fields
                       if (fields is None or field.name in fields) and
                       (exclude is None or field.name not in exclude)]
        self.connection = connection or django_connection

    def get_column_name(self, field):
        """Get field column name."""
        return field.get_attname_column()[1]

    def get_column_type(self, field):
        """Get field column type."""
        type = field.db_type(self.connection)
        return self.TYPE_REPLACEMENTS.get(type, type)

    def columns(self):
        """Get tuples of column name and type."""
        return [(self.get_column_name(field), self.get_column_type(field))
                for field in self.fields]

    def values(self, instance):
        """Get list of column values."""
        assert isinstance(instance, self.model)

        values = []

        for field in self.fields:
            value = field.value_from_object(instance)

            if value is None:
                if field.default != models.fields.NOT_PROVIDED:
                    value = field.get_default()

                elif isinstance(field, models.DateTimeField) and \
                        (field.auto_now or field.auto_now_add):
                    value = timezone.now()

            value = field.get_prep_value(value)
            values.append(value)

        return values


class IINE(object):
    """Insert-if-not-exists specification."""

    def __init__(self, table, primary, cl_value=None, cl_match=None):
        """
        Initialize with
        * Table name and primary key column name
        * value: Columns for `VALUES` clause and their types
        * match: Columns for `WHERE` clause and their types
        """
        self.table = table
        self.primary = primary

        assert isinstance(cl_value, collections.Iterable)
        assert isinstance(cl_match, collections.Iterable)

        self.cl_value = cl_value
        self.cl_match = cl_match

    def build(self, size=1):
        """Build query."""
        return (
            'INSERT INTO "{table}" ({cl_value}) '
            'SELECT {cl_value_at_values} '
            'FROM (VALUES {cl_format}) AS "values" ({cl_value}) '
            'LEFT JOIN {table} ON {cl_match} '
            'WHERE "{table}"."{primary}" IS NULL'
        ).format(
            table=self.table,
            primary=self.primary,

            cl_value=self.build_cl_value(),
            cl_value_at_table=self.build_cl_value_at(table=self.table),
            cl_value_at_values=self.build_cl_value_at(table='values'),

            cl_format=self.build_cl_format(size=size),
            cl_match=self.build_cl_match(),
        )

    def build_cl_value(self):
        """Build column list for `VALUES` clause."""
        return ', '.join([
            '"{}"'.format(column)
            for column, type in self.cl_value
        ])

    def build_cl_value_at(self, table=None):
        """Build column list for `SELECT` clause."""
        return ', '.join([
            '"{}"."{}"::{}'.format(table, column, type)
            for column, type in self.cl_value
        ])

    def build_cl_format(self, size):
        """Build values list for `VALUES` clause."""
        cl_format = '({})'.format(', '.join(['%s'] * len(self.cl_value)))
        cl_format = ', '.join([cl_format] * size)
        return cl_format

    def build_cl_match(self):
        """Build conditions for `LEFT JOIN` clause."""
        return ' AND '.join([(
            '(('
            '"{table}"."{column}" = "values"."{column}"::{type}'
            ') OR ('
            '"{table}"."{column}" IS NULL AND "values"."{column}" IS NULL'
            '))'
        ).format(
            table=self.table,
            column=column,
            type=type
        ) for column, type in self.cl_match])


class ModelIINE(IINE):
    """Insert-if-not-exists specification based on a model."""

    def __init__(self, model, mcl_value=None, mcl_match=None):
        assert isinstance(mcl_value, MCL)
        assert isinstance(mcl_match, MCL)

        self.mcl_value = mcl_value
        self.mcl_match = mcl_match

        super().__init__(get_table(model), get_primary_column(model),
                         cl_value=mcl_value.columns(),
                         cl_match=mcl_match.columns())


class StandardIINEModelMixin(object):

    @classmethod
    def get_iine_default_connection(cls):
        return django_connection

    @classmethod
    def get_iine_match_kwargs(cls):
        if cls._meta.unique_together:
            fields = cls._meta.unique_together[0]
        else:
            fields = [next(field for field in cls._meta.fields
                           if field.unique and not field.primary_key).name]

        return {'fields': fields}

    @classmethod
    def get_iine_value_kwargs(cls):
        return {'exclude': ('id',)}

    def insert_if_not_exists(self, connection=None):
        """Insert this instance if it doesn't exist."""
        return self.insert_if_not_exist([self], connection=None)

    @classmethod
    def insert_if_not_exist(cls, instances, connection=None):
        """Insert instances that don't exist."""
        connection = connection or cls.get_iine_default_connection()

        iine = ModelIINE(
            cls,
            mcl_value=MCL(cls, connection=connection,
                          **cls.get_iine_value_kwargs()),
            mcl_match=MCL(cls, connection=connection,
                          **cls.get_iine_match_kwargs()),
        )

        query = iine.build(size=len(instances))

        values = []
        for instance in instances:
            values.extend(iine.mcl_value.values(instance))

        cursor = connection.cursor()
        cursor.execute(query, values)
        cursor.close()
