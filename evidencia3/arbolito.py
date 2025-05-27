import csv
import time
import sys
import io

# Configuración universal de codificación
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class Node:
    def __init__(self, symbol, children=None, token=None):
        """
        Clase para representar nodos del árbol sintáctico.
        
        Args:
            symbol (str): Símbolo gramatical (terminal o no terminal)
            children (list[Node], optional): Nodos hijos. Defaults to None.
            token (str, optional): Token asociado si es terminal. Defaults to None.
        """
        self.symbol = symbol
        self.children = children if children is not None else []
        self.token = token  # Solo para nodos terminales
        self.id = id(self)  # Identificador único para graphviz
    
    def add_child(self, child_node):
        """Añade un nodo hijo"""
        self.children.append(child_node)
    
    def __repr__(self):
        return f"{self.symbol} ({self.token})" if self.token else self.symbol

class AnalizadorSintacticoLL:
    def __init__(self, archivo_tabla):
        self.tabla = self.cargar_tabla_csv(archivo_tabla)
        self.raiz = None  # Raíz del árbol sintáctico
    
    def cargar_tabla_csv(self, archivo):
        tabla = {}
        with open(archivo, newline='', encoding='utf-8') as csvfile:
            reader = list(csv.reader(csvfile, delimiter=','))
            terminales = reader[0][1:]  # Saltar la primera columna vacía
            for fila in reader[1:]:
                no_terminal = fila[0]
                for i, celda in enumerate(fila[1:]):
                    produccion = celda.strip()
                    if produccion:  # Solo agregamos si hay producción
                        lado_derecho = produccion.split() if produccion != 'ε' else ['ε']
                        tabla[(no_terminal, terminales[i])] = lado_derecho
        return tabla

    def mostrar_pila(self, pila):
        """Función para mostrar la pila de manera gráfica (versión compatible)"""
        print("\nEstado actual de la pila:")
        print("+---------------------------------+")
        for elemento in reversed(pila):
            print(f"| {elemento.center(31)} |")
            print("+---------------------------------+")

    def generar_codigo_graphviz(self):
        """
        Genera código DOT para visualizar en Graphviz Online.
        Devuelve una cadena con el código DOT.
        """
        dot = []
        dot.append("digraph G {")
        dot.append('  rankdir="TB";')  # Top to Bottom
        dot.append('  node [shape=ellipse, fontname="Courier", fontsize=12];')
        dot.append('  edge [fontname="Courier", fontsize=10];')
        
        # Función recursiva para agregar nodos
        def agregar_nodos(node):
            if node.token:
                # Nodo terminal (mostramos el token)
                dot.append(f'  {node.id} [label="{node.symbol}\\n[{node.token}]", shape=box, style=filled, fillcolor="#e6f3ff"];')
            else:
                # Nodo no terminal
                dot.append(f'  {node.id} [label="{node.symbol}"];')
            
            for child in node.children:
                agregar_nodos(child)
                dot.append(f'  {node.id} -> {child.id};')
        
        if self.raiz:
            agregar_nodos(self.raiz)
            dot.append("}")
            return "\n".join(dot)
        else:
            return "// No se pudo generar el árbol: análisis no exitoso"

    def analizar(self, tokens):
        """
        Analiza una lista de tokens utilizando el algoritmo LL y construye el árbol sintáctico.
        """
        # Agregar el símbolo de fin de entrada
        tokens.append('$')
        
        # Inicializar pila y puntero de entrada
        pila = ['$', 'PROGRAMA']  # Comenzamos con el símbolo inicial PROGRAMA y el marcador de fondo $
        indice = 0
        token_actual = tokens[indice]
        
        # Estructuras para construir el árbol
        stack_arbol = []  # Pila para construcción del árbol
        self.raiz = Node('PROGRAMA')  # Nodo raíz inicial
        stack_arbol.append(self.raiz)
        
        print("\n INICIANDO ANALISIS")
        print(" Nuestra pila siempre empezará ['$', 'PROGRAMA']):")
        self.mostrar_pila(pila)
        print(f"• Primer token a procesar: '{token_actual}'")
        time.sleep(1)
        
        pasos = []
        paso_num = 1
        
        while pila[-1] != '$':
            X = pila[-1]
            nodo_actual = stack_arbol[-1] if stack_arbol else None
            
            print(f"\n >>> PASO {paso_num} <<<")
            print(f"Tope de Pila: '{X}'")
            print(f"Token actual de Entrada: '{token_actual}'")
            
            entrada_restante = ' '.join(tokens[indice:])
            pila_actual = ' '.join(pila)
            accion = ""
            
            if X == token_actual:
                accion = f"Emparejar {X}"
                print(f"\n ¡COINCIDENCIA! El tope '{X}' coincide con el token actual")
                print(f"• Solucion: Sacar '{X}' de la pila y avanzar al siguiente token")
                
                # Para nodos terminales, guardamos el token
                if nodo_actual:
                    nodo_actual.token = token_actual
                
                pila.pop()
                stack_arbol.pop()
                indice += 1
                if indice < len(tokens):
                    token_actual = tokens[indice]
                
                self.mostrar_pila(pila)
                print(f"• Nuevo token: '{token_actual}'")
                time.sleep(1)
                
            elif (X, token_actual) in self.tabla:
                produccion = self.tabla[(X, token_actual)]
                produccion_str = ' -> '.join(produccion) if produccion != ['ε'] else 'ε'
                accion = f"{X} -> {produccion_str}"
                print(f"\n EXPANSIÓN Aplicando regla gramatical: {accion}")
                print(f"• Sacamos '{X}' de la pila y agregamos la producción")
                
                pila.pop()
                nodo_padre = stack_arbol.pop()
                
                # Procesar la producción (de derecha a izquierda para la pila)
                for simbolo in reversed(produccion):
                    if simbolo != 'ε':
                        pila.append(simbolo)
                        nuevo_nodo = Node(simbolo)
                        nodo_padre.add_child(nuevo_nodo)
                        stack_arbol.append(nuevo_nodo)
                        print(f"  - Agregando '{simbolo}' a la pila")
                
                self.mostrar_pila(pila)
                print(f"• Token actual se mantiene: '{token_actual}' (no avanzamos)")
                time.sleep(1)
                
            else:
                print(f"\n ¡ERROR! ¡No existe regla en la tabla para ({X}, {token_actual})!")
                print("Posibles causas:")
                print(f"- Falta una producción para '{X}' con el token '{token_actual}'")
                print(f"- Token inesperado en la posición {indice}")
                print(f"- Error en la gramática (revisar tabla sintáctica)")
                pasos.append((paso_num, pila_actual, entrada_restante, "ERROR: No hay regla definida"))
                return {
                    "CONCLUSION": "ERROR SINTACTICO :(",
                    "mensaje": f"Error sintáctico en el token '{token_actual}' (posición {indice}). No hay regla definida para el no terminal '{X}'.",
                    "pasos": pasos,
                    "arbol": None,
                    "graphviz_code": None
                }
            
            pasos.append((paso_num, pila_actual, entrada_restante, accion))
            paso_num += 1
        
        if token_actual == '$':
            print("\n <<< PILA VACIA >>> ")
            print("¡Proceso completado exitosamente!")
            print("La pila solo contiene '$' (se vació correctamente)")
            print("Todos los tokens fueron procesados")
            print("CONCLUSIÓN: La cadena es válida según la gramática")
            entrada_restante = ' '.join(tokens[indice:])
            pila_actual = ' '.join(pila)
            pasos.append((paso_num, pila_actual, entrada_restante, "ACEPTAR"))
            
            # Limpiar nodos vacíos (producciones epsilon)
            self.limpiar_nodos_epsilon(self.raiz)
            
            # Generar código Graphviz
            graphviz_code = self.generar_codigo_graphviz()
            
            return {
                "CONCLUSION": "ACEPTADO :)",
                "mensaje": "¡Esta cadena si pertenece a tu gramatica!",
                "pasos": pasos,
                "arbol": self.raiz,
                "graphviz_code": graphviz_code
            }
        else:
            print("\n <<< FALLO >>>")
            print("¡Proceso terminado con errores!")
            print(f" Token pendiente sin procesar: '{token_actual}'")
            print(" La pila se vació pero quedaron tokens sin consumir")
            entrada_restante = ' '.join(tokens[indice:])
            pila_actual = ' '.join(pila)
            pasos.append((paso_num, pila_actual, entrada_restante, "ERROR: Entrada no consumida"))
            
            return {
                "CONCLUSION": "ERROR SINTACTICO :(",
                "mensaje": f"Entrada no consumida completamente. Token actual: '{token_actual}'",
                "pasos": pasos,
                "arbol": None,
                "graphviz_code": None
            }
    
    def limpiar_nodos_epsilon(self, node):
        """Elimina nodos epsilon (producciones vacías) del árbol"""
        if not node:
            return
        
        # Procesar hijos recursivamente
        for child in node.children[:]:
            if child.symbol == 'ε':
                node.children.remove(child)
            else:
                self.limpiar_nodos_epsilon(child)

def imprimir_tabla(datos, titulos, anchos):
    def formatear_celda(texto, ancho):
        texto = str(texto)
        if len(texto) > ancho:
            return texto[:ancho-3] + "..."
        return texto.ljust(ancho)
    
    separador = "+" + "+".join(["-" * (ancho + 2) for ancho in anchos]) + "+"
    
    print(separador)
    header = "|"
    for titulo, ancho in zip(titulos, anchos):
        header += " " + formatear_celda(titulo, ancho) + " |"
    print(header)
    print(separador)
    
    for fila in datos:
        linea = "|"
        for valor, ancho in zip(fila, anchos):
            # Reemplazar caracteres Unicode problemáticos
            valor_str = str(valor).replace('→', '->').replace('ε', 'epsilon')
            linea += " " + formatear_celda(valor_str, ancho) + " |"
        print(linea)
    
    print(separador)

def analizar_cadena(cadena):
    """
    Analiza una cadena de tokens separados por espacios.
    """
    tokens = cadena.strip().split()
    analizador = AnalizadorSintacticoLL("tabla_ll1.csv")
    resultado = analizador.analizar(tokens)
    
    print("\n <<< RESUMEN DEL ANÁLISIS >>>")
    print(f"ENTRADA: {cadena}")
    print(f"CONCLUSION: {resultado['CONCLUSION']}")
    print(f"SALIDA: {resultado['mensaje']}")
    
    if resultado['graphviz_code']:
        print("\n=== CÓDIGO GRAPHVIZ PARA VISUALIZACIÓN ONLINE ===")
        print(resultado['graphviz_code'])
        print("\nInstrucciones:")
        print("1. Copia todo el código DOT mostrado arriba")
        print("2. Ve a https://dreampuf.github.io/GraphvizOnline/")
        print("3. Pega el código en el área de texto")
        print("4. Verás tu árbol sintáctico generado automáticamente")
    
    return resultado

def leer_cadena_desde_archivo(nombre_archivo):
    """
    Lee una cadena de tokens desde un archivo de texto.
    
    Args:
        nombre_archivo (str): Ruta del archivo a leer
        
    Returns:
        str: Cadena de tokens leída del archivo
    """
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            return archivo.read().strip()
    except FileNotFoundError:
        print(f"\nERROR: No se encontró el archivo '{nombre_archivo}'")
        return None
    except Exception as e:
        print(f"\nERROR al leer el archivo: {str(e)}")
        return None

if __name__ == "__main__":
    # Nombre del archivo que contiene los tokens
    archivo_entrada = "entrada.txt"
    
    # Leer la cadena desde el archivo
    cadena = leer_cadena_desde_archivo(archivo_entrada)
    
    if cadena is not None:
        print(f"\nAnalizando cadena desde el archivo '{archivo_entrada}':")
        print(f"Contenido: {cadena}\n")
        
        # Realizar el análisis
        resultado = analizar_cadena(cadena)
        
        # Mostrar resultados adicionales si es necesario
        if resultado['CONCLUSION'] == "ACEPTADO :)":
            print("\nAnálisis completado con éxito!")
        else:
            print("\nSe encontraron errores durante el análisis.")
