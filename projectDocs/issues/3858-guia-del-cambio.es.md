<!-- markdownlint-configure-file {"MD004": {"style": "dash"}, "MD050": {"style": "asterisk"}} -->

# Listas descriptivas en NVDA: guía del cambio desde cero

**Fecha de revisión del código: 20 de septiembre de 2026.**
Esta guía explica el cambio local de la incidencia [NVDA #3858](https://github.com/nvaccess/nvda/issues/3858), sin suponer experiencia desarrollando NVDA.
No es necesario conocer C++ ni Python para seguir la explicación.

La referencia es la rama `fix/description-lists-3858`, comparada con su último commit, `c43cf6c1b0518326bd9ff0ed4712474feeb6131c`.
Se describe el **estado actual de los archivos**, no todas las versiones intermedias por las que pasó el trabajo.
Por ejemplo, el anuncio actual es **«description list»**, no «definition list», y las cabeceras ya no incluyen el nombre añadido del usuario.

## Cómo leer esta guía

- Primero lee las secciones 1 a 4: explican el problema y las piezas de NVDA.
- La sección 5 recorre todos los archivos de implementación, en orden de aprendizaje, no alfabético.
- Las secciones 6 y 7 explican las pruebas y los documentos.
- La sección 8 distingue lo comprobado de lo pendiente.
- La sección 9 indica por dónde empezar a investigar o modificar este trabajo en el futuro.

**Los enlaces de líneas se refieren a la copia actual de cada archivo**, contando desde 1.
Un rango agrupa instrucciones que trabajan juntas; no significa que todo el archivo haya cambiado.
También se explican las sustituciones y la línea eliminada que ya no tiene número propio en el archivo actual.
Las líneas vacías y los cierres de bloques se incluyen en el rango al que pertenecen.
Si posteriormente se añaden líneas antes de un enlace, su número puede desplazarse: esta es una instantánea, no un índice que se actualiza solo.

## 1. Qué problema estamos resolviendo

### 1.1. Una lista que no es una lista de viñetas

HTML es el lenguaje que describe la estructura de una página web.
Una etiqueta HTML indica qué representa un fragmento: un encabezado, una tabla, un enlace, etc.
Para las listas que nos interesan hay tres etiquetas:

- `dl`: contiene la lista descriptiva completa; su nombre actual en HTML es *description list*.
- `dt`: contiene un nombre o término.
- `dd`: contiene una descripción o valor asociado a los términos que lo preceden.

Por ejemplo: «Student» es el término y «Judy» es su valor.
No tiene que ser una definición de diccionario: también puede ser «Autor: Ana».
Históricamente se hablaba de *definition lists*, por eso la incidencia y algunos nombres de pruebas conservan ese vocabulario.

### 1.2. El detalle importante: pueden existir varios términos y varios valores

Imagina estos tres grupos:

1. Student → Judy.
2. Staff y Teacher → Melissa y Robin.
3. Color y Colour → A visual characteristic.

Aquí hay **tres grupos, cinco términos y cuatro descripciones**.
No son tres maneras de contar lo mismo: cada cifra responde a una pregunta diferente.

- El contenedor debe comunicar **tres elementos**, entendiendo «elemento» como grupo completo de asociación.
- La tecla `i` debe visitar **cinco términos**.
- Staff y Teacher deben indicar que cada uno comparte **dos definiciones**.
- Los otros términos tienen una sola; este parche no anuncia «con una definición» para evitar ruido repetitivo.

Contar todos los hijos de `dl` mezcla nombres y valores.
Dividir ese número entre dos tampoco funciona: no siempre hay exactamente un término por descripción.

### 1.3. Qué cambia para quien usa NVDA

El objetivo observable es:

- Distinguir el contenedor: «description list»; en braille, «dlst».
- Distinguir los términos de las definiciones: «term» frente a «definition».
- Contar grupos completos, no todos los nodos que cuelgan del contenedor.
- Anunciar el número de definiciones de un término cuando es mayor que uno.
- Conservar `l` y `shift+l` para listas, y usar `i` y `shift+i` para los términos dentro de estas listas.
- Evitar que el término se lea dos veces por llegar como nombre y como contenido.
- Respetar la opción existente de informar listas.
- Actualizar los conteos cuando la página añade o retira una definición.

Estas son decisiones de este parche local, no una afirmación de que NV Access ya las haya aprobado.

## 2. Las piezas de NVDA, explicadas sin conocimientos previos

### 2.1. NVDA no lee directamente el código HTML para todo

El navegador interpreta la página y publica información de accesibilidad.
NVDA consulta esa información: texto, tipo de elemento, estados, relaciones y estructura.
El navegador y NVDA necesitan hablar un mismo «idioma» técnico, una **API de accesibilidad**.

En este cambio hay tres caminos:

- **IAccessible2, abreviado IA2:** lo usan Firefox y también Chromium cuando NVDA accede por IA2.
- **UI Automation, abreviado UIA:** otro camino de Windows, que aquí se adapta específicamente para Chromium.
- **MSHTML:** el motor antiguo asociado a Internet Explorer y a aplicaciones que lo alojan; tiene su propio camino.

**Chromium** es la base tecnológica de Chrome y otros navegadores.
**Gecko** es el motor de Firefox.
Aunque un archivo se llame «gecko», parte de su código de IA2 también sirve para Chromium: el nombre histórico no limita todos sus usos actuales.

### 2.2. Un objeto no es lo mismo que un fragmento de texto

Un `NVDAObject` representa un elemento accesible: por ejemplo, la lista completa.
Un `TextInfo` representa una posición o un intervalo de texto que se está leyendo.

Al leer, NVDA combina texto con **campos de control**, llamados `ControlField`.
Piensa en cada campo como una ficha con datos: «soy una lista», «tengo dos grupos», «este término tiene tres definiciones».
El lector de voz y el generador de braille consultan esas fichas.

Esto explica por qué a veces se modifica tanto el rol del objeto como el del campo de texto: son representaciones distintas, usadas por caminos distintos.
En Chromium UIA se toma una decisión deliberada diferente: cambiar el campo de lectura sin cambiar el rol del objeto, para no recorrer el árbol cada vez que alguien pregunta por ese rol.

### 2.3. Qué es el búfer virtual

Para el modo exploración, NVDA construye una representación de la página que permite leer por líneas y saltar por encabezados, enlaces o listas.
Esa representación se llama **búfer virtual**.
No es una captura de pantalla: contiene texto y datos estructurados.

En los caminos nativos IA2 y MSHTML, código C++ ayuda a construirlo y Python interpreta los resultados.
En UIA se utilizan también los intervalos y elementos que ofrece esa API; no se añade aquí una llamada al contador C++.

### 2.4. Diccionario mínimo para leer las secciones siguientes

- **Rol:** qué clase de cosa es un elemento. Ejemplos: botón, lista, término.
- **Estado:** una característica del elemento. Ejemplos: solo lectura, editable, seleccionado.
- **Nodo:** una pieza de la estructura en árbol; puede tener hijos y un padre.
- **Backend o proveedor:** el adaptador que obtiene información de una tecnología concreta.
- **Normalizar:** convertir datos de distintas procedencias al formato común que espera NVDA.
- **Wrapper o envoltura:** un elemento intermedio, como un `div`, que agrupa otros sin ser un término ni una definición.
- **Quick navigation o navegación rápida:** saltos como `i`, `l` y sus variantes con `shift`.
- **DOM:** la estructura de la página que el navegador mantiene y puede modificar mientras está abierta.
- **Runtime ID:** identificador de un elemento UIA durante la ejecución. Permite reconocerlo sin comparar su texto.
- **COM:** mecanismo de Windows para hablar con ciertos objetos y APIs; una llamada puede fallar y producir `COMError`.
- **Prueba de regresión:** comprueba que un error corregido no reaparece después de otro cambio.
- **Mock o doble de prueba:** imitación controlada de una dependencia; sirve para probar lógica, no demuestra cómo se comporta un navegador real.
- **Diff:** comparación entre una versión anterior y otra nueva; sus bloques de cambios suelen llamarse *hunks*.

## 3. Los datos que viajan por el sistema

### 3.1. Tres roles, pero solo dos son nuevos

- `Role.TERM = 159`: nuevo identificador interno para un término.
- `Role.DESCRIPTIONLIST = 160`: nuevo identificador interno para la lista descriptiva.
- `Role.DEFINITION = 157`: **ya existía**; lo reutilizamos para las definiciones.

Se añaden valores al final de la enumeración, sin cambiar los números anteriores.
Es importante porque los complementos pueden utilizar estos identificadores.
Ser aditivo reduce el riesgo, pero no demuestra que cualquier complemento que enumere roles siga funcionando sin revisión.

`DESCRIPTIONLIST` es un nombre interno de NVDA, **no un nuevo token ARIA para páginas web**.
ARIA es otro vocabulario que permite al autor de una página declarar roles accesibles.
Este parche reconoce `term`, pero no inventa `role="descriptionlist"` ni `role="associationlist"`.

### 3.2. Dos cantidades diferentes

- `description-list-group-count`: número de grupos completos; se produce en el búfer nativo.
- `_childcontrolcount`: dato que la presentación ya sabía usar para anunciar el tamaño de una lista. Para estas listas se sustituye por el conteo de grupos.
- `definition-count`: número de definiciones asociadas a **ese término**. Todos los términos del mismo grupo reciben el mismo número.

Aunque haya tres nombres de propiedades, solo se están representando dos cantidades: tamaño de la lista en grupos y cantidad de definiciones por término.
Los atributos del búfer nativo viajan inicialmente como texto; después se convierten a enteros donde corresponde.
Por eso fue necesaria una corrección en braille: no se puede concatenar directamente una cadena con un entero en Python.

### 3.3. Recorrido de un ejemplo, de principio a fin

Para «Staff, Teacher → Melissa, Robin»:

1. El navegador expone los dos términos y las dos definiciones.
2. El proveedor de NVDA reconoce la estructura y calcula **un grupo**.
3. Cada término recibe `definition-count = 2`.
4. El campo del contenedor recibe el rol `DESCRIPTIONLIST`; los términos, `TERM`.
5. La capa de presentación decide si debe anunciar las listas según la configuración.
6. Voz construye «Staff, term, with 2 definitions»; braille añade «trm 2 defs».
7. La navegación rápida busca el siguiente término, no la siguiente definición.

**Cambiar únicamente el texto de voz no habría bastado:** el conteo erróneo y los destinos de navegación seguirían siendo los mismos.

## 4. Alcance exacto de este documento

Antes de crear esta guía había **31 archivos intencionales**:

- 18 de implementación: cuatro de C++ y catorce de Python.
- 7 de pruebas: tres modificados y cuatro nuevos.
- 6 de documentación o ejemplos: tres modificados y tres nuevos.

Esta guía es el archivo adicional número 32.
Los 24 archivos que ya existían se compararon con Git; los siete nuevos se leyeron completos, porque todavía no están registrados en un commit.

**No se incluyen como trabajo de esta funcionalidad** las diferencias previas en las dependencias eSpeak, liblouis, nvda-cldr y la carpeta nvda_dmp.
Que aparezcan en el estado de Git no significa que formen parte del arreglo.
Tampoco se presentan las carpetas de compilación o los registros de pruebas como código fuente añadido a la contribución.

Los años de copyright cambiados se indican expresamente en cada archivo afectado.
Se ha conservado la atribución anterior; se retiró el nombre personal añadido durante el desarrollo.
No se ha aprovechado este trabajo para modernizar todas las cabeceras antiguas ni corregir sus erratas históricas.

## 5. Archivos de implementación: qué hace cada uno y por qué cambia

### 5.1. Vocabulario interno de roles

**Archivo:** [source/controlTypes/role.py](../../source/controlTypes/role.py).

Es el catálogo común de tipos de elementos y de sus nombres hablados.
Un navegador no debe inventarse sus propios identificadores de NVDA: todos los proveedores comparten este catálogo.

- [Línea 4](../../source/controlTypes/role.py#L4): actualiza 2022 a 2026 en el copyright; no cambia el funcionamiento.
- [Líneas 205–206](../../source/controlTypes/role.py#L205-L206): añade `TERM` y `DESCRIPTIONLIST`, con los valores 159 y 160.
- [Líneas 240–241](../../source/controlTypes/role.py#L240-L241): comentario para traductores y etiqueta «description list».
- [Líneas 539–540](../../source/controlTypes/role.py#L539-L540): comentario y etiqueta «term».

La llamada `_()` marca una cadena como traducible.
Cambiar el anuncio del contenedor más adelante sería cambiar esta etiqueta y las traducciones, pruebas y documentos correspondientes; no exige renumerar el rol ni reescribir el contador.

### 5.2. Traducción de roles ARIA a roles de NVDA

**Archivo:** [source/aria.py](../../source/aria.py).

Es un diccionario: a un nombre de rol de la web le corresponde un rol interno de NVDA.

- [Línea 2](../../source/aria.py#L2): copyright de 2022 a 2026.
- [Línea 58](../../source/aria.py#L58): añade la asociación `term` → `Role.TERM`.

Esto permite que los consumidores de ese diccionario reconozcan un término explícito.
No añade un rol ARIA para `dl`.
Tampoco cambia globalmente `description` a `DEFINITION`: en Chromium UIA, `description` puede representar texto estático, no el contenedor de una definición.

### 5.3. Reglas comunes para decidir qué anunciar

**Archivo:** [source/textInfos/\_\_init\_\_.py](../../source/textInfos/__init__.py).

Aquí está `ControlField`, la ficha que describe el elemento que rodea al texto.
También se decide su categoría de presentación: contenido que debe marcarse, contenedor del que se entra y sale, o mera disposición que no necesita anunciarse.

- [Líneas 57–59](../../source/textInfos/__init__.py#L57-L59): documentan `definition-count`, su tipo entero y cuándo omitirlo. Si el proveedor no puede calcularlo, no debe inventar un valor.
- [Líneas 139–143](../../source/textInfos/__init__.py#L139-L143): con `reportLists` desactivado, lista descriptiva, término y definición se tratan como disposición. Se ocultan sus anuncios estructurales, **no el texto de la página**.
- [Líneas 204–205](../../source/textInfos/__init__.py#L204-L205): clasifican término y definición como marcadores. Interesa indicar qué son, sin anunciar una salida de cada término como si fuese una región grande.
- [Línea 221](../../source/textInfos/__init__.py#L221): clasifica la lista descriptiva como contenedor. Así puede anunciarse la entrada y «out of description list» al salir usando el mecanismo existente.

**Por qué aquí:** la decisión sirve tanto para voz como para braille y para varios navegadores.
No se crea una opción nueva en la interfaz; se reutiliza informar listas.

### 5.4. Construcción del anuncio hablado

**Archivo:** [source/speech/speech.py](../../source/speech/speech.py).

Esta capa convierte los campos comunes en una secuencia de información que se enviará a voz.
No debería tener que averiguar por sí misma qué HTML originó cada campo.

- [Línea 4](../../source/speech/speech.py#L4): copyright de 2025 a 2026.
- [Líneas 2362–2367](../../source/speech/speech.py#L2362-L2367): si el rol es `TERM` y su conteo supera uno, añade «with N definitions» al texto del rol. `ngettext()` deja que cada idioma gestione sus formas de plural.
- [Líneas 2421–2424](../../source/speech/speech.py#L2421-L2424): amplía la condición del anuncio de tamaño para admitir `DESCRIPTIONLIST`. Antes solo se admitía `LIST` con estado de solo lectura; ese requisito se conserva para las listas ordinarias, pero no se impone al nuevo contenedor.

La condición que rodea este último bloque sigue limitando el anuncio al momento apropiado de entrada en el contenedor.
La frase de salida no se añade como una cadena especial por navegador: procede de la categoría de contenedor y de la etiqueta del rol.

### 5.5. Abreviaturas para braille

**Archivo:** [source/braille/labels.py](../../source/braille/labels.py).

Las celdas braille son limitadas; los nombres de roles pueden tener abreviaturas diferentes de lo hablado.

- [Líneas 45–46](../../source/braille/labels.py#L45-L46): añade «dlst» para `DESCRIPTIONLIST`, con comentario para traducción.
- [Líneas 168–169](../../source/braille/labels.py#L168-L169): añade «trm» para `TERM`, también traducible.

Este archivo decide **las palabras**, no cuántas definiciones existen.
El copyright ya incluía 2026; no queda un cambio neto de cabecera frente a Git.

### 5.6. Composición de la información braille

**Archivo:** [source/braille/regions/properties.py](../../source/braille/regions/properties.py).

Aquí se combinan rol, estados, cantidades y contenido para formar el texto destinado a braille.

- [Línea 94](../../source/braille/regions/properties.py#L94): incluye `DESCRIPTIONLIST` en el tratamiento de listas.
- [Líneas 96–97](../../source/braille/regions/properties.py#L96-L97): reserva el tratamiento de lista multiselección para `LIST`; una lista descriptiva no debe recibir esa abreviatura por herencia accidental.
- [Línea 111](../../source/braille/regions/properties.py#L111): convierte el conteo a texto antes de concatenarlo. Evita el error de intentar sumar, por ejemplo, «dlst» y el entero 2.
- [Líneas 308–311](../../source/braille/regions/properties.py#L308-L311): permite transferir el conteo del campo también para `DESCRIPTIONLIST`.
- [Líneas 315–320](../../source/braille/regions/properties.py#L315-L320): añade «N defs» a los términos con más de una definición; usa separación y pluralización traducible.

El resultado puede ser «dlst2» para el contenedor y «trm 2 defs» para el término.
Esto describe el texto generado por NVDA; no sustituye una comprobación con una línea braille física.

### 5.7. Declaración del contador nativo compartido

**Archivo:** [nvdaHelper/vbufBase/utils.h](../../nvdaHelper/vbufBase/utils.h).

En C++, una cabecera permite a otros archivos saber que una función existe y qué datos necesita.
No contiene aquí el cálculo; lo anuncia para que Gecko y MSHTML puedan llamarlo.

- [Línea 4](../../nvdaHelper/vbufBase/utils.h#L4): copyright de 2010 a 2026, manteniendo la atribución colectiva original.
- [Líneas 69–73](../../nvdaHelper/vbufBase/utils.h#L69-L73): documentan qué cuenta el helper, el límite de una envoltura y la necesidad de actualizar lista y términos juntos.
- [Líneas 74–81](../../nvdaHelper/vbufBase/utils.h#L74-L81): declaran `fillDescriptionListCounts()` y sus parámetros, más el separador final.

Los parámetros indican el nodo de la lista y los nombres de atributos y etiquetas usados por el proveedor.
Así se comparte un algoritmo sin obligar a MSHTML a usar los nombres internos de IA2.

### 5.8. El algoritmo que cuenta grupos y definiciones en C++

**Archivo:** [nvdaHelper/vbufBase/utils.cpp](../../nvdaHelper/vbufBase/utils.cpp).

Es la implementación del contador compartido.
La explicación paso a paso es importante: aquí se decide qué significan realmente las cantidades anunciadas.

- [Línea 4](../../nvdaHelper/vbufBase/utils.cpp#L4): copyright de 2010 a 2026.
- [Líneas 18–19](../../nvdaHelper/vbufBase/utils.cpp#L18-L19): incorpora herramientas estándar de C++ para una función recursiva y una colección de términos.
- [Líneas 24–33](../../nvdaHelper/vbufBase/utils.cpp#L24-L33): abre `fillDescriptionListCounts()` y prepara el contador de grupos, el de definiciones y la lista de términos pendientes.
- [Líneas 34–43](../../nvdaHelper/vbufBase/utils.cpp#L34-L43): `finishGroup()` cierra un grupo. Solo suma un grupo si hay términos y definiciones; escribe el mismo número de definiciones en cada término y vacía el estado para el siguiente grupo.
- [Líneas 44–50](../../nvdaHelper/vbufBase/utils.cpp#L44-L50): prepara el recorrido de hijos. Omite los nodos que no son controles; no cuenta los fragmentos de texto como definiciones independientes.
- [Líneas 51–55](../../nvdaHelper/vbufBase/utils.cpp#L51-L55): marca que un cambio en un hijo requiere actualizar el padre y omite los controles ocultos.
- [Líneas 56–61](../../nvdaHelper/vbufBase/utils.cpp#L56-L61): al encontrar un término, cierra el grupo anterior si ya tenía definiciones y guarda el nuevo término.
- [Líneas 62–65](../../nvdaHelper/vbufBase/utils.cpp#L62-L65): una definición incrementa la cantidad; una envoltura permitida se recorre con la prohibición de entrar en otra envoltura dentro de ella.
- [Líneas 66–69](../../nvdaHelper/vbufBase/utils.cpp#L66-L69): cierra el recorrido y lo ejecuta desde la lista.
- [Líneas 70–75](../../nvdaHelper/vbufBase/utils.cpp#L70-L75): cierra el último grupo, guarda el total y fuerza la reconstrucción de descendientes cuando se actualiza la lista; incluye el cierre y la separación de la función.

**Ejemplo de estado:** llegan Staff y Teacher, se guardan ambos; llegan Melissa y Robin, el contador de definiciones pasa a dos; llega el siguiente término, se cierra el grupo y ambos términos anteriores reciben dos.

No se entra dentro de cada definición para contar sus párrafos o las definiciones de una lista interior.
Eso evita que una descripción larga se convierta artificialmente en varias.
Un término final sin definición puede recibir cero, pero no forma un grupo completo.
El estado se comparte al recorrer las envolturas hermanas: también se toleran algunas estructuras irregulares, sin pretender ser un validador HTML.

**Por qué las marcas de actualización:** al retirar Robin, también debe cambiar el dato guardado en Staff y Teacher, aunque sus textos no hayan cambiado.
Reutilizar ciegamente esos nodos dejaría un número antiguo.
Reconstruir descendientes tiene un coste; aquí se prioriza la coherencia de los conteos.

### 5.9. Activación del contador desde Gecko/IA2

**Archivo:** [nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp).

Este backend construye nodos del búfer a partir de IAccessible2.
Es utilizado para Firefox y para el camino IA2 de Chromium.

- [Línea 4](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L4): copyright de 2023 a 2026; conserva NV Access y Mozilla, sin el nombre añadido.
- [Líneas 1373–1379](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1373-L1379): si la etiqueta es `dl` y el rol nativo es de lista, llama al contador compartido con los nombres de atributos IA2 y las etiquetas en minúsculas.

La llamada está al final del procesamiento relevante del nodo, cuando sus hijos ya están disponibles.
No tendría sentido contar antes de construirlos.
Las listas ordinarias no entran en esta condición.
El respeto al rol explícito también necesita la normalización Python explicada más abajo; no depende solo de esta comprobación C++.

### 5.10. Activación del contador desde MSHTML

**Archivo:** [nvdaHelper/vbufBackends/mshtml/mshtml.cpp](../../nvdaHelper/vbufBackends/mshtml/mshtml.cpp).

- [Línea 4](../../nvdaHelper/vbufBackends/mshtml/mshtml.cpp#L4): copyright de 2010 a 2026.
- [Líneas 1343–1346](../../nvdaHelper/vbufBackends/mshtml/mshtml.cpp#L1343-L1346): para `DL`, llama al mismo helper usando el atributo de nombre de nodo de MSHTML y etiquetas en mayúsculas.

**Por qué otro punto de entrada:** MSHTML construye su propio búfer y no pasa por el backend Gecko.
**Por qué no otro contador completo:** las reglas de asociación son las mismas; duplicarlas facilitaría que los navegadores terminasen contando de forma distinta.
La normalización posterior decide si utilizar el conteo como tamaño de una lista descriptiva.

### 5.11. Conversión común de números del búfer

**Archivo:** [source/virtualBuffers/\_\_init\_\_.py](../../source/virtualBuffers/__init__.py).

- [Línea 2](../../source/virtualBuffers/__init__.py#L2): copyright de 2025 a 2026.
- [Línea 398](../../source/virtualBuffers/__init__.py#L398): amplía el comentario: ya no se trata solamente de números de tablas.
- [Línea 400](../../source/virtualBuffers/__init__.py#L400): añade `definition-count` a los atributos que se convierten de texto a entero.

Esto evita que cada consumidor tenga que manejar de forma distinta el «2» que llegó del búfer nativo.
La conversión se comparte entre los normalizadores que utilizan esta base.

### 5.12. Normalización y navegación del búfer Gecko/IA2

**Archivo:** [source/virtualBuffers/gecko_ia2.py](../../source/virtualBuffers/gecko_ia2.py).

Esta capa recibe los atributos del búfer C++ y los convierte a roles y campos utilizables por la presentación.
También establece qué nodos encuentra la navegación rápida.

- [Líneas 131–134](../../source/virtualBuffers/gecko_ia2.py#L131-L134): guarda la etiqueta HTML, divide los roles declarados y busca el primer rol reconocido. La comprobación previa de `blockquote` se conserva, pero ahora usa la variable común.
- [Líneas 136–137](../../source/virtualBuffers/gecko_ia2.py#L136-L137): convierte una lista nativa `dl` sin rol explícito reconocido a `DESCRIPTIONLIST`.
- [Líneas 138–141](../../source/virtualBuffers/gecko_ia2.py#L138-L141): reconoce `dt` como término y `dd` como definición, bajo las condiciones de rol indicadas en el código. No se sustituye indiscriminadamente cualquier rol explícito.
- [Líneas 142–143](../../source/virtualBuffers/gecko_ia2.py#L142-L143): retira el atributo `name` de términos y definiciones; el contenido textual permanece y no debe repetirse como un nombre separado.
- [Líneas 144–146](../../source/virtualBuffers/gecko_ia2.py#L144-L146): si el rol final es `DESCRIPTIONLIST` y el contador existe, lo usa como `_childcontrolcount`. Comprueba ausencia, no solo si el número es distinto de cero.
- **Eliminación:** se quita la segunda lectura de `xmlRoles`, que estaba en la antigua línea 179. Ahora el dato se prepara una sola vez en [la línea 132 actual](../../source/virtualBuffers/gecko_ia2.py#L132) y se reutiliza; no se elimina el procesamiento posterior de roles.
- [Líneas 464–471](../../source/virtualBuffers/gecko_ia2.py#L464-L471): sustituye la única condición de búsqueda de elementos de lista por tres alternativas: elementos nativos ordinarios, `dt` sin atributo de rol y marcos de texto IA2 con el token `term`.

La búsqueda trabaja sobre atributos del proveedor, no simplemente sobre la palabra que se anuncia.
Por eso cambiar el catálogo de roles no bastaba para que `i` encontrase todos los términos.
La búsqueda de listas con `l` sigue utilizando el rol nativo de lista.

### 5.13. Rol del objeto web IA2

**Archivo:** [source/NVDAObjects/IAccessible/ia2Web.py](../../source/NVDAObjects/IAccessible/ia2Web.py).

- [Línea 4](../../source/NVDAObjects/IAccessible/ia2Web.py#L4): copyright de 2022 a 2026.
- [Líneas 111–123](../../source/NVDAObjects/IAccessible/ia2Web.py#L111-L123): añade un método de obtención del rol. Parte del rol heredado; solo lo cambia si era `LIST`, la etiqueta es `dl` y no hay un rol ARIA reconocido en `xml-roles`.

**Por qué además del archivo anterior:** el búfer de texto no es la única forma de consultar un elemento.
Este cambio da identidad de lista descriptiva al propio objeto web IA2.
Las listas `ul` y `ol` y los roles explícitos reconocidos conservan el camino previo.

### 5.14. Conservación del tratamiento especial de listas en IAccessible

**Archivo:** [source/NVDAObjects/IAccessible/\_\_init\_\_.py](../../source/NVDAObjects/IAccessible/__init__.py).

Al inventar un nuevo rol interno hay que revisar los lugares que antes reconocían exclusivamente `LIST`.
De lo contrario una lista que ayer recibía cierto tratamiento podría dejar de recibirlo solo por el cambio de nombre interno.

- [Líneas 1115–1116](../../source/NVDAObjects/IAccessible/__init__.py#L1115-L1116): mantiene `DESCRIPTIONLIST` dentro de la excepción de listas al resolver los estados de solo lectura y editable en IA2. No convierte la lista en un cuadro de edición; conserva la excepción que distingue listas interactivas y no interactivas.
- [Línea 2055](../../source/NVDAObjects/IAccessible/__init__.py#L2055): incluye el nuevo rol entre los descendientes considerados para hablar en el tratamiento de alertas.

Son cambios de integración: no cuentan grupos ni generan un anuncio nuevo por sí solos.
La cabecera ya estaba actualizada; no hay cambio neto de copyright.

### 5.15. Adaptación específica de Chromium con IA2

**Archivo:** [source/NVDAObjects/IAccessible/chromium.py](../../source/NVDAObjects/IAccessible/chromium.py).

- [Línea 4](../../source/NVDAObjects/IAccessible/chromium.py#L4): copyright de 2022 a 2026.
- [Líneas 195–197](../../source/NVDAObjects/IAccessible/chromium.py#L195-L197): amplía a `DESCRIPTIONLIST` la selección de la clase auxiliar `PresentationalList` para etiquetas de lista.

Una clase auxiliar u *overlay* añade comportamiento especializado a un objeto.
En este caso permite conservar el tratamiento de lista de presentación y su estado de solo lectura.
Sin incluir el rol nuevo, una `dl` podría dejar de recibir el tratamiento que recibía cuando era simplemente `LIST`.

### 5.16. Roles de objetos MSHTML

**Archivo:** [source/NVDAObjects/IAccessible/MSHTML.py](../../source/NVDAObjects/IAccessible/MSHTML.py).

- [Línea 3](../../source/NVDAObjects/IAccessible/MSHTML.py#L3): copyright de 2025 a 2026.
- [Línea 133](../../source/NVDAObjects/IAccessible/MSHTML.py#L133): cambia `DL` de `LIST` a `DESCRIPTIONLIST` en el diccionario de etiquetas.
- [Líneas 135–136](../../source/NVDAObjects/IAccessible/MSHTML.py#L135-L136): cambia `DD` y `DT`, que antes eran ambos `LISTITEM`, a `DEFINITION` y `TERM` respectivamente.
- [Línea 814](../../source/NVDAObjects/IAccessible/MSHTML.py#L814): inicializa `ariaRole` a `None`; así hay un valor definido incluso cuando no existe nodo HTML.
- [Líneas 816–823](../../source/NVDAObjects/IAccessible/MSHTML.py#L816-L823): en vez de quedarse con la primera palabra del atributo `role`, elige la primera reconocida. Por ejemplo, un token desconocido no debe ocultar un `list` válido que viene después.
- [Línea 833](../../source/NVDAObjects/IAccessible/MSHTML.py#L833): incluye `DL` entre las etiquetas cuyo rol HTML se consulta aunque no se cumpla la condición de ancestro accesible.

El método consulta primero el rol explícito reconocido y después la etiqueta.
Así un cambio intencionado de rol no queda anulado simplemente por haber escrito `dl` en HTML.

### 5.17. Normalización y navegación del búfer MSHTML

**Archivo:** [source/virtualBuffers/MSHTML.py](../../source/virtualBuffers/MSHTML.py).

- [Línea 4](../../source/virtualBuffers/MSHTML.py#L4): copyright de 2024 a 2026.
- [Línea 99](../../source/virtualBuffers/MSHTML.py#L99): usa `split()` para separar roles por espacios en blanco, incluidas tabulaciones; sustituye una separación limitada al espacio literal con un filtro adicional.
- [Líneas 215–219](../../source/virtualBuffers/MSHTML.py#L215-L219): sustituye el conteo de hijos por el de grupos solo si el rol normalizado es `DESCRIPTIONLIST` y el dato existe.
- [Línea 435](../../source/virtualBuffers/MSHTML.py#L435): elimina `DD` de los destinos de `listItem`. Conserva `LI` para listas ordinarias y `DT` para términos.

El mapa de roles del archivo de objetos anterior también sirve en esta normalización.
Aquí no se repite el cálculo C++; se consume su resultado.

### 5.18. Chromium con UI Automation: el camino que necesita su propio contador

**Archivo:** [source/NVDAObjects/UIA/chromium.py](../../source/NVDAObjects/UIA/chromium.py).

Es el archivo de implementación con más lógica nueva.
No puede reutilizar directamente el recorrido de nodos C++: sus datos llegan como elementos UIA.

#### Preparación e identidad de elementos

- [Línea 4](../../source/NVDAObjects/UIA/chromium.py#L4): copyright de 2021 a 2026.
- [Líneas 7–12](../../source/NVDAObjects/UIA/chromium.py#L7-L12): incorpora manejo de errores COM, una estructura de datos sencilla y el mapa ARIA; recoloca la importación UIA existente.
- [Líneas 15–16](../../source/NVDAObjects/UIA/chromium.py#L15-L16): importa campos de texto y el iterador de navegación UIA ya existente.
- [Líneas 25–32](../../source/NVDAObjects/UIA/chromium.py#L25-L32): `_getPrimaryAriaRole()` comprueba que recibió texto y selecciona el primer rol reconocido. «button term» sigue siendo botón; «unsupported term» permite reconocer término.
- [Líneas 35–40](../../source/NVDAObjects/UIA/chromium.py#L35-L40): `_DescriptionListInfo` guarda el número de grupos y un diccionario que relaciona el identificador de cada término con su cantidad de definiciones.

Usar el identificador en lugar del nombre evita confundir dos términos que contengan exactamente el mismo texto.

#### Obtener los conteos desde el árbol completo

- [Líneas 43–56](../../source/NVDAObjects/UIA/chromium.py#L43-L56): contrato y limitaciones de `_getDescriptionListInfo()`.
- [Líneas 57–62](../../source/NVDAObjects/UIA/chromium.py#L57-L62): prepara el recorrido usando **`RawViewWalker`**, la vista cruda de UIA, y los contadores.
- [Líneas 64–71](../../source/NVDAObjects/UIA/chromium.py#L64-L71): cierre de grupo, equivalente conceptual al de C++; asigna el mismo conteo a todos sus términos.
- [Líneas 73–92](../../source/NVDAObjects/UIA/chromium.py#L73-L92): recorre hijos y una capa de grupos; reconoce términos expuestos como `listitem` o `term`, y cuenta solamente nodos `definition`.
- [Líneas 94–105](../../source/NVDAObjects/UIA/chromium.py#L94-L105): comprueba el rol del contenedor, descarta el resultado si falla COM y solo devuelve información descriptiva si vio alguna definición.

**Por qué vista cruda:** la vista de controles puede omitir el contenedor de una definición y mostrar sus párrafos.
Contar estos últimos produjo un exceso de definiciones en las pruebas anteriores.
El código actual no cuenta `description` como definición: ese rol puede ser simplemente el texto que hay dentro.

**Por qué el árbol completo:** cuando se lee una sola línea o se salta a un término, el intervalo leído puede no incluir sus definiciones hermanas.
Un contador basado solo en ese intervalo daría un número incompleto.

**Límites importantes:** UIA no permite aquí distinguir un `dl` nativo de un `role="list"` con exactamente los mismos descendientes.
Una lista vacía o sin definiciones expuestas permanece como lista ordinaria.
Otros roles reconocidos del contenedor, como `listbox` o `directory`, no se tratan como lista descriptiva por este detector.
Si hay un fallo COM no se publica un conteo parcial como si fuese fiable.

#### Incorporar los datos al texto leído

- [Líneas 108–138](../../source/NVDAObjects/UIA/chromium.py#L108-L138): `_normalizeDescriptionListTerms()` recorre los campos de texto con una pila, es decir, un registro de qué contenedores están abiertos. Busca la **lista más cercana**, convierte sus elementos apropiados a términos, elimina nombres duplicados y asigna conteos por runtime ID. Al salir de un campo lo retira de la pila.
- [Líneas 139–140](../../source/NVDAObjects/UIA/chromium.py#L139-L140): separación entre los helpers nuevos y la clase existente; sin efecto funcional.
- [Líneas 180–190](../../source/NVDAObjects/UIA/chromium.py#L180-L190): al construir un campo de lista, obtiene la información completa y cambia **el campo**, no el objeto, a `DESCRIPTIONLIST`; guarda temporalmente los conteos y limpia los atributos de nombre/contenido duplicados de términos ya reconocidos.
- [Líneas 200–207](../../source/NVDAObjects/UIA/chromium.py#L200-L207): aplica el normalizador al resultado de `getTextWithFields()` y lo devuelve; incluye el separador del método.

La información temporal `_descriptionListInfo` se retira del campo al usarla; no es un nuevo dato público destinado a voz.
Si hay una lista ordinaria dentro de una descripción, actúa como frontera: sus elementos no heredan los conteos ni el rol de término de la lista exterior.

#### Navegación rápida

- [Líneas 220–235](../../source/NVDAObjects/UIA/chromium.py#L220-L235): para `listItem`, busca el tipo de control UIA de elemento de lista **o** el rol UIA `term`. Reutiliza `UIAControlQuicknavIterator`. Para otros tipos de navegación conserva el método heredado; incluye el separador final.

No es un lector nuevo de páginas ni una implementación independiente de todas las teclas: se adapta únicamente la búsqueda necesaria.

## 6. Archivos de pruebas: qué verifican y qué no

Una prueba contiene datos de entrada, una acción y una expectativa.
Que el código de una prueba diga «espero dos definiciones» **no significa por sí solo que la prueba haya pasado**.
Los resultados de ejecución se separan al final de esta guía.

### 6.1. Categorías de presentación

**Archivo modificado:** [tests/unit/test_textInfos.py](../../tests/unit/test_textInfos.py).

- [Línea 12](../../tests/unit/test_textInfos.py#L12): importa los roles comunes para utilizarlos en las comprobaciones.
- [Líneas 26–47](../../tests/unit/test_textInfos.py#L26-L47): añade una clase con dos pruebas: con informar listas activado, término y definición son marcadores; desactivado, son disposición. El rango incluye los separadores.

**Por qué existe:** evita que un cambio posterior vuelva a anunciar esos roles cuando el usuario ha pedido no informar listas.
No abre un navegador ni escucha un sintetizador.

### 6.2. Conteos y presentación común

**Archivo nuevo completo:** [tests/unit/test_descriptionLists.py](../../tests/unit/test_descriptionLists.py), 196 líneas.

- [Líneas 1–21](../../tests/unit/test_descriptionLists.py#L1-L21): cabecera, explicación e importaciones. La inicialización de IAccessible antes de sus módulos evita un problema de importaciones circulares en estas pruebas aisladas.
- [Líneas 22–40](../../tests/unit/test_descriptionLists.py#L22-L40): verifica que los conteos 0, 1, 2 y 5 del búfer se conservan como enteros y que `dt` se normaliza a término, tanto en IA2 como en MSHTML.
- [Líneas 42–59](../../tests/unit/test_descriptionLists.py#L42-L59): da al campo siete hijos estructurales, pero dos grupos; comprueba que acaba como `DESCRIPTIONLIST` con tamaño dos.
- [Líneas 62–65](../../tests/unit/test_descriptionLists.py#L62-L65): prepara una copia de la configuración con informar listas activado.
- [Líneas 67–85](../../tests/unit/test_descriptionLists.py#L67-L85): prueba el conteo hablado para lectura con cursor, lectura continua, navegación rápida y foco. Solo se añade cuando supera uno.
- [Líneas 87–93](../../tests/unit/test_descriptionLists.py#L87-L93): comprueba que el conteo no se repite al permanecer dentro del término o al salir de él en el contexto probado.
- [Líneas 95–103](../../tests/unit/test_descriptionLists.py#L95-L103): comprueba «trm» o «trm N defs» al entrar y ausencia de marca de salida del término en braille.
- [Líneas 105–112](../../tests/unit/test_descriptionLists.py#L105-L112): prueba conteos de lista tanto en texto como en entero; es la regresión contra el error de concatenación en braille, para listas ordinarias y descriptivas.
- [Líneas 114–153](../../tests/unit/test_descriptionLists.py#L114-L153): comprueba entrada «description list», salida «out of description list», categoría de contenedor, salida braille «dlst end» y supresión al desactivar informar listas. Lo repite con varios motivos de lectura y con o sin estado de solo lectura.
- [Líneas 155–161](../../tests/unit/test_descriptionLists.py#L155-L161): comprueba que desactivar listas suprime tanto el rol como el conteo del término en voz y braille.
- [Líneas 163–180](../../tests/unit/test_descriptionLists.py#L163-L180): comprueba que añadir `definition-count` a otros roles no altera su presentación.
- [Líneas 182–196](../../tests/unit/test_descriptionLists.py#L182-L196): conserva el conteo cuando se utiliza una descripción de rol personalizada, como «entry» o «ent».

Las líneas separadoras restantes solo organizan el archivo.
Las llamadas braille prueban el texto de presentación y la entrada/salida de campos, **no braille contraído frente a no contraído** ni un dispositivo físico.

### 6.3. Proveedores UIA, IA2 y MSHTML simulados

**Archivo nuevo completo:** [tests/unit/test_NVDAObjects_UIA_chromium.py](../../tests/unit/test_NVDAObjects_UIA_chromium.py), 464 líneas.

Aunque su nombre menciona UIA Chromium, la última clase también prueba roles de proveedores nativos.

- [Líneas 1–23](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L1-L23): cabecera e importaciones de infraestructura y proveedores.
- [Líneas 24–58](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L24-L58): crea elementos, un recorrido de árbol y flujos de campos simulados. Permiten preparar casos pequeños sin lanzar Chrome.
- [Líneas 61–69](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L61-L69): instala el recorrido simulado como vista cruda y registra su retirada al terminar la prueba.
- [Líneas 71–140](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L71-L140): prueba listas ordinarias, grupos muchos-a-muchos, envolturas, estructuras mezcladas, alternativas de roles, roles explícitos, envolturas demasiado profundas y grupos incompletos.
- [Líneas 142–155](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L142-L155): comprueba que las listas interiores tienen conteos independientes.
- [Líneas 157–167](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L157-L167): comprueba que un rol explícito del contenedor impide una detección indebida, y que se admiten alternativas hasta encontrar `list`.
- [Líneas 169–204](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L169-L204): prueba la construcción del campo, su rol y tamaño, la conservación de estados y la retirada de información temporal.
- [Líneas 206–230](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L206-L230): comprueba los conteos compartidos por términos, el cero del término huérfano y la independencia de listas interiores, con y sin envolturas.
- [Líneas 232–245](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L232-L245): comprueba que definiciones en envolturas hermanas pueden asociarse al término previo según el recorrido implementado.
- [Líneas 247–258](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L247-L258): comprueba que varios párrafos no se cuentan como varias definiciones y que `description` no sustituye a `definition`.
- [Líneas 260–264](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L260-L264): fuerza un error COM y exige descartar el conteo parcial.
- [Líneas 266–271](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L266-L271): cambia el número de definiciones y exige recalcularlo, sin reutilizar el número anterior.
- [Líneas 274–283](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L274-L283): una lista ordinaria mantiene su elemento y nombre.
- [Líneas 285–300](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L285-L300): los términos pierden el nombre duplicado y la información temporal se consume.
- [Líneas 302–335](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L302-L335): prueba listas ordinarias y descriptivas anidadas para que cada una conserve su semántica.
- [Líneas 337–349](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L337-L349): un intervalo con solo el segundo término, sin ninguna definición dentro, sigue obteniendo el conteo completo por su identificador.
- [Líneas 351–366](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L351-L366): los conteos exteriores no se filtran a la lista interior.
- [Líneas 368–377](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L368-L377): un botón explícito dentro de la estructura no se convierte en término ni recibe conteo.
- [Líneas 380–414](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L380-L414): prueba roles y tamaños de campos nativos para `dl`, `ul`, `ol` y roles explícitos o desconocidos.
- [Líneas 416–431](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L416-L431): comprueba el rol del objeto IA2, no solo el del campo de texto.
- [Líneas 433–454](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L433-L454): hace lo equivalente en MSHTML con y sin ancestro accesible.
- [Líneas 456–464](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L456-L464): confirma que el filtro nativo para navegar por listas continúa incluyendo las listas descriptivas.

**Límite:** estos dobles permiten aislar errores de lógica, pero no prueban qué árbol publica una versión real del navegador ni ejecutan el contador C++.

### 6.4. Pruebas reales de Chrome

**Archivo modificado:** [tests/system/robot/chromeTests.py](../../tests/system/robot/chromeTests.py).

Se añade el bloque [887–1019](../../tests/system/robot/chromeTests.py#L887-L1019), con dos funciones y sus separadores:

- [Líneas 887–940](../../tests/system/robot/chromeTests.py#L887-L940): `test_definitionList_semantics()` abre el ejemplo Student/Staff/Teacher/Color/Colour, comprueba cinco saltos con `i` y la lectura por líneas hasta salir del contenedor. Incluye el anuncio actual y las dos definiciones compartidas.
- [Líneas 943–970](../../tests/system/robot/chromeTests.py#L943-L970): `test_definitionList_counts()` selecciona IA2 o UIA y construye una página con sinónimos, varios párrafos, una lista descriptiva interior, una lista ordinaria interior y un botón que retira o reinserta una definición. El parámetro `wrapped` permite repetirla con envolturas.
- [Líneas 971–988](../../tests/system/robot/chromeTests.py#L971-L988): comprueba navegación por listas en ambos sentidos, tamaños y braille, que la lista ordinaria no se anuncie como descriptiva y que salir del contenedor llegue al botón.
- [Líneas 989–1001](../../tests/system/robot/chromeTests.py#L989-L1001): comprueba términos y sus cantidades, incluidos los casos de una sola definición.
- [Líneas 1002–1019](../../tests/system/robot/chromeTests.py#L1002-L1019): retira y reinserta una definición y comprueba que los dos términos compartidos pasan de dos a una y de una a dos, sin refrescar manualmente el búfer; incluye los separadores finales.

El ejemplo de la primera función mezcla hijos directos y envueltos deliberadamente como prueba de recuperación de estructura.
No debe tomarse como demostración de que esa mezcla sea el modelo HTML recomendado.

### 6.5. Registro de los casos Chrome en Robot Framework

**Archivo modificado:** [tests/system/robot/chromeTests.robot](../../tests/system/robot/chromeTests.robot).

Robot Framework organiza y ejecuta pruebas de sistema.
El archivo Python anterior contiene las acciones; este archivo declara qué casos se ejecutan y con qué parámetros.

- [Líneas 49–52](../../tests/system/robot/chromeTests.robot#L49-L52): registra el caso básico de semántica.
- [Líneas 53–60](../../tests/system/robot/chromeTests.robot#L53-L60): registra conteos directos y con envolturas por el camino IA2.
- [Líneas 61–68](../../tests/system/robot/chromeTests.robot#L61-L68): registra las dos variantes con UIA forzada.

Son cinco casos nuevos, etiquetados `chrome_list`.
Esa etiqueta también selecciona cuatro casos de listas que ya existían: **no equivale exclusivamente a estas cinco pruebas**.
Los títulos conservan «Definition list» por historia; sus expectativas de anuncio son «description list».

### 6.6. Automatización real de Firefox y MSHTML

**Archivo nuevo completo:** [tests/system/robot/descriptionListTests.py](../../tests/system/robot/descriptionListTests.py), 218 líneas.

- [Líneas 1–26](../../tests/system/robot/descriptionListTests.py#L1-L26): cabecera, explicación e importaciones para archivos temporales, procesos, registro de Windows y control de ventanas.
- [Líneas 27–35](../../tests/system/robot/descriptionListTests.py#L27-L35): mantiene la identidad del proceso, ventana y carpeta creados por la prueba.
- [Líneas 37–51](../../tests/system/robot/descriptionListTests.py#L37-L51): localiza Firefox por una ruta indicada o por su registro en Windows. Si no existe, la prueba falla explícitamente.
- [Líneas 53–86](../../tests/system/robot/descriptionListTests.py#L53-L86): genera un documento temporal con el ejemplo de conteos, versiones con o sin envolturas y el botón que modifica la página.
- [Líneas 87–102](../../tests/system/robot/descriptionListTests.py#L87-L102): inicia Firefox con perfil temporal separado o el motor MSHTML mediante `mshta.exe`; no utiliza el perfil personal de Firefox.
- [Líneas 103–125](../../tests/system/robot/descriptionListTests.py#L103-L125): localiza la ventana, intenta darle foco y coloca la lectura en la página. Incluye tratamiento de un menú que podría abrirse al activar la ventana.
- [Líneas 126–137](../../tests/system/robot/descriptionListTests.py#L126-L137): busca en el registro de NVDA la creación del backend esperado. No da por hecho que se usó Gecko o MSHTML solo por el nombre del ejecutable.
- [Líneas 139–156](../../tests/system/robot/descriptionListTests.py#L139-L156): comprueba listas exteriores, interiores y ordinarias, navegación en ambos sentidos, braille y salida al botón.
- [Líneas 157–176](../../tests/system/robot/descriptionListTests.py#L157-L176): comprueba términos, conteos compartidos, navegación inversa y lectura por líneas de un término y una definición.
- [Líneas 177–189](../../tests/system/robot/descriptionListTests.py#L177-L189): retira y reinserta una definición y verifica cantidades y supresión del anuncio cuando queda solo una.
- [Líneas 191–218](../../tests/system/robot/descriptionListTests.py#L191-L218): cierra el host creado, espera su terminación y limpia los archivos; reintenta de forma acotada si Firefox todavía tiene archivos temporales bloqueados.

**Por qué hay tanto código de preparación:** una prueba de escritorio necesita un navegador disponible, una ventana identificable y el foco correcto antes de poder comprobar la funcionalidad.
Un fallo aquí puede impedir probar el producto sin demostrar un fallo del contador.
MSHTML se prueba como motor alojado en una aplicación HTML local; esto no equivale a probar la aplicación Internet Explorer ni el modo IE de Edge.

### 6.7. Registro de los casos Firefox y MSHTML

**Archivo nuevo completo:** [tests/system/robot/descriptionListTests.robot](../../tests/system/robot/descriptionListTests.robot), 34 líneas.

- [Líneas 1–10](../../tests/system/robot/descriptionListTests.robot#L1-L10): cabecera, bibliotecas y preparación/limpieza de cada caso con una instancia de prueba de NVDA.
- [Líneas 12–17](../../tests/system/robot/descriptionListTests.robot#L12-L17): vuelca voz y braille al registro, cierra el host y sale de NVDA. Intenta continuar las tareas de limpieza aunque una falle.
- [Líneas 19–26](../../tests/system/robot/descriptionListTests.robot#L19-L26): dos casos Firefox: grupos directos y envueltos.
- [Líneas 28–34](../../tests/system/robot/descriptionListTests.robot#L28-L34): dos casos MSHTML equivalentes.

Son optativos mediante las etiquetas `description_lists_firefox` y `description_lists_mshtml`.
No se incorporan a la etiqueta general `NVDA`, porque no todas las máquinas de pruebas disponen de esos hosts.

## 7. Documentos y ejemplo manual

### 7.1. Instrucciones de pruebas de sistema

**Archivo modificado:** [tests/system/readme.md](../../tests/system/readme.md).

Se añade [el bloque 34–50](../../tests/system/readme.md#L34-L50):

- Qué etiquetas seleccionan Firefox y MSHTML.
- Cómo indicar una ruta alternativa de Firefox y qué aislamiento se usa.
- Qué significa probar MSHTML mediante una aplicación HTML local.
- Qué comprueban los casos y cómo limpian sus recursos.
- Advertencia de no usar el teclado mientras corren: necesitan el foco y pueden interrumpir la instancia de prueba de NVDA.

**Por qué aquí:** quien ejecute la batería necesita estas condiciones sin leer todo su código.

### 7.2. Novedades para usuarios y desarrolladores

**Archivo modificado:** [user_docs/en/changes.md](../../user_docs/en/changes.md).

- [Líneas 20–24](../../user_docs/en/changes.md#L20-L24): resumen del cambio observable: contenedor, braille, grupos, conteos por término y navegación; incluye el separador final.
- [Líneas 36–40](../../user_docs/en/changes.md#L36-L40): documenta los dos roles nuevos y `definition-count`; aclara que el rol es interno y explica las limitaciones de detección UIA, incluida la conservación del rol del objeto; incluye el separador.

La primera parte sirve a quien utiliza NVDA; la segunda, a quien mantiene complementos o código que consume esos campos.
No basta con que el código compile: introducir una propiedad o cambiar los roles observados es información relevante para otros desarrolladores.

### 7.3. Guía de usuario

**Archivo modificado:** [user_docs/en/userGuide.md](../../user_docs/en/userGuide.md).

El bloque añadido [1083–1089](../../user_docs/en/userGuide.md#L1083-L1089) explica la navegación por términos y listas, el anuncio del contenedor, el ajuste de informar listas, el conteo compartido y la independencia de las listas anidadas; incluye el separador final.

Se coloca junto a las instrucciones de navegación del modo exploración porque ahí buscará esta información quien use el lector.
No crea atajos nuevos ni otro panel de configuración.

### 7.4. Página HTML para probar a mano

**Archivo nuevo completo:** [projectDocs/issues/3858-prueba-manual.html](3858-prueba-manual.html), 28 líneas.

- [Líneas 1–7](3858-prueba-manual.html#L1-L7): identifica el documento HTML, idioma, codificación y título.
- [Líneas 8–10](3858-prueba-manual.html#L8-L10): abre el cuerpo, explica que la mezcla de estructuras es deliberada y añade el encabezado.
- [Líneas 11–13](3858-prueba-manual.html#L11-L13): abre la lista y añade Student → Judy.
- [Líneas 14–19](3858-prueba-manual.html#L14-L19): grupo Staff y Teacher → Melissa y Robin.
- [Líneas 20–24](3858-prueba-manual.html#L20-L24): grupo Color y Colour → A visual characteristic.
- [Líneas 25–28](3858-prueba-manual.html#L25-L28): cierra la lista y añade «After list» para poder comprobar la salida del contenedor.

Este archivo **no modifica NVDA**: es material de entrada para observarlo.
No contiene un botón de cambios dinámicos ni listas anidadas; esos escenarios pertenecen a las pruebas de sistema.
Tiene tres grupos y cinco destinos de término, y reproduce una estructura mixta de recuperación, no una recomendación de autoría HTML.

### 7.5. Explicación histórica de la incidencia

**Archivo nuevo completo:** [projectDocs/issues/3858-explicacion.es.md](3858-explicacion.es.md), 352 líneas.

- [Líneas 1–28](3858-explicacion.es.md#L1-L28): alcance, advertencias sobre versiones y resultados de pruebas, e índice.
- [Líneas 29–62](3858-explicacion.es.md#L29-L62): problema, semántica HTML y decisiones locales.
- [Líneas 63–161](3858-explicacion.es.md#L63-L161): estado consultado de la incidencia, copia local, proveedores y evidencia de pruebas.
- [Líneas 162–231](3858-explicacion.es.md#L162-L231): los 31 comentarios recuperados y cómo evolucionó la discusión.
- [Líneas 232–311](3858-explicacion.es.md#L232-L311): recorrido de datos, conteo, duplicación de nombres y orientación para el anexo anterior.
- [Líneas 312–352](3858-explicacion.es.md#L312-L352): límites, fuentes y método de revisión.

**Por qué existe:** conserva la investigación y separa lo que se propuso en la incidencia de lo que se decidió implementar localmente.
Su información de GitHub es una consulta histórica; no se ha vuelto a consultar GitHub al redactar esta guía.
No es una parte que se ejecute al arrancar NVDA.

### 7.6. Anexo antiguo con el diff comentado

**Archivo nuevo completo:** [projectDocs/issues/3858-diff-comentado.es.md](3858-diff-comentado.es.md), 1771 líneas.

**Atención: es histórico. No lo uses como mapa de las líneas actuales.**
Reproduce una versión inicial anterior al contador compartido definitivo, a los conteos por término y al nuevo rol del contenedor.
Por eso puede mostrar nombres añadidos en cabeceras, funciones antiguas y cifras de líneas que ya no coinciden con el parche actual.
Conservar una transcripción histórica no significa volver a aplicar esos cambios al código.

- [Líneas 1–64](3858-diff-comentado.es.md#L1-L64): alcance histórico, formato, cifras de aquella versión y mapa arquitectónico.
- [Líneas 65–602](3858-diff-comentado.es.md#L65-L602): antiguo backend IA2, mapa MSHTML y primera implementación UIA.
- [Líneas 603–988](3858-diff-comentado.es.md#L603-L988): roles, braille, presentación y navegación de aquella versión.
- [Líneas 989–1317](3858-diff-comentado.es.md#L989-L1317): pruebas y novedades de entonces.
- [Líneas 1318–1735](3858-diff-comentado.es.md#L1318-L1735): primera versión del archivo unitario UIA, no sus 464 líneas actuales.
- [Líneas 1736–1771](3858-diff-comentado.es.md#L1736-L1771): límites y método de comprobación de aquel documento.

**Por qué no se ha reescrito aquí:** hacerlo borraría la separación entre versiones que el propio anexo declara.
La presente guía es el mapa actualizado solicitado para aprender el código actual.

### 7.7. Esta guía

**Archivo nuevo:** [projectDocs/issues/3858-guia-del-cambio.es.md](3858-guia-del-cambio.es.md).

Todo su contenido se añade ahora.
Su función es reunir el inventario actual, explicar cada bloque y enlazarlo con el código, sin obligarte a leer antes el historial de la incidencia ni el anexo antiguo.
No modifica el comportamiento del producto.

## 8. Qué está comprobado y qué sigue pendiente

Esta sección describe el registro de trabajo de la sesión, **no pruebas nuevas ejecutadas al escribir esta guía**.

### Comprobaciones que sí constan

- Se compilaron los helpers nativos x64 y x86 durante la implementación del conteo.
- Pasaron las suites específicas de presentación, proveedores y TextInfo, con totales comunicados de 73, 82 y 101 pruebas respectivamente; esos totales incluyen las pruebas comunes de inicialización, no son todos casos nuevos de esta funcionalidad.
- Tras cambiar el anuncio a «description list», se repitió la suite de presentación: 73 pruebas correctas.
- Constan comprobaciones correctas de Ruff, tipos con Pyright y ty, cadenas traducibles POT y Markdown en las etapas indicadas en el historial.
- La actualización posterior de cabeceras se comprobó como cambio de comentarios, sin modificación de la lógica.

### Lo que no debe darse por aprobado

- Los cinco casos Chrome y los cuatro Firefox/MSHTML que pasaron anteriormente validaban la versión de conteos **anterior a `DESCRIPTIONLIST`**. No certifican automáticamente la versión actual del contenedor y sus anuncios.
- Los intentos posteriores de pruebas reales quedaron bloqueados por foco, notificaciones y acceso al escritorio; hubo también «BitBlt: Access is denied» al capturar la pantalla. Hay que repetirlos en un escritorio disponible.
- La suite general de voz ejecutada aisladamente tuvo dos fallos con sintetizador sin inicializar; el intento de usar el sintetizador silencioso también falló. Sin una referencia comparable no se atribuyen esos fallos al parche ni se consideran resueltos.
- La batería unitaria completa previa no estaba verde; hubo fallos relacionados con tablas braille y dependencias. No se ha demostrado una referencia limpia para todos ellos.
- No se ha validado con un dispositivo braille físico ni se ha añadido cobertura nueva para PDF.
- Las cadenas nuevas son traducibles, pero eso no implica que ya exista una traducción española incorporada.

No confundir tres afirmaciones distintas: «la prueba está escrita», «la prueba se ejecutó» y «la prueba pasó con esta versión exacta».

## 9. Por dónde empezar si quieres tocar el código tú

### Si quieres cambiar una palabra

Empieza por [las etiquetas de roles](../../source/controlTypes/role.py#L240-L241) para voz y por [las etiquetas braille](../../source/braille/labels.py#L45-L46).
Después revisa las expectativas en [la suite de presentación](../../tests/unit/test_descriptionLists.py#L114-L153), las pruebas de sistema y la documentación.
No necesitas empezar por C++ para cambiar «description list» por otro anuncio.

### Si el número de grupos es incorrecto

Primero identifica el camino utilizado por el navegador.
Para IA2 o MSHTML, estudia [el contador C++](../../nvdaHelper/vbufBase/utils.cpp#L24-L75) y después el normalizador correspondiente.
Para Chromium UIA, estudia [el recorrido de vista cruda](../../source/NVDAObjects/UIA/chromium.py#L43-L105).
No intentes arreglar la cifra únicamente en voz: braille seguiría recibiendo el dato incorrecto.

### Si el conteo del término es correcto al leer la página completa, pero no con I

Piensa en un intervalo parcial: quizá el término está en el fragmento leído y sus definiciones no.
Mira [la asignación UIA por identificador](../../source/NVDAObjects/UIA/chromium.py#L108-L138) y [su prueba específica](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L337-L349).

### Si I salta al sitio equivocado

Revisa los filtros de navegación, no solo el rol anunciado:

- [Filtro IA2](../../source/virtualBuffers/gecko_ia2.py#L464-L471).
- [Filtro MSHTML](../../source/virtualBuffers/MSHTML.py#L435).
- [Filtro UIA](../../source/NVDAObjects/UIA/chromium.py#L220-L234).

### Si se oye el término dos veces

Puede estar llegando como `name` y como contenido.
Revisa [la normalización IA2](../../source/virtualBuffers/gecko_ia2.py#L142-L143) y [la normalización UIA](../../source/NVDAObjects/UIA/chromium.py#L108-L138).
Eliminar un nombre duplicado no debe confundirse con eliminar el texto que la persona necesita leer.

### Si quieres una primera prueba manual sencilla

Abre [el ejemplo manual](3858-prueba-manual.html) con el NVDA del repositorio.
Comprueba entrada a la lista, cinco saltos de términos, dos definiciones para Staff y Teacher, y salida hacia «After list».
Para arrancar, el script disponible es [runnvda.bat](../../runnvda.bat); no se ha modificado en este parche.
En esta máquina fue necesario permitir el Python gestionado mediante `UV_PYTHON_PREFERENCE=managed`, porque la preferencia del proyecto por Python del sistema impedía encontrar la versión requerida.
Eso es un problema del entorno de ejecución, independiente de cómo se cuentan las listas.

## 10. Resumen en una frase por capa

1. **Roles:** dar un nombre interno distinto a lista descriptiva y término.
2. **Proveedores:** reconocer esos conceptos en los datos que entrega cada motor.
3. **Conteos:** calcular grupos y definiciones compartidas, sin contar párrafos ni listas interiores.
4. **Normalización:** transportar los resultados en campos comunes y evitar duplicados.
5. **Navegación:** encontrar términos sin convertir las definiciones en paradas adicionales.
6. **Voz y braille:** presentar la misma información, respetando la configuración.
7. **Pruebas:** detectar regresiones y distinguir lógica simulada de comportamiento real de escritorio.
8. **Documentación:** explicar lo que cambia, cómo probarlo y qué sigue sin verificar.

La cantidad de archivos no significa que se hayan hecho 31 arreglos independientes: son las piezas que conectan una misma semántica desde el navegador hasta la salida accesible y sus comprobaciones.
