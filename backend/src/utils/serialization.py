from sqlalchemy.inspection import inspect
def serialize(row):
 return {c.key:getattr(row,c.key) for c in inspect(row).mapper.column_attrs}
def rows(query): return [serialize(row) for row in query]
