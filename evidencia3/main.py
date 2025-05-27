class SymbolTable:
    def __init__(self):
        self.global_scope = {}  # Diccionario para el ámbito global
        self.functions = {}     # Diccionario para funciones
        self.current_scope = self.global_scope
        self.scope_stack = [self.global_scope]
class VariableSymbol:
    def __init__(self, name, type, scope, line_declared):
        self.name = name
        self.type = type
        self.scope = scope
        self.line = line_declared

class FunctionSymbol:
    def __init__(self, name, return_type, parameters, line_declared):
        self.name = name
        self.return_type = return_type
        self.parameters = parameters  # Lista de tuples (nombre, tipo)
        self.line = line_declared
        self.local_vars = {}  # Variables locales
class SymbolTable:
    # ... (continuación de la clase anterior)
    
    def add_variable(self, name, var_type, line):
        if name in self.current_scope:
            raise SymbolAlreadyDefinedError(f"Variable '{name}' ya está definida en este ámbito")
        self.current_scope[name] = VariableSymbol(name, var_type, self.current_scope_name(), line)
    
    def add_function(self, name, return_type, parameters, line):
        if name in self.functions:
            raise SymbolAlreadyDefinedError(f"Función '{name}' ya está definida")
        self.functions[name] = FunctionSymbol(name, return_type, parameters, line)
        # Entramos al ámbito de la función
        self.enter_scope(name)
    
    def lookup_variable(self, name):
        # Busca en los ámbitos desde el actual hacia afuera
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None
    
    def lookup_function(self, name):
        return self.functions.get(name)
    
    def enter_scope(self, function_name):
        if function_name in self.functions:
            new_scope = self.functions[function_name].local_vars
            self.scope_stack.append(new_scope)
            self.current_scope = new_scope
    
    def exit_scope(self):
        if len(self.scope_stack) > 1:  # No salir del ámbito global
            self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]
    
    def current_scope_name(self):
        if len(self.scope_stack) > 1:
            # El ámbito actual es una función
            for name, func in self.functions.items():
                if func.local_vars is self.current_scope:
                    return name
        return "global"

def build_symbol_table(node, symbol_table):
    if node is None:
        return
    
    # Registro de funciones
    if node.type == "function_declaration":
        func_name = node.children[1].value  # Nombre de la función
        return_type = node.children[0].children[0].value  # Tipo de retorno
        
        # Procesar parámetros
        params = []
        params_node = node.children[3]  # Nodo de parámetros
        if params_node.children:
            for param in params_node.children:
                param_type = param.children[0].children[0].value
                param_name = param.children[1].value
                params.append((param_name, param_type))
        
        # Registrar función
        symbol_table.add_function(func_name, return_type, params, node.line)
        
        # Registrar parámetros como variables
        for param_name, param_type in params:
            symbol_table.add_variable(param_name, param_type, node.line)
        
        # Procesar cuerpo de la función
        build_symbol_table(node.children[5], symbol_table)  # Bloque de la función
        
        # Salir del ámbito de la función
        symbol_table.exit_scope()
    
    # Registro de variables globales
    elif node.type == "global_variable_declaration":
        var_type = node.children[0].children[0].value
        var_name = node.children[1].value
        symbol_table.add_variable(var_name, var_type, node.line)
    
    # Verificación de uso de variables
    elif node.type == "variable_reference":
        var_name = node.children[0].value
        if not symbol_table.lookup_variable(var_name):
            raise UndefinedVariableError(f"Variable '{var_name}' no definida")
    
    # Verificación de llamadas a funciones
    elif node.type == "function_call":
        func_name = node.children[0].value
        if not symbol_table.lookup_function(func_name):
            raise UndefinedFunctionError(f"Función '{func_name}' no definida")
    
    # Procesar hijos recursivamente
    for child in node.children:
        build_symbol_table(child, symbol_table)
class SemanticError(Exception):
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(f"Error semántico (línea {line}): {message}" if line else f"Error semántico: {message}")

class SymbolAlreadyDefinedError(SemanticError):
    pass

class UndefinedVariableError(SemanticError):
    pass

class UndefinedFunctionError(SemanticError):
    pass

class TypeMismatchError(SemanticError):
    pass
