from valor import Valor
from regla import Regla
from nodo import Nodo
import csv

class Sintactico:
    def __init__(self, tokens, archivo_tabla_csv):
        self.tokens = tokens
        self.tabla = self._cargar_tabla_csv(archivo_tabla_csv)
        self.reglas = self._extraer_reglas()
        # Inicializar con valores por defecto (0,0)
        self.pila = [Valor("PROGRAMA", "$", 0, 0)]
        self._mapeo_tokens = self._crear_mapeo_tokens()

    def _cargar_tabla_csv(self, archivo):
        """Carga la tabla sintáctica desde un archivo CSV"""
        tabla = {}
        try:
            with open(archivo, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Verifica encabezados
                if 'Nonterminal' not in reader.fieldnames:
                    raise ValueError("El CSV debe tener columna 'Nonterminal'")
                
                for row in reader:
                    estado = row['Nonterminal'].strip()
                    for token, accion in row.items():
                        if token != 'Nonterminal':
                            # Procesa cada acción de manera segura
                            parsed = self._parsear_accion(accion)
                            if parsed[0] != "error":
                                tabla[(estado, token.strip())] = parsed
        except FileNotFoundError:
            raise Exception(f"Error: Archivo CSV no encontrado: {archivo}")
        except csv.Error as e:
            raise Exception(f"Error de formato en CSV: {str(e)}")
        except Exception as e:
            raise Exception(f"Error cargando tabla CSV: {str(e)}")
        return tabla

    def _parsear_accion(self, accion_str):
        """Convierte una acción de la tabla en un formato procesable"""
        # Primero verifica si accion_str es None o no es string
        if accion_str is None:
            return ("error",)
        
        # Convierte a string y elimina espacios
        accion_str = str(accion_str).strip()
        
        # Si está vacío después de strip()
        if not accion_str:
            return ("error",)
        
        # Maneja acciones shift (números)
        if accion_str.isdigit():
            return ("shift", int(accion_str))
        
        # Maneja acciones reduce (producciones)
        if '->' in accion_str:
            try:
                lado_izq, lado_der = [parte.strip() for parte in accion_str.split('->', 1)]
                num_regla = self._obtener_num_regla(lado_izq, lado_der)
                return ("reduce", num_regla) if num_regla is not None else ("error",)
            except Exception as e:
                return ("error", f"Error en la producción: {str(e)}")
        
        # Si no es shift ni reduce, es error
        return ("error", f"Acción no reconocida: {accion_str}")

    def _obtener_num_regla(self, lado_izq, lado_der):
        """Obtiene el número de regla basado en la producción"""
        # Mapeo de producciones a números de regla
        reglas = {
            'PROGRAMA -> lista_sentencias': 0,
            'lista_sentencias -> sentencia lista_sentencias': 1,
            'lista_sentencias -> ε': 2,
            'sentencia -> VAR IDENTIFICADOR IGUAL expresion PUNTOYCOMA': 3,
            'sentencia -> IDENTIFICADOR asignacion_o_llamada PUNTOYCOMA': 4,
            'sentencia -> RETORNAR expresion PUNTOYCOMA': 5,
            'sentencia -> IMPRIMIR PAR_IZQ lista_argumentos PAR_DER PUNTOYCOMA': 6,
            'sentencia -> si_sentencia': 7,
            'sentencia -> mientras_sentencia': 8,
            'sentencia -> para_sentencia': 9,
            'sentencia -> funcion_def': 10,
            'asignacion_o_llamada -> IGUAL expresion': 11,
            'asignacion_o_llamada -> PAR_IZQ lista_argumentos PAR_DER': 12,
            'lista_argumentos -> expresion lista_argumentos_cont': 13,
            'lista_argumentos -> ε': 14,
            'lista_argumentos_cont -> COMA expresion lista_argumentos_cont': 15,
            'lista_argumentos_cont -> ε': 16,
            'si_sentencia -> SI PAR_IZQ expresion PAR_DER bloque sino_parte': 17,
            'sino_parte -> SINO bloque': 18,
            'sino_parte -> ε': 19,
            'mientras_sentencia -> MIENTRAS PAR_IZQ expresion PAR_DER bloque': 20,
            'para_sentencia -> PARA PAR_IZQ para_inicio PUNTOYCOMA expresion PUNTOYCOMA IDENTIFICADOR IGUAL expresion PAR_DER bloque': 21,
            'para_inicio -> VAR IDENTIFICADOR IGUAL expresion': 22,
            'para_inicio -> IDENTIFICADOR IGUAL expresion': 23,
            'funcion_def -> DEFINIR IDENTIFICADOR PAR_IZQ parametros PAR_DER bloque': 24,
            'parametros -> IDENTIFICADOR parametros_cont': 25,
            'parametros -> ε': 26,
            'parametros_cont -> COMA IDENTIFICADOR parametros_cont': 27,
            'parametros_cont -> ε': 28,
            'bloque -> LLAVE_IZQ lista_sentencias LLAVE_DER': 29,
            'expresion -> exp_logico_and exp_logico_or_resto': 30,
            'exp_logico_or_resto -> O_LOGICO exp_logico_and exp_logico_or_resto': 31,
            'exp_logico_or_resto -> ε': 32,
            'exp_logico_and -> exp_igualdad exp_logico_and_resto': 33,
            'exp_logico_and_resto -> Y_LOGICO exp_igualdad exp_logico_and_resto': 34,
            'exp_logico_and_resto -> ε': 35,
            'exp_igualdad -> exp_comparacion exp_igualdad_resto': 36,
            'exp_igualdad_resto -> op_igualdad exp_comparacion exp_igualdad_resto': 37,
            'exp_igualdad_resto -> ε': 38,
            'op_igualdad -> IGUAL_IGUAL': 39,
            'op_igualdad -> DIFERENTE': 40,
            'exp_comparacion -> exp_suma exp_comparacion_resto': 41,
            'exp_comparacion_resto -> op_comp exp_suma exp_comparacion_resto': 42,
            'exp_comparacion_resto -> ε': 43,
            'op_comp -> MAYOR': 44,
            'op_comp -> MENOR': 45,
            'op_comp -> MAYOR_IGUAL': 46,
            'op_comp -> MENOR_IGUAL': 47,
            'exp_suma -> exp_mult exp_suma_resto': 48,
            'exp_suma_resto -> op_suma exp_mult exp_suma_resto': 49,
            'exp_suma_resto -> ε': 50,
            'op_suma -> MAS': 51,
            'op_suma -> MENOS': 52,
            'exp_mult -> exp_potencia exp_mult_resto': 53,
            'exp_mult_resto -> op_mult exp_potencia exp_mult_resto': 54,
            'exp_mult_resto -> ε': 55,
            'op_mult -> MULT': 56,
            'op_mult -> DIV': 57,
            'exp_potencia -> exp_unario exp_potencia_resto': 58,
            'exp_potencia_resto -> POTENCIA exp_unario exp_potencia_resto': 59,
            'exp_potencia_resto -> ε': 60,
            'exp_unario -> NEGACION exp_unario': 61,
            'exp_unario -> MENOS exp_unario': 62,
            'exp_unario -> primario': 63,
            'primario -> NUMERO': 64,
            'primario -> CADENA': 65,
            'primario -> VERDADERO': 66,
            'primario -> FALSO': 67,
            'primario -> IDENTIFICADOR primario_llamada_opcional': 68,
            'primario -> PAR_IZQ expresion PAR_DER': 69,
            'primario_llamada_opcional -> PAR_IZQ lista_argumentos PAR_DER': 70,
            'primario_llamada_opcional -> ε': 71
        }
        produccion = f"{lado_izq} -> {lado_der}"
        return reglas.get(produccion, None)

    def _extraer_reglas(self):
        """Extrae las reglas gramaticales de la tabla"""
        reglas = {}
        # Crear un diccionario para acceso por índice
        reglas_lista = [
            Regla(0, 1, "PROGRAMA -> lista_sentencias"),
            Regla(1, 2, "lista_sentencias -> sentencia lista_sentencias"),
            Regla(2, 0, "lista_sentencias -> ε"),
            Regla(3, 5, "sentencia -> VAR IDENTIFICADOR IGUAL expresion PUNTOYCOMA"),
            Regla(4, 3, "sentencia -> IDENTIFICADOR asignacion_o_llamada PUNTOYCOMA"),
            Regla(5, 3, "sentencia -> RETORNAR expresion PUNTOYCOMA"),
            Regla(6, 5, "sentencia -> IMPRIMIR PAR_IZQ lista_argumentos PAR_DER PUNTOYCOMA"),
            Regla(7, 1, "sentencia -> si_sentencia"),
            Regla(8, 1, "sentencia -> mientras_sentencia"),
            Regla(9, 1, "sentencia -> para_sentencia"),
            Regla(10, 1, "sentencia -> funcion_def"),
            Regla(11, 2, "asignacion_o_llamada -> IGUAL expresion"),
            Regla(12, 3, "asignacion_o_llamada -> PAR_IZQ lista_argumentos PAR_DER"),
            Regla(13, 2, "lista_argumentos -> expresion lista_argumentos_cont"),
            Regla(14, 0, "lista_argumentos -> ε"),
            Regla(15, 3, "lista_argumentos_cont -> COMA expresion lista_argumentos_cont"),
            Regla(16, 0, "lista_argumentos_cont -> ε"),
            Regla(17, 6, "si_sentencia -> SI PAR_IZQ expresion PAR_DER bloque sino_parte"),
            Regla(18, 2, "sino_parte -> SINO bloque"),
            Regla(19, 0, "sino_parte -> ε"),
            Regla(20, 5, "mientras_sentencia -> MIENTRAS PAR_IZQ expresion PAR_DER bloque"),
            Regla(21, 11, "para_sentencia -> PARA PAR_IZQ para_inicio PUNTOYCOMA expresion PUNTOYCOMA IDENTIFICADOR IGUAL expresion PAR_DER bloque"),
            Regla(22, 4, "para_inicio -> VAR IDENTIFICADOR IGUAL expresion"),
            Regla(23, 3, "para_inicio -> IDENTIFICADOR IGUAL expresion"),
            Regla(24, 6, "funcion_def -> DEFINIR IDENTIFICADOR PAR_IZQ parametros PAR_DER bloque"),
            Regla(25, 2, "parametros -> IDENTIFICADOR parametros_cont"),
            Regla(26, 0, "parametros -> ε"),
            Regla(27, 3, "parametros_cont -> COMA IDENTIFICADOR parametros_cont"),
            Regla(28, 0, "parametros_cont -> ε"),
            Regla(29, 3, "bloque -> LLAVE_IZQ lista_sentencias LLAVE_DER"),
            Regla(30, 2, "expresion -> exp_logico_and exp_logico_or_resto"),
            Regla(31, 3, "exp_logico_or_resto -> O_LOGICO exp_logico_and exp_logico_or_resto"),
            Regla(32, 0, "exp_logico_or_resto -> ε"),
            Regla(33, 2, "exp_logico_and -> exp_igualdad exp_logico_and_resto"),
            Regla(34, 3, "exp_logico_and_resto -> Y_LOGICO exp_igualdad exp_logico_and_resto"),
            Regla(35, 0, "exp_logico_and_resto -> ε"),
            Regla(36, 2, "exp_igualdad -> exp_comparacion exp_igualdad_resto"),
            Regla(37, 3, "exp_igualdad_resto -> op_igualdad exp_comparacion exp_igualdad_resto"),
            Regla(38, 0, "exp_igualdad_resto -> ε"),
            Regla(39, 1, "op_igualdad -> IGUAL_IGUAL"),
            Regla(40, 1, "op_igualdad -> DIFERENTE"),
            Regla(41, 2, "exp_comparacion -> exp_suma exp_comparacion_resto"),
            Regla(42, 3, "exp_comparacion_resto -> op_comp exp_suma exp_comparacion_resto"),
            Regla(43, 0, "exp_comparacion_resto -> ε"),
            Regla(44, 1, "op_comp -> MAYOR"),
            Regla(45, 1, "op_comp -> MENOR"),
            Regla(46, 1, "op_comp -> MAYOR_IGUAL"),
            Regla(47, 1, "op_comp -> MENOR_IGUAL"),
            Regla(48, 2, "exp_suma -> exp_mult exp_suma_resto"),
            Regla(49, 3, "exp_suma_resto -> op_suma exp_mult exp_suma_resto"),
            Regla(50, 0, "exp_suma_resto -> ε"),
            Regla(51, 1, "op_suma -> MAS"),
            Regla(52, 1, "op_suma -> MENOS"),
            Regla(53, 2, "exp_mult -> exp_potencia exp_mult_resto"),
            Regla(54, 3, "exp_mult_resto -> op_mult exp_potencia exp_mult_resto"),
            Regla(55, 0, "exp_mult_resto -> ε"),
            Regla(56, 1, "op_mult -> MULT"),
            Regla(57, 1, "op_mult -> DIV"),
            Regla(58, 2, "exp_potencia -> exp_unario exp_potencia_resto"),
            Regla(59, 3, "exp_potencia_resto -> POTENCIA exp_unario exp_potencia_resto"),
            Regla(60, 0, "exp_potencia_resto -> ε"),
            Regla(61, 2, "exp_unario -> NEGACION exp_unario"),
            Regla(62, 2, "exp_unario -> MENOS exp_unario"),
            Regla(63, 1, "exp_unario -> primario"),
            Regla(64, 1, "primario -> NUMERO"),
            Regla(65, 1, "primario -> CADENA"),
            Regla(66, 1, "primario -> VERDADERO"),
            Regla(67, 1, "primario -> FALSO"),
            Regla(68, 2, "primario -> IDENTIFICADOR primario_llamada_opcional"),
            Regla(69, 3, "primario -> PAR_IZQ expresion PAR_DER"),
            Regla(70, 3, "primario_llamada_opcional -> PAR_IZQ lista_argumentos PAR_DER"),
            Regla(71, 0, "primario_llamada_opcional -> ε")
        ]
        
        # Convertir la lista a un diccionario para acceso más eficiente
        for regla in reglas_lista:
            reglas[regla.getId()] = regla  # Changed from getNumero() to getId()
            
        return reglas

    def _crear_mapeo_tokens(self):
        """Crea un mapeo de tokens léxicos a nombres en la tabla sintáctica"""
        return {
            'VAR': 'VAR',
            'IDENTIFICADOR': 'IDENTIFICADOR',
            'IGUAL': 'IGUAL',
            'PUNTOYCOMA': 'PUNTOYCOMA',
            'RETORNAR': 'RETORNAR',
            'IMPRIMIR': 'IMPRIMIR',
            'PAR_IZQ': 'PAR_IZQ',
            'PAR_DER': 'PAR_DER',
            'COMA': 'COMA',
            'SI': 'SI',
            'SINO': 'SINO',
            'MIENTRAS': 'MIENTRAS',
            'PARA': 'PARA',
            'DEFINIR': 'DEFINIR',
            'LLAVE_IZQ': 'LLAVE_IZQ',
            'LLAVE_DER': 'LLAVE_DER',
            'O_LOGICO': 'O_LOGICO',
            'Y_LOGICO': 'Y_LOGICO',
            'NUMERO': 'NUMERO',
            'CADENA': 'CADENA',
            'VERDADERO': 'VERDADERO',
            'FALSO': 'FALSO',
            'IGUAL_IGUAL': 'IGUAL_IGUAL',
            'DIFERENTE': 'DIFERENTE',
            'MAYOR': 'MAYOR',
            'MENOR': 'MENOR',
            'MAYOR_IGUAL': 'MAYOR_IGUAL',
            'MENOR_IGUAL': 'MENOR_IGUAL',
            'MAS': 'MAS',
            'MENOS': 'MENOS',
            'MULT': 'MULT',
            'DIV': 'DIV',
            'POTENCIA': 'POTENCIA',
            'NEGACION': 'NEGACION',
            '$': '$'  # Añadido para el manejo de fin de entrada
        }

    def _obtener_simbolo_tabla(self, token):
        """Obtiene el símbolo para la tabla basado en el token léxico"""
        token_type = token.getToken()
        simbolo = self._mapeo_tokens.get(token_type)
        if simbolo is None:
            raise Exception(f"Token no reconocido: {token_type}")
        return simbolo

    def analizar(self):
        """Realiza el análisis sintáctico"""
        arbol = []
        tokens = self.tokens.copy()
        
        # Añadir token de fin de entrada con valores por defecto si es necesario
        ultimo_token = tokens[-1] if tokens else None
        linea_fin = getattr(ultimo_token, 'linea', 0) if ultimo_token else 0
        columna_fin = getattr(ultimo_token, 'columna', 0) if ultimo_token else 0
        tokens.append(Valor("$", "$", linea_fin, columna_fin))
        
        while True:
            try:
                # Obtener estado actual de la pila
                if not self.pila:
                    return "Error: Pila vacía", None
                    
                estado_actual = self.pila[-1].getLexema() if hasattr(self.pila[-1], 'getLexema') else "$"
                
                if not tokens:
                    return "Error: No hay más tokens pero el análisis no ha terminado", None
                    
                token_actual = tokens[0]
                
                # Manejo seguro de atributos
                linea_actual = getattr(token_actual, 'linea', 0)
                columna_actual = getattr(token_actual, 'columna', 0)
                
                simbolo_actual = self._obtener_simbolo_tabla(token_actual)

                print(f"Buscando produccion para [{estado_actual}, {simbolo_actual}]")
                
                # Buscar acción en la tabla
                accion = self.tabla.get((estado_actual, simbolo_actual), ("error",))
                
                if accion[0] == "shift":
                    # Acción de desplazamiento
                    _, nuevo_estado = accion
                    token_shift = tokens.pop(0)
                    
                    # Obtener posición del token
                    linea = getattr(token_shift, 'linea', 0)
                    columna = getattr(token_shift, 'columna', 0)
                    
                    # Añadir a la pila con todos los argumentos
                    self.pila.append(token_shift)
                    self.pila.append(Valor("ESTADO", str(nuevo_estado), linea, columna))
                    
                elif accion[0] == "reduce":
                    # Acción de reducción
                    _, num_regla = accion
                    regla = self.reglas.get(num_regla)
                    
                    if regla is None:
                        return f"Error: Regla {num_regla} no encontrada", None
                    
                    # Crear nodo para el árbol
                    nodo = Nodo(num_regla, [], [])
                    
                    # Extraer elementos de la pila
                    elementos_pila = []
                    for _ in range(regla.getLon() * 2):
                        if not self.pila:
                            return "Error: Pila vacía durante reducción", None
                        elem = self.pila.pop()
                        elementos_pila.insert(0, elem)
                    
                    # Procesar elementos
                    for elem in elementos_pila:
                        if hasattr(elem, 'getToken') and elem.getToken() != "ESTADO":
                            nodo.addTerminal(elem)
                    
                    # Añadir nodos no terminales
                    self._agregar_nodos_no_terminales(nodo, arbol, num_regla)
                    
                    # Configurar nodo
                    nodo.setRegla(num_regla)
                    nodo.revTerminales()
                    arbol.append(nodo)
                    
                    # Manejar GOTO
                    if not self.pila:
                        return "Error: Pila vacía después de reducción", None
                    
                    estado_previo = self.pila[-1].getLexema() if hasattr(self.pila[-1], 'getLexema') else "$"
                    no_terminal = regla.getNombre().split('->')[0].strip()
                    
                    # Crear nuevo Valor con todos los argumentos
                    nuevo_valor = Valor(
                        no_terminal, 
                        "NO_TERMINAL", 
                        linea_actual, 
                        columna_actual
                    )
                    
                    self.pila.append(nuevo_valor)
                    
                    # Buscar acción GOTO
                    goto = self.tabla.get((estado_previo, no_terminal), ("error",))
                    
                    if goto[0] != "shift":
                        return f"Error: No se encontró GOTO para {no_terminal}", None
                    
                    _, nuevo_estado_goto = goto
                    self.pila.append(Valor("ESTADO", str(nuevo_estado_goto), linea_actual, columna_actual))
                    
                    # Verificar aceptación
                    if num_regla == 0 and tokens[0].getToken() == "$":
                        return "Análisis exitoso", arbol[0] if arbol else None
                
                else:
                    return self._generar_mensaje_error(token_actual), None
                    
            except Exception as e:
                return f"Error durante el análisis: {str(e)}", None
            
            # Si salimos del bucle por máximo de iteraciones
            return "Error: Análisis sintáctico excedió el máximo de iteraciones", None

    def _agregar_nodos_no_terminales(self, nodo, arbol, num_regla):
        """Agrega nodos no terminales según el tipo de regla"""
        # Reglas que no tienen hijos no terminales
        reglas_sin_hijos = [2, 14, 16, 19, 26, 28, 32, 35, 38, 39, 40, 43, 44, 45, 
                           46, 47, 50, 51, 52, 55, 56, 57, 60, 61, 62, 63, 64, 65, 
                           66, 67, 71]
        
        if num_regla in reglas_sin_hijos:
            return
        
        # Reglas con un hijo no terminal
        reglas_un_hijo = [0, 7, 8, 9, 10, 11, 18, 30, 33, 36, 41, 48, 53, 58, 68]
        
        if num_regla in reglas_un_hijo:
            if not arbol:
                raise Exception(f"Error: No hay nodos no terminales para la regla {num_regla}")
            nodo.addNoTerminal(arbol.pop())
            return
        
        # Reglas con dos hijos no terminales
        reglas_dos_hijos = [1, 13, 25, 29, 31, 34, 37, 42, 49, 54, 59, 69, 70]
        
        if num_regla in reglas_dos_hijos:
            if len(arbol) < 2:
                raise Exception(f"Error: No hay suficientes nodos no terminales para la regla {num_regla}")
            nodo.addNoTerminal(arbol.pop())  # El segundo hijo
            nodo.addNoTerminal(arbol.pop())  # El primer hijo
            nodo.revNoTerminales()  # Revertir para mantener el orden correcto
            return
        
        # Reglas con tres o más hijos no terminales
        if num_regla in [3, 4, 5, 6, 12, 15, 17, 20, 22, 23, 24, 27]:
            # Extraer los hijos en orden inverso y luego revertir
            hijos = []
            cantidad_hijos = 3  # Por defecto
            
            if num_regla in [3, 6, 17, 20, 24]:
                cantidad_hijos = 4
            elif num_regla == 21:
                cantidad_hijos = 5
            
            for _ in range(min(cantidad_hijos, len(arbol))):
                if arbol:
                    hijos.append(arbol.pop())
            
            # Añadir los hijos en orden correcto
            for hijo in reversed(hijos):
                nodo.addNoTerminal(hijo)
            
            return
        
        # Para reglas especiales
        if num_regla == 21:  # para_sentencia
            # Esta regla tiene múltiples elementos
            # Reunir los nodos necesarios
            hijos = []
            for _ in range(min(7, len(arbol))):
                if arbol:
                    hijos.append(arbol.pop())
            
            # Añadir en orden correcto
            for hijo in reversed(hijos):
                nodo.addNoTerminal(hijo)
        
        # Si no se maneja explícitamente, dar un error informativo
        else:
            raise Exception(f"Error: Regla {num_regla} no implementada para agregar nodos no terminales")

    def _generar_mensaje_error(self, token):
        """Genera mensaje de error detallado"""
        error_pos = f"Línea {token.getLinea()}, Columna {token.getColumna()}"
        token_info = f"Token inesperado: '{token.getLexema()}' ({token.getToken()})"
        
        # Sugerencias basadas en el tipo de token
        sugerencias = {
            'PUNTOYCOMA': "¿Falta un ';' al final de la sentencia?",
            'LLAVE_DER': "¿Falta cerrar un bloque con '}'?",
            'LLAVE_IZQ': "¿Falta abrir un bloque con '{'?",
            'PAR_DER': "¿Falta cerrar paréntesis ')'?",
            'PAR_IZQ': "¿Falta abrir paréntesis '('?",
            'IGUAL': "¿Falta una expresión después del '='?",
            'IDENTIFICADOR': "Se esperaba un identificador válido",
            'NUMERO': "Se esperaba un número",
            'CADENA': "Se esperaba una cadena de texto",
            '$': "Error al final del archivo. Posible falta de cierre de alguna estructura"
        }
        
        # Determinar posibles tokens esperados
        tokens_esperados = []
        
        # Estado actual
        if self.pila:
            estado_actual = self.pila[-1].getLexema() if self.pila[-1].getToken() == "ESTADO" else "$"
            
            # Buscar todos los posibles tokens que serían válidos en este estado
            for key in self.tabla:
                if key[0] == estado_actual and self.tabla[key][0] != "error":
                    tokens_esperados.append(key[1])
        
        # Construir mensaje de error
        sugerencia = sugerencias.get(token.getToken(), "Revisa la sintaxis en esta posición")
        mensaje_esperados = ""
        
        if tokens_esperados:
            mensaje_esperados = f" Se esperaba uno de: {', '.join(tokens_esperados)}."
        
        return f"Error sintáctico en {error_pos}. {token_info}.{mensaje_esperados} {sugerencia}"

    def get_regla_name(self, num_regla):
        """Obtiene el nombre de una regla por su número"""
        if num_regla in self.reglas:
            return self.reglas[num_regla].getNombre()
