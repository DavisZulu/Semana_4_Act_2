# Semana 4 — Actividad 2: Serialización y persistencia (JSON)

Los objetos viven en la **memoria** de Python: existen mientras el programa corre y desaparecen
cuando termina. Para guardarlos en disco o enviarlos a otro sistema hay que convertirlos a un
formato de texto universal: **JSON**.

> 🧳 **Analogía:** serializar es **empacar** las cosas en una caja para un viaje (el objeto se
> vuelve texto, y el texto sí viaja o se guarda); deserializar es **desempacar** al llegar.

## Archivos

| Archivo | Para qué sirve |
|---------|----------------|
| [`serializacion_json.py`](./serializacion_json.py) | **La solución.** Clases, fábrica, serialización, deserialización y persistencia. |
| [`transacciones.txt`](./transacciones.txt) | 10 transacciones simuladas (`ID,TIPO,MONTO`) de los cuatro tipos. Los datos **no van dentro del código**. |
| [`transacciones.json`](./transacciones.json) | Archivo serializado. **Lo genera el programa**, no se escribe a mano. |

El recorrido completo: `transacciones.txt` → objetos Python → `transacciones.json`

## Paso 1 — Fundamentos de la serialización

Un intento de guardar el objeto directamente falla:

```text
TypeError: Object of type TransaccionCredito is not JSON serializable
```

- **Por qué falla:** JSON solo entiende textos, números, listas y diccionarios. Una clase propia
  del proyecto no está en esa lista.
- **La escala intermedia es obligatoria:** el módulo `json` no sabe traducir un objeto, pero sí
  sabe traducir un diccionario. Por eso se pasa primero por ahí.
- **Serializar:** Objeto → Diccionario → Texto JSON, con `json.dumps()`.
- **Deserializar:** Texto JSON → Diccionario → Objeto, con `json.loads()` y el constructor.

> ⚠️ **Detalle que se pregunta en el quiz:** `json.dumps()` **no** devuelve un diccionario, devuelve
> un `str`. Y `json.loads()` **no** devuelve un objeto, devuelve un diccionario. La `s` es de
> *string*, no es plural.

### Por qué JSON y no un texto plano cualquiera

Los dos son texto; la diferencia está en lo que cada formato **conserva**.

| Aspecto | Texto plano `C001,CREDITO,500000` | JSON |
|---------|-----------------------------------|------|
| Tipos de dato | Todo vuelve como texto: `'500000'` es `str` | El número vuelve como número |
| Significado | Hay que saber que el tercer campo es el monto | El nombre viaja pegado al valor |
| Errores de formato | Una columna faltante pasa inadvertida | Lanza `JSONDecodeError` con línea y columna |
| Compatibilidad | Exige escribir un lector propio en cada sistema | `json.loads()` está en casi todos los lenguajes |

> 💡 La primera fila tiene consecuencia directa en este proyecto: como el texto plano devuelve el
> monto en forma de cadena, hay que convertirlo con `float()`, y esa conversión es la que produjo
> los `ValueError` de la Actividad 1.

## Paso 2 — Objeto → JSON y viceversa

- **`objeto_a_diccionario()`** copia los atributos a un diccionario simple. Aquí se pierden los
  métodos: solo se copian datos.
- **`objeto_a_json()`** convierte ese diccionario en texto con `json.dumps()`.
- **`json_a_objeto()`** hace el camino inverso: `json.loads()` llega hasta el diccionario, y el
  último tramo es manual, llamando al constructor.

Las dos etapas se dejaron en **funciones separadas** a propósito, para que la secuencia
`Objeto → Diccionario → cadena JSON` quede visible y no escondida dentro de una sola llamada.

### Salida esperada

```text
1) Objeto original     : Transaccion [CREDITO ] - ID: C001 | Monto: $500,000.00
   Clase de Python     : TransaccionCredito
2) Diccionario         : {'cliente_id': 'C001', 'tipo': 'CREDITO', 'monto': 500000.0}
3) Texto JSON          : {"cliente_id": "C001", "tipo": "CREDITO", "monto": 500000.0}
4) Objeto reconstruido : TransaccionCredito, impacto $10,000.00 (el metodo volvio)
```

## Qué se pierde y qué se recupera

- **Se pierden los métodos.** En el JSON solo quedan los datos; `calcular_impacto()` no aparece.
  Vuelve al llamar al constructor.
- **No viaja la clase.** El JSON no guarda que era un `TransaccionCredito`: solo viaja
  `"tipo": "CREDITO"`. Es la fábrica `crear_transaccion()` la que decide qué clase construir en el
  destino.
- **No es el mismo objeto.** Es una copia nueva con los mismos datos, en otra dirección de memoria.

## Persistencia

**Persistir significa permanecer:** los datos siguen existiendo después de que el programa termina.
La memoria es volátil, el disco es persistente.

- Para archivos se usan **`json.dump()` y `json.load()`, sin la `s` final**. Las versiones con `s`
  trabajan con texto en memoria; estas leen y escriben el archivo directamente.
- El resultado es `transacciones.json`, un archivo de texto legible por una persona y por cualquier
  otro sistema.

> 💡 **Serializar y persistir no son lo mismo.** La serialización es la técnica (traducir el objeto
> a texto); la persistencia es el resultado (que ese texto quede guardado). Se puede serializar sin
> persistir, pero no persistir sin serializar: un disco no almacena objetos de Python, solo texto.

## Manejo de casos de error

Misma estrategia de la Actividad 1: detectar el fallo, dejar constancia y continuar.

| Origen del fallo | Excepción | Dónde se detecta |
|------------------|-----------|------------------|
| Texto JSON mal formado | `JSONDecodeError` | `json_a_objeto()` |
| Falta una clave en el registro | `ValueError` | `diccionario_a_objeto()` |
| Tipo de transacción desconocido | `ValueError` | `crear_transaccion()` |
| Monto no numérico o negativo | `ValueError` | *setter* de `TransaccionBase` |
| El archivo `.json` no existe | `FileNotFoundError` | `cargar_transacciones()` |
| No se puede escribir el archivo | `OSError` | `guardar_transacciones()` |

- **Los errores técnicos se traducen a errores del dominio.** Un `JSONDecodeError` describe lo que
  le pasó al módulo `json`; el mensaje útil es `"al registro le faltan las claves: monto"`.
- **Las claves se validan antes de usarlas**, en vez de dejar que salte un `KeyError` seco.
- **No todos los fallos se tratan igual:** los de un registro se aíslan y la carga sigue; los que
  impiden continuar, como un archivo inexistente, sí detienen el proceso.

> ⚠️ El monto se valida en el *setter* de `TransaccionBase`, conservando el encapsulamiento de la
> Semana 3. Así, un JSON con monto de texto o negativo se rechaza al reconstruir el objeto y no más
> adelante, cuando ya habría contaminado un cálculo.

## Cómo ejecutar

```bash
python3 serializacion_json.py
```

Lee `transacciones.txt`, muestra el viaje de ida y vuelta de una `TransaccionCredito`, guarda las 10
transacciones en `transacciones.json`, las vuelve a leer y comprueba los seis casos de error.
