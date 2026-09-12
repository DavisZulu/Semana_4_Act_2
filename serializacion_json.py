"""
serializacion_json.py
Semana 4 - Actividad 2: Serializacion y persistencia (JSON).

EL PROBLEMA QUE SE RESUELVE
---------------------------
Los objetos viven en la MEMORIA de Python: existen mientras el programa corre y
desaparecen cuando termina. Para guardarlos en un disco, meterlos en una base de
datos o enviarlos por internet hay que convertirlos a un formato de texto que
cualquier sistema entienda. Ese formato universal es JSON.

LA ANALOGIA DEL VIAJE
---------------------
Serializar es EMPACAR: no se puede enviar un armario por correo, asi que su
contenido se mete en una caja plana y etiquetada. El objeto se vuelve texto, y
el texto si cabe en un archivo o en una peticion HTTP.
Deserializar es DESEMPACAR al llegar: se abre la caja y se vuelve a armar el
objeto, con todo su comportamiento.

EL VIAJE COMPLETO, EN DOS ESCALAS
---------------------------------
    Objeto Python  ->  Diccionario  ->  Texto JSON      (serializar)
    Texto JSON     ->  Diccionario  ->  Objeto Python   (deserializar)

La escala del medio, el DICCIONARIO, no es opcional: el modulo json no sabe
traducir un objeto de una clase propia del proyecto, pero si sabe traducir un
diccionario. Por eso primero se pasa por ahi.

QUE SE PIERDE Y QUE SE RECUPERA
-------------------------------
Al serializar se pierden los METODOS: el JSON guarda unicamente los DATOS
(cliente_id, tipo, monto). Al deserializar los metodos vuelven, porque se los
devuelve la clase en el momento de llamar al constructor. El objeto que resulta
no es el original: es una copia nueva con los mismos datos.

El JSON tampoco guarda A QUE CLASE pertenecia el objeto. Lo unico que viaja es
el dato "tipo". Es la fabrica crear_transaccion() la que lee ese texto en el
destino y decide si construye un TransaccionCredito, un TransaccionDebito, un
TransaccionEfectivo o un TransaccionCripto.

MANEJO DE ERRORES
-----------------
Traducir datos entre dos mundos es donde mas cosas pueden fallar, asi que el
proceso no se deja desprotegido. La estrategia es la misma de la Actividad 1:
detectar el fallo, dejar constancia y seguir con el registro siguiente.

    Origen del fallo                        Excepcion
    ----------------------------------------------------------------
    Serializar un objeto directamente       TypeError
    Texto JSON mal formado                  json.JSONDecodeError
    Falta una clave en el registro          se valida y se lanza ValueError
    Tipo de transaccion desconocido         ValueError (lo lanza la fabrica)
    Monto que no es un numero               ValueError (lo lanza el setter)
    Monto negativo                          ValueError (lo lanza el setter)
    El archivo de entrada no existe         FileNotFoundError

Las funciones traducen los fallos tecnicos a un ValueError con un mensaje del
dominio ("al registro le faltan las claves: monto"), porque quien llama necesita
saber QUE dato esta mal, no en que linea del modulo json ocurrio. Los fallos de
un registro se aislan; los que impiden continuar, como un archivo inexistente,
si detienen el proceso, porque ahi no hay nada que recuperar.

DETALLE QUE SE PREGUNTA EN EL QUIZ
----------------------------------
json.dumps() NO devuelve un diccionario: devuelve un str. Y json.loads() NO
devuelve un objeto: devuelve un diccionario. El ultimo tramo hasta el objeto es
siempre manual. La "s" de dumps y loads es de string, no es un plural; las
versiones sin "s", json.dump() y json.load(), trabajan directamente con archivos.

ARCHIVOS Y EJECUCION
--------------------
    Archivo de entrada        : transacciones.txt   (10 transacciones simuladas
                                de los cuatro tipos, en formato cliente_id,tipo,monto)
    Archivo que se genera     : transacciones.json  (las mismas 10, serializadas)
    Objeto de la demostracion : TransaccionCredito C001, como pide el enunciado.
    Ejecucion                 : python3 serializacion_json.py
"""

import json


ARCHIVO_TXT = "transacciones.txt"     # datos de entrada
ARCHIVO_JSON = "transacciones.json"    # archivo que genera el programa


# ============================================================================
# 1. LAS CLASES (jerarquia heredada de la Semana 3)
# ============================================================================
class TransaccionBase:
    """Estructura comun de todas las transacciones."""

    def __init__(self, cliente_id, tipo, monto):
        self.cliente_id = cliente_id
        self.tipo = tipo
        self.monto = monto          # pasa por el setter, que valida

    # El monto conserva el encapsulamiento de la Semana 3: el valor real vive en
    # _monto y solo entra al objeto si supera la validacion del setter. Gracias a
    # esto, un JSON con un monto de texto o negativo se rechaza al reconstruir el
    # objeto, no despues.
    @property
    def monto(self):
        """Devuelve el monto protegido de la transaccion."""
        return self._monto

    @monto.setter
    def monto(self, nuevo_monto):
        """Valida y almacena el monto. Lanza ValueError si el dato no sirve."""
        # float() lanza ValueError si el dato es un texto no numerico.
        nuevo_monto = float(nuevo_monto)

        if nuevo_monto < 0:
            raise ValueError("el monto no puede ser negativo")

        self._monto = nuevo_monto

    def calcular_impacto(self):
        """Cada clase hija define su formula. Este metodo NO viaja en el JSON."""
        raise NotImplementedError("Cada tipo debe calcular su propio impacto.")

    def __str__(self):
        return (f"Transaccion [{self.tipo:<8}] - ID: {self.cliente_id} | "
                f"Monto: ${self.monto:>12,.2f}")


class TransaccionCredito(TransaccionBase):
    """Credito: impacto del 2 % del monto."""

    def calcular_impacto(self):
        return self.monto * 0.02


class TransaccionDebito(TransaccionBase):
    """Debito: comision fija de 1.500."""

    def calcular_impacto(self):
        return 1500


class TransaccionEfectivo(TransaccionBase):
    """Efectivo: impacto del 1 % del monto."""

    def calcular_impacto(self):
        return self.monto * 0.01


class TransaccionCripto(TransaccionBase):
    """Cripto: impacto del 3 % del monto."""

    def calcular_impacto(self):
        return self.monto * 0.03


def crear_transaccion(cliente_id, tipo, monto):
    """
    Devuelve el objeto especializado segun el tipo recibido.

    Es la pieza clave al deserializar: el JSON guarda el dato "tipo", pero no
    guarda a que clase de Python pertenecia el objeto. Esta fabrica traduce ese
    texto de vuelta a la clase correcta.
    """
    tipo = tipo.upper()

    if tipo == "CREDITO":
        return TransaccionCredito(cliente_id, tipo, monto)
    elif tipo == "DEBITO":
        return TransaccionDebito(cliente_id, tipo, monto)
    elif tipo == "EFECTIVO":
        return TransaccionEfectivo(cliente_id, tipo, monto)
    elif tipo == "CRIPTO":
        return TransaccionCripto(cliente_id, tipo, monto)
    else:
        raise ValueError(f"tipo de transaccion desconocido: {tipo}")


# ============================================================================
# 2. SERIALIZACION:  Objeto -> Diccionario -> Texto JSON
# ============================================================================
def objeto_a_diccionario(transaccion):
    """Paso 1: copia los atributos del objeto a un diccionario simple."""
    return {
        "cliente_id": transaccion.cliente_id,
        "tipo": transaccion.tipo,
        "monto": transaccion.monto,
    }


def objeto_a_json(transaccion):
    """
    Paso 2: convierte el diccionario en una cadena de texto JSON.

    El try protege contra el caso en que algun atributo no sea convertible a
    JSON. Ocurre, por ejemplo, si un monto se guardara como un objeto Decimal o
    como una fecha en vez de un numero.
    """
    como_dict = objeto_a_diccionario(transaccion)

    try:
        # json.dumps() no devuelve un diccionario: devuelve un str.
        return json.dumps(como_dict)

    except TypeError as error:
        raise TypeError(
            f"la transaccion {transaccion.cliente_id} contiene un dato que no "
            f"se puede convertir a JSON: {error}"
        ) from error


# ============================================================================
# 3. DESERIALIZACION:  Texto JSON -> Diccionario -> Objeto
# ============================================================================
CLAVES_OBLIGATORIAS = ("cliente_id", "tipo", "monto")


def diccionario_a_objeto(como_dict):
    """
    Reconstruye el objeto a partir del diccionario, validando antes sus claves.

    Se revisan las claves en lugar de dejar que Python lance un KeyError seco.
    Un KeyError solo dice 'monto'; este mensaje dice que registro venia
    incompleto y que le falta, que es lo que necesita quien corrige los datos.
    """
    faltantes = [clave for clave in CLAVES_OBLIGATORIAS if clave not in como_dict]

    if faltantes:
        raise ValueError(f"al registro le faltan las claves: {', '.join(faltantes)}")

    # La fabrica lanza ValueError si el tipo no existe, y el constructor lo
    # lanza si el monto no es un numero. Ambos suben tal cual a quien llama.
    return crear_transaccion(
        como_dict["cliente_id"],
        como_dict["tipo"],
        como_dict["monto"],
    )


def json_a_objeto(texto_json):
    """
    Camino inverso: del texto al diccionario, y del diccionario al objeto.

    Un texto mal formado hace fallar a json.loads() con JSONDecodeError. Ese
    error se traduce a ValueError para que quien llame maneje un solo tipo de
    fallo de datos, sin tener que conocer el detalle interno del modulo json.
    """
    # Paso 1: json.loads() solo llega hasta el diccionario.
    try:
        como_dict = json.loads(texto_json)

    except json.JSONDecodeError as error:
        raise ValueError(f"el texto recibido no es un JSON valido: {error}") from error

    # Paso 2: con sus claves se llama al constructor. Ahi vuelven los metodos.
    return diccionario_a_objeto(como_dict)


# ============================================================================
# 4. PERSISTENCIA: del texto en memoria al archivo en disco
# ============================================================================
# json.dumps() y json.loads() trabajan con texto. Sus versiones sin la "s",
# json.dump() y json.load(), hacen la misma traduccion y ademas leen o escriben
# directamente el archivo.
def guardar_transacciones(lista_transacciones, nombre_archivo):
    """
    Serializa la lista completa de objetos y la escribe en un archivo .json.

    Un fallo de escritura (permisos, disco lleno, ruta inexistente) llega como
    OSError y se reporta con el nombre del archivo, que es el dato util.
    """
    lista_de_diccionarios = [objeto_a_diccionario(t) for t in lista_transacciones]

    try:
        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            json.dump(lista_de_diccionarios, archivo, indent=2, ensure_ascii=False)

    except OSError as error:
        raise OSError(f"no se pudo escribir {nombre_archivo}: {error}") from error

    return len(lista_de_diccionarios)


def cargar_transacciones(nombre_archivo):
    """
    Lee el archivo .json y reconstruye la lista de objetos con sus metodos.

    Se distinguen dos clases de fallo, y se tratan distinto a proposito:

      - Los que impiden continuar (el archivo no existe, o su contenido no es
        JSON) detienen la carga, porque no hay nada que recuperar.
      - Los de un registro suelto (le falta una clave, el tipo no existe, el
        monto no es numero) se aislan: se deja constancia y se sigue con el
        siguiente, igual que en la Actividad 1.
    """
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            lista_de_diccionarios = json.load(archivo)

    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"no existe el archivo {nombre_archivo}; se genera al ejecutar "
            f"guardar_transacciones()"
        ) from error

    except json.JSONDecodeError as error:
        raise ValueError(
            f"{nombre_archivo} existe pero su contenido no es un JSON valido: {error}"
        ) from error

    transacciones = []

    for numero, registro in enumerate(lista_de_diccionarios, start=1):
        try:
            transacciones.append(diccionario_a_objeto(registro))

        except ValueError as error:
            print(f"   [Registro {numero}] descartado -> {error}")

    return transacciones


# ============================================================================
# 5. LECTURA DE LOS DATOS DE ENTRADA
# ============================================================================
def leer_transacciones(nombre_archivo):
    """
    Lee el archivo de texto y crea un objeto por cada linea.

    Los datos no van escritos dentro del programa: viven en transacciones.txt,
    con el mismo formato cliente_id,tipo,monto de las semanas anteriores. Asi se
    pueden cambiar los datos sin tocar una sola linea de codigo.
    """
    transacciones = []

    with open(nombre_archivo, "r", encoding="utf-8") as archivo:
        for numero_linea, linea in enumerate(archivo, start=1):
            linea = linea.strip()

            if not linea:
                continue

            try:
                cliente_id, tipo, monto = [dato.strip() for dato in linea.split(",")]
                transacciones.append(crear_transaccion(cliente_id, tipo, float(monto)))

            # Un ValueError cubre los tres fallos posibles de esta linea: que no
            # traiga tres columnas, que el monto no sea numero, o que el tipo no
            # exista. El registro se descarta y la lectura continua.
            except ValueError as error:
                print(f"   [Linea {numero_linea}] descartada -> {error}")

    return transacciones


# ============================================================================
# 6. DEMOSTRACION
# ============================================================================
def demostrar_manejo_de_errores():
    """
    Comprueba que cada fallo previsto se detecta y se reporta con claridad.

    Se alimentan a proposito cinco entradas defectuosas. En los cinco casos el
    programa informa que dato esta mal y continua: ninguna detiene la ejecucion.
    """
    print("\n--- Manejo de casos de error ---\n")

    casos = [
        ("JSON mal formado", '{"cliente_id": "C001", "tipo": "CREDITO",}'),
        ("Falta la clave monto", '{"cliente_id": "C001", "tipo": "CREDITO"}'),
        ("Tipo desconocido", '{"cliente_id": "C001", "tipo": "BONO", "monto": 1000}'),
        ("Monto no numerico", '{"cliente_id": "C001", "tipo": "CREDITO", "monto": "mil"}'),
        ("Monto negativo", '{"cliente_id": "C001", "tipo": "CREDITO", "monto": -5000}'),
    ]

    for descripcion, texto in casos:
        try:
            json_a_objeto(texto)
            print(f"   {descripcion:<22} -> no se detecto el fallo")

        except ValueError as error:
            print(f"   {descripcion:<22} -> ValueError: {error}")

    # Caso aparte: el fallo no es de un registro sino del archivo completo.
    try:
        cargar_transacciones("archivo_que_no_existe.json")

    except FileNotFoundError as error:
        print(f"   {'Archivo inexistente':<22} -> FileNotFoundError: {error}")


def ejecutar():
    transacciones = leer_transacciones(ARCHIVO_TXT)
    print(f"Se leyeron {len(transacciones)} transacciones desde {ARCHIVO_TXT}\n")

    # El enunciado pide demostrar el proceso con un objeto TransaccionCredito.
    original = transacciones[0]

    print("--- Viaje de ida y vuelta de una transaccion ---\n")

    print("1) Objeto original :", original)
    print("   Clase de Python :", type(original).__name__)
    print(f"   Impacto         : ${original.calcular_impacto():,.2f}")

    como_dict = objeto_a_diccionario(original)
    print("\n2) Diccionario     :", como_dict)
    print("   Tipo de dato    :", type(como_dict).__name__)

    texto = objeto_a_json(original)
    print("\n3) Texto JSON      :", texto)
    print("   Tipo de dato    :", type(texto).__name__, "(ya puede viajar o guardarse)")

    reconstruido = json_a_objeto(texto)
    print("\n4) Objeto reconstruido :", reconstruido)
    print("   Clase de Python     :", type(reconstruido).__name__)
    print(f"   Impacto             : ${reconstruido.calcular_impacto():,.2f} (el metodo volvio)")

    print("\n--- Persistencia en disco ---\n")

    cantidad = guardar_transacciones(transacciones, ARCHIVO_JSON)
    print(f"Se guardaron {cantidad} transacciones en {ARCHIVO_JSON}")

    recuperadas = cargar_transacciones(ARCHIVO_JSON)
    print(f"Se leyeron   {len(recuperadas)} transacciones desde {ARCHIVO_JSON}\n")

    for t in recuperadas:
        print(f"   {t} | {type(t).__name__:<20} | Impacto: ${t.calcular_impacto():>10,.2f}")

    demostrar_manejo_de_errores()


if __name__ == "__main__":
    ejecutar()
