# Semana 4 — Actividad 2: Serialización y persistencia (JSON)

| | |
|---|---|
| **Núcleo** | Fundamentos de Software — Fundación Universitaria CEIPA |
| **Grupo** | FUNSO_2_N_H |
| **Estudiante** | Deibis Zuluaga Baena |
| **Proyecto** | Quantum Core |
| **Entrega** | 13 de septiembre de 2026 |

---

## El problema

Los objetos viven en la **memoria** de Python: existen mientras el programa corre y desaparecen
cuando termina. Para guardarlos en disco, enviarlos a una base de datos o transmitirlos a otro
sistema hay que convertirlos a un formato de texto universal. Ese formato es **JSON**.

> 🧳 **Analogía.** Serializar es **empacar**: no se puede enviar un armario por correo, así que su
> contenido se mete en una caja plana y etiquetada. Deserializar es **desempacar** al llegar.

---

## Archivos

| Archivo | Tipo | Para qué sirve |
|---------|------|----------------|
| [`serializacion_json.py`](./serializacion_json.py) | Código | Clases, fábrica, serialización, deserialización y persistencia |
| [`transacciones.txt`](./transacciones.txt) | Entrada | **10 transacciones simuladas** de los cuatro tipos |
| [`transacciones.json`](./transacciones.json) | Salida | Lo genera el programa en cada ejecución. **No se escribe a mano** |
| [`README.md`](./README.md) | Documento | Esta documentación |

### El recorrido completo

```text
transacciones.txt   →   objetos Python   →   transacciones.json
   (texto plano)          (en memoria)          (texto JSON)
```

> 💡 Los datos **no están escritos dentro del programa**. Para cambiarlos se edita el `.txt`, sin
> tocar una sola línea de código.

---

## Paso 1 — Fundamentos de la serialización

### Por qué la conversión es obligatoria

Un intento de guardar el objeto directamente falla:

```python
json.dumps(transaccion)
```

```text
TypeError: Object of type TransaccionCredito is not JSON serializable
```

JSON solo entiende **textos, números, listas y diccionarios**. Una clase creada dentro del proyecto
no está en esa lista.

> ⚠️ Por eso existe una **escala intermedia obligatoria**: el objeto se traduce primero a un
> diccionario, y ese diccionario sí lo sabe convertir el módulo `json`.

### El viaje completo, en dos escalas

| Sentido | Recorrido | Herramienta |
|---------|-----------|-------------|
| **Serializar** | Objeto → Diccionario → Texto JSON | `json.dumps()` |
| **Deserializar** | Texto JSON → Diccionario → Objeto | `json.loads()` + constructor |

> ⚠️ **Detalle que se pregunta en el quiz.** `json.dumps()` **no** devuelve un diccionario: devuelve
> un `str`. Y `json.loads()` **no** devuelve un objeto: devuelve un diccionario. El último tramo
> hasta el objeto es siempre manual. La `s` de `dumps` y `loads` es de *string*, no es plural.

### Por qué JSON y no un texto plano cualquiera

Los dos son texto. La diferencia está en lo que cada formato **conserva**.

| Aspecto | Texto plano `C001,CREDITO,500000` | JSON |
|---------|-----------------------------------|------|
| **Tipos de dato** | Todo vuelve como texto: `'500000'` es `str` | El número vuelve como número |
| **Significado** | Hay que saber que el tercer campo es el monto | El nombre viaja pegado al valor |
| **Errores de formato** | Una columna faltante pasa inadvertida | Lanza `JSONDecodeError` con línea y columna |
| **Estructura** | Plano: una fila de campos sueltos | Admite objetos anidados y listas |
| **Compatibilidad** | Exige escribir un lector propio en cada sistema | `json.loads()` está en casi todos los lenguajes |

> 💡 **La consecuencia concreta.** Como el texto plano devuelve el monto en forma de cadena, hay que
> convertirlo a mano con `float()`, y **esa conversión es exactamente la que produjo los
> `ValueError` de la Actividad 1** al encontrarse con `texto_invalido`.

---

## Paso 2 — Objeto → JSON y viceversa

### Serialización

```python
def objeto_a_diccionario(transaccion):
    """Paso 1: copia los atributos del objeto a un diccionario simple."""
    return {
        "cliente_id": transaccion.cliente_id,
        "tipo": transaccion.tipo,
        "monto": transaccion.monto,
    }


def objeto_a_json(transaccion):
    """Paso 2: convierte el diccionario en una cadena de texto JSON."""
    como_dict = objeto_a_diccionario(transaccion)
    return json.dumps(como_dict)
```

> 💡 Las dos etapas se dejaron en **funciones separadas** a propósito. Podrían ser una sola, pero
> entonces la escala intermedia quedaría escondida dentro de la llamada, y es justo la etapa que
> explica por qué el proceso necesita dos pasos y no uno.

### Deserialización

```python
def json_a_objeto(texto_json):
    """Camino inverso: del texto al diccionario, y del diccionario al objeto."""
    como_dict = json.loads(texto_json)
    return diccionario_a_objeto(como_dict)
```

`json.loads()` solo llega hasta el diccionario. El último tramo es manual: con sus claves se llama
al constructor, y ahí vuelven los métodos.

### Salida esperada

```text
1) Objeto original : Transaccion [CREDITO ] - ID: C001 | Monto: $  500,000.00
   Clase de Python : TransaccionCredito
   Impacto         : $10,000.00

2) Diccionario     : {'cliente_id': 'C001', 'tipo': 'CREDITO', 'monto': 500000.0}
   Tipo de dato    : dict

3) Texto JSON      : {"cliente_id": "C001", "tipo": "CREDITO", "monto": 500000.0}
   Tipo de dato    : str (ya puede viajar o guardarse)

4) Objeto reconstruido : Transaccion [CREDITO ] - ID: C001 | Monto: $  500,000.00
   Clase de Python     : TransaccionCredito
   Impacto             : $10,000.00 (el metodo volvio)
```

---

## Qué se pierde y qué se recupera

| Qué pasa | Explicación |
|----------|-------------|
| **Se pierden los métodos** | En el JSON solo quedan los datos. `calcular_impacto()` no aparece. Vuelve al llamar al constructor |
| **No viaja la clase** | El JSON no guarda que era un `TransaccionCredito`. Solo viaja `"tipo": "CREDITO"` |
| **No es el mismo objeto** | Es una copia nueva con los mismos datos, en otra dirección de memoria |

> 💡 **La clase no se transporta: se reconstruye.** Es la fábrica `crear_transaccion()` la que lee
> el texto `"CREDITO"` en el destino y decide qué clase construir. Por eso la deserialización pasa
> por la fábrica y no por un constructor fijo.

---

## Persistencia

**Persistir significa permanecer.** Los datos persistentes siguen existiendo después de que el
programa termina.

| | Memoria (RAM) | Disco |
|---|---|---|
| **Cuánto dura** | Hasta que cierras el programa | Hasta que lo borres |
| **Se llama** | Volátil | **Persistente** |

```python
with open(nombre_archivo, "w", encoding="utf-8") as archivo:
    json.dump(lista_de_diccionarios, archivo, indent=2, ensure_ascii=False)
```

> ⚠️ Para archivos se usan `json.dump()` y `json.load()`, **sin la `s` final**. Las versiones con
> `s` trabajan con texto en memoria; estas dos leen y escriben el archivo directamente.

### El archivo generado

```json
[
  {
    "cliente_id": "C001",
    "tipo": "CREDITO",
    "monto": 500000.0
  },
  ...
]
```

> 💡 **Serializar y persistir no son lo mismo.** La serialización es la *técnica* —traducir el
> objeto a texto—; la persistencia es el *resultado* —que ese texto quede guardado—. Se puede
> serializar sin persistir (un JSON que viaja por internet y nadie guarda), pero **no se puede
> persistir sin serializar**, porque un disco no almacena objetos de Python, solo texto.

---

## Manejo de casos de error

La estrategia es la misma de la Actividad 1: **detectar el fallo, dejar constancia y continuar**.

| Origen del fallo | Excepción | Dónde se detecta |
|------------------|-----------|------------------|
| Serializar un objeto con un dato no convertible | `TypeError` | `objeto_a_json()` |
| Texto JSON mal formado | `JSONDecodeError` | `json_a_objeto()` |
| Falta una clave en el registro | `ValueError` | `diccionario_a_objeto()` |
| Tipo de transacción desconocido | `ValueError` | `crear_transaccion()` |
| Monto no numérico o negativo | `ValueError` | *setter* de `TransaccionBase` |
| El archivo `.json` no existe | `FileNotFoundError` | `cargar_transacciones()` |
| No se puede escribir el archivo | `OSError` | `guardar_transacciones()` |

### Tres decisiones de diseño

| Decisión | Por qué |
|----------|---------|
| **Traducir el error técnico a uno del dominio** | Un `JSONDecodeError` describe lo que le pasó al módulo `json`, no a los datos. El mensaje útil es `"al registro le faltan las claves: monto"` |
| **Validar las claves antes de usarlas** | En vez de un `KeyError` seco, se revisan todas y se nombran juntas. Un solo mensaje resuelve el problema completo |
| **No tratar todos los fallos igual** | Los de un registro se aíslan y la carga sigue. Los que impiden continuar (archivo inexistente) sí detienen el proceso |

### Salida esperada

```text
--- Manejo de casos de error ---

   JSON mal formado       -> ValueError: el texto recibido no es un JSON valido: ...
   Falta la clave monto   -> ValueError: al registro le faltan las claves: monto
   Tipo desconocido       -> ValueError: tipo de transaccion desconocido: BONO
   Monto no numerico      -> ValueError: could not convert string to float: 'mil'
   Monto negativo         -> ValueError: el monto no puede ser negativo
   Archivo inexistente    -> FileNotFoundError: no existe el archivo ...
```

> ⚠️ El monto se valida en el *setter* de `TransaccionBase`, conservando el **encapsulamiento de la
> Semana 3**. Gracias a eso, un JSON con un monto de texto o negativo se rechaza al reconstruir el
> objeto, y no más adelante cuando ya contaminó un cálculo.

---

## Cómo ejecutar

```bash
python3 serializacion_json.py
```

El programa lee `transacciones.txt`, muestra el viaje de ida y vuelta de una `TransaccionCredito`,
guarda las 10 transacciones en `transacciones.json`, las vuelve a leer y comprueba el manejo de
los seis casos de error.

---

## Conclusiones

| Idea | En una frase |
|------|--------------|
| **El puente** | La serialización une dos mundos que no se entienden: el de los objetos, que solo existe mientras el programa corre, y el del disco y las redes, que solo transporta texto |
| **La elección de JSON** | Se eligió por razones medibles: conserva tipos, explica el significado, avisa cuando está mal formado y lo entiende cualquier sistema |
| **La asimetría** | Convertir un objeto en texto es directo; reconstruirlo exige que el destino conozca la clase. El texto lleva los datos, el comportamiento lo pone quien recibe |
| **Los errores** | Un dato que viene de un archivo o de otro sistema es, por definición, un dato en el que no se puede confiar |
