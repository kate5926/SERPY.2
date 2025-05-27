from sintactico_NEW_C import nodoPadre

print("\n")

class SymbolAlreadyDefinedError(Exception):
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(f"Error semántico (línea {line}): {message}" if line else f"Error semántico: {message}")

class UndefinedVariableError(Exception):
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(f"Error semántico (línea {line}): {message}" if line else f"Error semántico: {message}")

class SymbolTable:
    def __init__(self):
        self.symbols = []
        self.functions = set()
        self.current_scope = "global"
        self.scope_stack = ["global"]

    def insert(self, data_type, name, scope, is_function=True, line=None):
        symbol = {
            'data_type': data_type,
            'name': name,
            'scope': scope,
            'is_function': is_function,
            'line': line
        }
        self.symbols.append(symbol)
        if is_function:
            self.functions.add(name)

    def lookup(self, name, scope=None):
        if scope is None:
            scope = self.current_scope
        
        # Buscar en el ámbito actual primero
        for symbol in reversed(self.symbols):
            if symbol['name'] == name and symbol['scope'] == scope:
                return symbol
        
        # Si no se encuentra, buscar en ámbitos superiores
        if scope != "global":
            for symbol in self.symbols:
                if symbol['name'] == name and symbol['scope'] == "global":
                    return symbol
        return None

    def enter_scope(self, function_name):
        self.scope_stack.append(function_name)
        self.current_scope = function_name

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]

def registrar_en_tabla(nodo, symbol_table, scope="global"):
    if nodo is None:
        return

    # Obtener línea (si está disponible en el nodo)
    line = getattr(nodo, 'linea', None)

    # Registrar funciones
    if getattr(nodo, 'simbolo_lexer', None) == "FUNCTION":
        try:
            tipo_nodo = nodo.children[0].children[0].children[0].valor
            function_name = nodo.children[2].valor
            
            if symbol_table.lookup(function_name, "global"):
                raise SymbolAlreadyDefinedError(f"La función '{function_name}' ya está definida", line)
            
            symbol_table.insert(tipo_nodo, function_name, "global", True, line)
            symbol_table.enter_scope(function_name)
            
            # Registrar parámetros
            if len(nodo.children) > 3:  # Asumiendo que los parámetros están en children[3]
                parametros_node = nodo.children[3]
                for child in parametros_node.children:
                    if getattr(child, 'simbolo_lexer', None) == "TI":
                        param_type = child.children[0].children[0].children[0].valor
                        param_name = child.children[1].valor
                        if symbol_table.lookup(param_name, function_name):
                            raise SymbolAlreadyDefinedError(f"El parámetro '{param_name}' ya está definido", line)
                        symbol_table.insert(param_type, param_name, function_name, False, line)
            
            # Procesar el cuerpo de la función
            for child in nodo.children[4:]:  # Asumiendo que el cuerpo está después de los parámetros
                registrar_en_tabla(child, symbol_table, function_name)
            
            symbol_table.exit_scope()
            return  # Salir después de procesar la función para evitar procesar hijos nuevamente
        
        except IndexError as e:
            raise SyntaxError(f"Error al procesar la función: estructura incorrecta. {str(e)}")

    # Registrar variables
    elif getattr(nodo, 'simbolo_lexer', None) == "Crear_variables":
        try:
            tipo_nodo = nodo.children[0].children[0].children[0].valor
            var_name = nodo.children[1].valor
            
            if symbol_table.lookup(var_name, scope):
                raise SymbolAlreadyDefinedError(f"La variable '{var_name}' ya está definida en este ámbito", line)
            
            symbol_table.insert(tipo_nodo, var_name, scope, False, line)
        except IndexError as e:
            raise SyntaxError(f"Error al procesar declaración de variable: estructura incorrecta. {str(e)}")

    # Verificar uso de variables/funciones
    elif getattr(nodo, 'simbolo_lexer', None) in ["FH", "F'", "TX", "sentencia"]:
        for child in nodo.children:
            if getattr(child, 'simbolo_lexer', None) == "ID":
                var_name = child.valor
                found = symbol_table.lookup(var_name, scope)
                
                # Verificar si es una llamada a función
                is_function_call = False
                if len(child.children) > 0:
                    first_child = child.children[0]
                    if getattr(first_child, 'simbolo_lexer', None) == "PARENTESIS_ABIERTO":
                        is_function_call = True
                
                if is_function_call:
                    if var_name not in symbol_table.functions:
                        raise UndefinedVariableError(f"Función '{var_name}' no definida", line)
                elif not found:
                    raise UndefinedVariableError(f"Variable '{var_name}' no definida", line)

    # Procesar hijos recursivamente
    for child in nodo.children:
        registrar_en_tabla(child, symbol_table, scope)

# Crear y poblar la tabla de símbolos
symbol_table = SymbolTable()

try:
    registrar_en_tabla(nodoPadre, symbol_table)

    # Mostrar resultados
    print("\nTabla de Símbolos:")
    print(f"{'Tipo':<10} | {'Nombre':<15} | {'Ámbito':<15} | {'Tipo':<10} | {'Línea':<5}")
    print("-" * 60)
    for symbol in symbol_table.symbols:
        data_type = symbol['data_type'] or 'N/A'
        name = symbol['name']
        scope = symbol['scope']
        kind = "Función" if symbol['is_function'] else "Variable"
        line = symbol.get('line', 'N/A')
        print(f"{data_type:<10} | {name:<15} | {scope:<15} | {kind:<10} | {line:<5}")

except (SymbolAlreadyDefinedError, UndefinedVariableError) as e:
    print(f"\n{e}")
except Exception as e:
    print(f"\nError inesperado: {str(e)}")
