def safe_cell(value):
 return "'"+value if isinstance(value,str) and value.startswith(("=","+","-","@","\t","\r")) else value
