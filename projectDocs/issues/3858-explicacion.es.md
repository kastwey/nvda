<!-- markdownlint-configure-file {"MD004": {"style": "dash"}, "MD050": {"style": "asterisk"}} -->

# NVDA #3858: explicación, estado, histórico y código

Instantánea del **12 de septiembre de 2026**, sobre [#3858: Definition lists not exposed correctly](https://github.com/nvaccess/nvda/issues/3858).

El entregable se divide en esta explicación general y [3858-diff-comentado.es.md](3858-diff-comentado.es.md), que reproduce y explica cada línea del **parche inicial**.
Ese anexo es una instantánea histórica: no representa el diff actual tras añadir el anuncio de definiciones por término y el rol de contenedor `Role.DESCRIPTIONLIST`.
Este documento incorpora ambas ampliaciones, sin atribuirlas retroactivamente al anexo.
Los resultados de navegadores aprobados corresponden a la ampliación de conteos anterior al nuevo rol; no acreditan una ejecución aprobada con `DESCRIPTIONLIST`.
Las pruebas unitarias del nuevo contenedor sí se han ejecutado: presentación (73), proveedores (82) y TextInfo (101), todas correctas; los totales incluyen pruebas de arranque.
La repetición de pruebas reales quedó bloqueada por el escritorio: foco retenido por una notificación, activación de ventanas rechazada y, finalmente, `BitBlt: Access is denied` al capturar la pantalla.
Debe repetirse esa validación en un escritorio interactivo disponible; no se considera aprobada por los resultados de la versión anterior.
La comprobación adicional de roles pasó (73 pruebas), al igual que Ruff, Pyright, ty y POT.
La suite de voz ejecutada aisladamente tuvo dos fallos en los puntos de extensión de pausa/cancelación, con el sintetizador sin inicializar; el intento de inicializar el sintetizador silencioso también falló.
No se considera aprobada esa suite ni se atribuyen esos fallos al cambio sin una ejecución de referencia.

## Índice

1. [La issue](#1-la-issue).
2. [Estado actual](#2-estado-actual).
3. [Los 31 comentarios](#3-los-31-comentarios).
4. [Del requisito al diseño y al diff](#4-del-requisito-al-diseño-y-al-diff).
5. [Limitaciones](#5-limitaciones).
6. [Fuentes y comprobación](#6-fuentes-y-comprobación).

**Alcance:** explicar una línea no demuestra que sea infalible. Se separan propuestas históricas, decisiones locales, hechos del código y evidencia de pruebas. Este informe no cambia la implementación ni presenta el parche como una solución aceptada por NV Access.

## 1. La issue

### 1.1. Semántica y problema práctico

WHATWG denomina `dl` **description list**: una lista descriptiva de grupos de asociaciones nombre-valor. No se limita a un diccionario: puede representar nombres y valores, preguntas y respuestas o metadatos. `dt` aporta un nombre o término; `dd`, un valor o descripción asociado.

La semántica HTML, los roles de las APIs de accesibilidad y las etiquetas de NVDA son niveles distintos.
[ARIA in HTML](https://www.w3.org/TR/html-aria/#el-dl) indica **No corresponding role** para `dl`, y también para `dt` y `dd`; `dfn`, en cambio, corresponde a `term`.
Eso no elimina la semántica HTML ni impide su exposición mediante las APIs de accesibilidad.
El [índice actual de roles WAI-ARIA](https://w3c.github.io/aria/#role_definitions) no incluye `associationlist`: su mención en el comentario de 2022 se conserva como referencia histórica, no como un estándar vigente establecido.
`Role.DESCRIPTIONLIST` es un enum interno de NVDA, no un token válido que este cambio añada a ARIA.

La relación es **muchos a muchos**. Varios `dt` consecutivos pueden compartir varios `dd` consecutivos. Student → Judy y Teacher → Melissa son cuatro hijos HTML, pero dos grupos. Staff, Teacher → Melissa, Robin son también cuatro hijos, pero **un grupo**. Dividir el número de hijos entre dos no sirve en general.

Color, Colour → A visual characteristic contiene dos términos y un grupo. Por tanto, número de grupos, número de términos y número de pulsaciones de I son magnitudes distintas.

El cuerpo actual de #3858 contiene una lista exterior con cinco grupos y una interior con dos. La salida allí reproducida anuncia **11 elementos** fuera y **4 elementos** dentro: suma términos y definiciones en lugar de asociaciones. Tampoco comunica sus papeles diferenciados. Según el mismo cuerpo, I recorre solo `dt`, lo que agrava la incoherencia entre el conteo y los destinos disponibles.

La consecuencia no es meramente terminológica: si el contenido no resulta obvio, una persona que escucha no sabe dónde acaba un nombre y empieza su valor. La sangría, alineación y tipografía suelen distinguirlos visualmente; esa información debe sobrevivir al recorrido por las APIs de accesibilidad.

### 1.2. Expectativas históricas frente a alcance local

El cuerpo de la issue reúne propuestas **expresamente abiertas a discusión**: anunciar «Description List», contar `dt`, anunciar «Term», indicar cuántas definiciones tiene un término, expresar anidamiento y relaciones y evitar sumar indiscriminadamente `dt` y `dd`.

No es una especificación cerrada. Contar `dt` no equivale a contar asociaciones cuando hay sinónimos. Leer un grupo entero con I no equivale a visitar cada término. Implementar una alternativa no satisface automáticamente las demás.

La petición local inicial concretó: **contenedor como lista; términos y definiciones diferenciados; conteo de asociaciones completas; I solo por términos dentro de estas listas**.
Después se amplió expresamente para anunciar el número de definiciones de cada término cuando supera uno, en voz y braille.
Todos los términos de un mismo grupo reciben el mismo conteo; los párrafos de una definición y las definiciones de listas anidadas no lo incrementan.
Se añadió `Role.DESCRIPTIONLIST = 160` para distinguir el contenedor de una lista ordinaria, inicialmente con la cadena inglesa «definition list» y la abreviatura braille «dlst».
La petición más reciente cambia el anuncio a «description list», coherente con HTML actual; el identificador, la abreviatura braille y el comportamiento se mantienen.
Ese anuncio responde a una decisión local, no a un consenso de la issue ni a una frase que los estándares obliguen a pronunciar.
Se mantienen L/shift+L para listas, I/shift+I para términos y ambos conteos; no se crean objetos sintéticos de asociación.

## 2. Estado actual

### 2.1. GitHub

La API pública consultada durante esta redacción devuelve:

- Estado **abierta**, sin fecha de cierre.
- Creada el **7 de febrero de 2014**; última actualización el **5 de febrero de 2026 a las 02:08:04 UTC**.
- **31 comentarios** recuperados completos; la segunda página está vacía.
- Etiquetas `p3`, `app/chrome`, `feature`, `app/firefox`, `app/edge/anaheim`, `triaged`.
- Sin personas asignadas y sin hito.

La issue y dos comentarios migrados figuran como `nvaccessAuto`; los textos de esos comentarios identifican a los autores originales. No se atribuye al bot su opinión.

«Todos los comentarios» significa los 31 de #3858. No se ha reconstruido la cronología de todos los eventos de GitHub ni cada discusión de las issues duplicadas. Tampoco se infiere aquí que exista o no una PR relacionada.

### 2.2. Copia local

Rama comprobada: `fix/description-lists-3858`. Base: `c43cf6c1b0518326bd9ff0ed4712474feeb6131c`.

El parche inicial comprendía 14 archivos, con 500 líneas añadidas y 19 eliminadas.
La ampliación supera esas cifras: incorpora un helper C++ compartido, presentación, documentación y más pruebas.
Las pruebas nuevas no seguidas por Git deben incluirse al calcular el alcance; un diff ordinario las omite.

Los cambios permanecen en la copia de trabajo, sin crear commits, publicar ramas ni cerrar la issue.
El tamaño ampliado debe revisarse con los mantenedores; no se presenta como un parche limitado a 500 líneas.

Se preservan las modificaciones ajenas de espeak, liblouis y nvda-cldr y el directorio no seguido nvda_dmp. No forman parte del diff explicado.

### 2.3. Qué cambia realmente por backend

| Recorrido | Implementación presente | Evidencia y límites |
| --- | --- | --- |
| Gecko/IA2, compartido con Chromium IA2 | Contenedor nativo `dl` como `DESCRIPTIONLIST`; conteo nativo de grupos y definiciones por término; normalización `dt`/`dd`; limpieza de nombres; filtro I | Pruebas anteriores al nuevo rol: Chrome IA2 y Firefox 155.0.1 reales, incluidos cambios dinámicos |
| Chromium UIA | Normalización del campo de texto a `DESCRIPTIONLIST` a partir de la vista cruda, sin cambiar el rol del objeto; conteos por runtime ID y rangos parciales | Pruebas anteriores al nuevo rol: Chrome real con UIA forzada, incluidos párrafos, anidamiento y cambios dinámicos; no distingue `dl` de `role="list"` con descendientes idénticos |
| MSHTML | Contenedor nativo `dl` como `DESCRIPTIONLIST`, roles de hijos y navegación; helper C++ compartido para ambos conteos | Pruebas anteriores al nuevo rol: `mshta.exe`, HTA local en modo `IE=edge`, compilación x64/x86 y tests del normalizador |
| Presentación común | Contenedor «description list»/«dlst»; voz «with 2 definitions» y braille «trm 2 defs» cuando el conteo supera uno; respeta `reportLists` | Las capturas y tests anteriores acreditan los conteos, no la nueva etiqueta del contenedor; sin dispositivo braille físico |

El conteo ahora está implementado en los tres recorridos, pero eso no demuestra paridad de todos los navegadores y proveedores.

#### Roles y ejemplos esperados tras el cambio de contenedor

- Contenedor: `Role.DESCRIPTIONLIST = 160`; término: `Role.TERM = 159`; definición: `Role.DEFINITION`, ya existente. Los valores numéricos previos no se renumeran.
- Student → Judy y Teacher → Melissa: dos grupos; entrada esperada en inglés «description list with 2 items», con «dlst» como marcador braille del contenedor. Cada término tiene una definición, por lo que no se anuncia su cantidad.
- Staff, Teacher → Melissa, Robin: un grupo y dos destinos I. Cada término conserva «with 2 definitions» en voz y «trm 2 defs» en braille; no se convierte en dos grupos.
- Color, Colour → A visual characteristic: un grupo y dos destinos I, sin anuncio de cantidad por término porque ambos comparten una sola definición.

Son ejemplos esperados, no capturas nuevas de ejecución. Las cadenas inglesas son localizables mediante el flujo habitual de traducción de NVDA; no se promete que una traducción nueva al español esté instalada o terminada.

### 2.4. Pruebas y nivel de certeza

Para la ampliación de conteos, **antes de añadir `DESCRIPTIONLIST`**, se recompilaron e instalaron los helpers x64/x86 y se ejecutaron:

- **Cinco casos Robot, todos pasados:** semántica básica y conteos con/sin envolturas en IA2 y UIA.
- **72 tests** en la invocación de normalización/presentación y **75** en la de Chromium UIA, todos pasados; incluyen bootstrap y no son 147 pruebas nuevas distintas.
- Los casos reales comprueban dos términos con dos definiciones compartidas, una definición con dos párrafos, una lista anidada con tres definiciones y un término con una sola definición.
- También comprueban retirar/reinsertar una definición: el anuncio cambia de dos a una (sin anunciar cantidad) y vuelve a dos.
- Un listener local temporal ayudó a enfocar Chrome en este escritorio; no forma parte del parche y se retiró después.

La prueba UIA detectó y permitió corregir dos errores: usar la vista de controles contaba párrafos en vez de contenedores `definition`; braille no aceptaba un conteo entero de lista.
La vista cruda conserva los contenedores. El rol UIA `description` identifica texto estático y ya no se utiliza como señal de definición.
Los informes bajo `testOutput` se sobrescriben entre ejecuciones.

### 2.5. Validación posterior en Firefox y MSHTML

Esta validación también es anterior al cambio de rol del contenedor; «posterior» se refiere a la primera entrega de conteos, no a `DESCRIPTIONLIST`.
La primera entrega omitió pruebas reales en estos motores; se añadió después una suite reproducible para cubrir esa carencia.
La ejecución conjunta final superó **cuatro casos de cuatro**, incluido el cierre y la limpieza:

| Motor real | Grupos directos | Grupos con `div` | Identidad comprobada en el registro |
| --- | --- | --- | --- |
| Firefox 155.0.1, instalado desde Microsoft Store | Pasado | Pasado | `virtualBuffers.gecko_ia2.Gecko_ia2`, proceso Firefox |
| MSHTML de Windows, alojado por `mshta.exe` | Pasado | Pasado | `virtualBuffers.MSHTML.MSHTML`, ventana `Internet Explorer_Server` |

Cada caso comprueba voz, texto braille, dos términos que comparten dos definiciones, una definición con dos párrafos, una lista anidada con tres definiciones y un término con una sola definición.
También comprueba I y shift+I, lectura de roles por líneas y retirada/reinserción de una definición: dos → una → dos, sin refrescar manualmente el buffer.
No fue necesario modificar el código del producto para superar estos casos.

Los primeros intentos detectaron problemas del arnés: foco inicial de Firefox y archivos que sus procesos secundarios retenían/recreaban durante el cierre del perfil temporal.
Se corrigieron y se repitió la suite completa.
Otra ejecución se interrumpió por entradas externas de teclado y el arranque de otra instancia de NVDA; no se contabiliza como una prueba superada.

La suite y su lógica están en [descriptionListTests.robot](../../tests/system/robot/descriptionListTests.robot) y [descriptionListTests.py](../../tests/system/robot/descriptionListTests.py).
Las [instrucciones para repetirla](../../tests/system/readme.md#description-lists-in-firefox-and-mshtml) especifican los tags, la ruta alternativa de Firefox y el aislamiento del perfil.
MSHTML aquí significa el motor dentro de un HTA local; no acredita la aplicación Internet Explorer, el modo IE de Edge ni todos los modos de documento históricos.

El historial de implementación anterior comunicó los resultados siguientes. No se presentan como nuevas ejecuciones de esta redacción:

| Comprobación anterior | Resultado comunicado | Precisión |
| --- | --- | --- |
| Invocaciones Chromium, textInfos y controlTypes | 68, 101 y 73 tests; 242 ejecuciones sumadas | No son 242 tests nuevos ni necesariamente casos distintos |
| Compilación/instalación nativa x64 y x86 | Correctas; última comprobación sin trabajo pendiente | No prueba todos los navegadores |
| Ruff, formato de Python cambiado, Pyright y ty | Correctos en su alcance | No prueban semántica de APIs |
| POT y licencias | Correctos, con errores esperados del comprobador POT | No implica traducciones terminadas |
| Suite unitaria completa | 1439 tests; 54 fallos, un error, cinco omitidos | **La suite completa no está verde** |
| Formato global | 48 archivos requerían formato; 752 correctos | No se modificaron archivos ajenos para ocultarlo |

Los fallos unitarios se localizaron entonces en tablas braille: 18 en `TestBrailleTables`, 36 en `TestTranslate` y un error en `TestResolvingInternal`. Se registró la ausencia de `ovd-6g0.utb` y una revisión local de liblouis distinta de la esperada. Esa explicación **no sustituye una comparación limpia antes/después** que demuestre causalidad de todos los fallos.

## 3. Los 31 comentarios

Se usan fechas de creación en UTC y el contenido actual completo. Los enlaces permiten volver al original. Las opiniones de participantes no se presentan como decisiones oficiales ni como pruebas realizadas aquí.

<!-- La numeración identifica los 31 comentarios de forma continua entre subsecciones. -->
<!-- markdownlint-disable MD029 -->

### 3.1. 2014–2019: necesidad y prioridad

1. **@bgaraventa**, importado como `nvaccessAuto`, [10 de febrero de 2014](https://github.com/nvaccess/nvda/issues/3858#issuecomment-155317296): pide distinguir `DT` y `DD` sin adivinar por el contenido. Ha usado ARIA para hacer la asociación más evidente, pero cree que no debería ser necesario. No proporciona la receta ARIA concreta.
2. **@jmuheim**, importado como `nvaccessAuto`, [7 de octubre de 2014](https://github.com/nvaccess/nvda/issues/3858#issuecomment-155317297): expresa acuerdo, sin requisitos técnicos nuevos.
3. **@bhavyashah**, [26 de agosto de 2017](https://github.com/nvaccess/nvda/issues/3858#issuecomment-325145713): propone considerarlo para Project Webfix y consulta a @feerrenrut. Es una propuesta de prioridad, no de código.
4. **@feerrenrut**, [29 de agosto de 2017](https://github.com/nvaccess/nvda/issues/3858#issuecomment-325588453): reproduce el fallo en `master-14328,c6379eb3`. Explica que Webfix aborda problemas especialmente molestos, no todos los defectos web. Entonces estima que estas listas aparecen poco y la semántica puede deducirse del contexto; no lo ve candidato. No afirma imposibilidad técnica ni corrección del comportamiento.
5. **@ArmandFrvr**, [6 de octubre de 2017](https://github.com/nvaccess/nvda/issues/3858#issuecomment-334829236): el soporte insuficiente le frena al cambiar una plantilla de `ul` a `dl`. Señala el coste de exigir ARIA adicional para HTML nativo.
6. **@derekriemer**, [6 de octubre de 2017](https://github.com/nvaccess/nvda/issues/3858#issuecomment-334846362): recomienda usar `dl` pese a la semántica imperfecta, por el beneficio para otros lectores y usuarios videntes. Distingue soporte incompleto de imposibilidad de uso.
7. **@Adriani90**, [23 de mayo de 2019](https://github.com/nvaccess/nvda/issues/3858#issuecomment-495367665): aporta usos en estadísticas, grandes bases de datos y SharePoint empresarial. Sugiere una opción de formato de documentos para mejorar eficiencia. Cuestiona la escasa frecuencia supuesta, sin aportar estadísticas de prevalencia.

### 3.2. 2020–2022: muchos-a-muchos y falta de plan

8. **@medeaoblongata**, [3 de marzo de 2020](https://github.com/nvaccess/nvda/issues/3858#issuecomment-594040992): recuerda que un término puede tener varias definiciones y varios términos compartir una. Los hijos pueden superar el doble de las entradas. Rechaza tratar `DT` y `DD` como `LI` equivalentes y señala la falta de paridad ARIA de entonces. Es el antecedente directo del conteo por grupos.
9. **@masi**, [31 de agosto de 2020](https://github.com/nvaccess/nvda/issues/3858#issuecomment-683764070): pregunta si el bloqueo es técnico o hay otros motivos; no establece una causa.
10. **@jenstrickland**, [5 de octubre de 2020](https://github.com/nvaccess/nvda/issues/3858#issuecomment-703758362): pide novedades y soporte comparable al que atribuye a JAWS y VoiceOver. La comparación es de la participante, no una medición de este informe.
11. **@talimarcus**, [12 de octubre de 2020](https://github.com/nvaccess/nvda/issues/3858#issuecomment-707371954): su equipo también está bloqueado y necesita conocer los planes próximos.
12. **@feerrenrut**, [14 de octubre de 2020](https://github.com/nvaccess/nvda/issues/3858#issuecomment-708445640): no hay planes entonces; ha mejorado la descripción para facilitar el trabajo. El cuerpo actual, por tanto, no debe tratarse como una copia intacta del informe de 2014.
13. **@brunopulis**, [18 de agosto de 2022](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1219692336): pregunta qué atributo ARIA se utilizó en 2014 y solicita ejemplo. No aparece una respuesta con ese ejemplo entre los comentarios recuperados.
14. **@Qchristensen**, [5 de octubre de 2022](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1267749683): reactiva el hilo tras una consulta de @mausmalone en Twitter. Confirma interés continuado, sin propuesta técnica nueva.
15. **@medeaoblongata**, [6 de octubre de 2022](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1269868947): enlaza el **borrador** ARIA 1.3 con `associationlist`, orientado a la paridad con `DL/DT/DD`, y menciona desacuerdo sobre los nombres largos. Es una referencia histórica, no prueba de estandarización, soporte de navegador ni inclusión en el parche.

### 3.3. 2023: estructura, envolturas y orden

16. **@paulGeoghegan**, [6 de septiembre de 2023](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1707540703): sigue oyendo solo «list with N items», sin información de los `dd`, y pregunta si se solucionó. Describe persistencia del síntoma, no todas las configuraciones.
17. **@YetiAnt**, [21 de septiembre de 2023](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1729358243): una entrada puede contener varios `DT` y `DD`; propone que un `DT` tras `DD` o `DL` inicia otra. Lo observa también en PDF. El parche local **no modifica PDF**.
18. **@ferdnyc**, [16 de diciembre de 2023](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1858738802): critica que la nomenclatura key/value pueda ocultar muchos-a-muchos. Detalla las envolturas `div` directas y el modelo «hijos directos o envueltos». Explica que una lista puede anidarse dentro del contenido de `dd` y técnicamente también de `dt`, cuyo contenido de flujo tiene restricciones; desaconseja este último uso. Una `dl` no debe ser hija directa de otra `dl`. Esta observación no autoriza profundidad arbitraria ni toda mezcla como HTML conforme.
19. **@masi**, [16 de diciembre de 2023](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1858802338): propone convertir multiplicidades en listas virtuales o agrupar varios términos en uno virtual para aproximarlas a clave-valor. **No se implementa aquí** esa transformación de estructura.
20. **@ferdnyc**, [16 de diciembre de 2023](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1858864142): coincide en buena parte, pero recuerda que el orden de grupos, nombres y valores puede ser significativo. Preferiría listas ordenadas antes que perderlo y cita instrucciones cuyo primer caso aplicable determina puntos. No debe reordenarse alfabéticamente ni fusionarse ignorando la secuencia.
21. **@masi**, [17 de diciembre de 2023](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1859276535): acepta que el orden importa. Hay acuerdo local en preservarlo, no una decisión oficial de convertir `dl` en `ol`.

### 3.4. 2024: concretar conteo y navegación

22. **@BogdanCerovac**, [1 de febrero de 2024](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1922111256): propone separar listas de un nivel de las anidadas para desbloquear lo habitual. Student/Judy y Teacher/Melissa producen cuatro elementos sin relación semántica. Advierte que inferirla por contexto puede ser insuficiente. Ese vocabulario reaparece en el test local ampliado.
23. **@ferdnyc**, [3 de febrero de 2024](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1925415127): espera dos entradas tanto con un valor como con varios por término. Pregunta si Student/Judy más Staff,Teacher/Melissa debe contar dos o tres. Identifica la ambigüedad entre **grupos y términos**; el conteo local opta por dos grupos.
24. **@jenstrickland**, [3 de febrero de 2024](https://github.com/nvaccess/nvda/issues/3858#issuecomment-1925436622): propone anunciar términos y, en cada uno, el número de elementos asociados. Pregunta si debe aclararse con W3C HTML/AGWG o decidirlo navegadores y tecnologías de apoyo. La ampliación local implementa el conteo por término **cuando supera uno**, respetando las definiciones compartidas.
25. **@Adriani90**, [20 de octubre de 2024](https://github.com/nvaccess/nvda/issues/3858#issuecomment-2425180989): no considera necesario anunciar tipo de lista ni papeles término/definición; ve valores como subelementos y pide dos elementos, no cuatro. El parche mantiene «lista» y corrige conteo, pero **no adopta** la omisión de roles.
26. **@Adriani90**, [20 de octubre de 2024](https://github.com/nvaccess/nvda/issues/3858#issuecomment-2425182534): propone que I lea término y todos sus valores, como Students: Judy, Robin. **No es el comportamiento local**: I visita cada término sin leer automáticamente el grupo entero.
27. **@medeaoblongata**, [27 de octubre de 2024](https://github.com/nvaccess/nvda/issues/3858#issuecomment-2440075940): Color/Colour comparten definición y Console tiene dos. Propone dos grupos, descartando contar cada término o cada definición de forma independiente.
28. **@Adriani90**, [27 de octubre de 2024](https://github.com/nvaccess/nvda/issues/3858#issuecomment-2440197258): coincide en contar cada combinación de términos/definiciones como elemento y lo relaciona con navegación intuitiva. No resuelve todos los detalles de presentación ni acepta un parche todavía inexistente.

### 3.5. 2026: información visual y última objeción

29. **@alexarnaud**, [3 de febrero de 2026](https://github.com/nvaccess/nvda/issues/3858#issuecomment-3843219256): desde su experiencia con baja visión rebate que no exista distinción visual. La sangría por defecto y el espaciado, alineación y estilo de diseños reales separan los papeles. Student/James puede ser claro, pero otros textos no; pide transmitir la diferencia con NVDA. Fundamenta anunciar roles separados.
30. **@jenstrickland**, [4 de febrero de 2026](https://github.com/nvaccess/nvda/issues/3858#issuecomment-3848308197): propone listas dentro de listas: cada término como elemento/lista con definiciones hijas. Es una propuesta, no una modificación aplicada.
31. **@SaschaCowley**, [5 de febrero de 2026](https://github.com/nvaccess/nvda/issues/3858#issuecomment-3850671998): objeta que lo anterior parece uno-a-muchos, cuando la relación es muchos-a-muchos. Es el último comentario recuperado y **no aprueba una solución definitiva**.

### 3.6. Cómo desemboca el histórico en este parche

<!-- markdownlint-enable MD029 -->

El debate pasa de «no distingo los papeles» a «conteo y navegación necesitan entender asociaciones». La baja prioridad inicial no niega el defecto. Después aparecen usos y consecuencias concretos. Lo más claro es que sumar hijos engaña y que debe respetarse muchos-a-muchos; las propuestas de anuncio y navegación siguen sin ser idénticas.

| Decisión local | Antecedentes | Alternativa no implementada |
| --- | --- | --- |
| Separar `TERM` y `DEFINITION` | Comentarios 1, 8 y 29 | Omitir roles como propone el 25 |
| Contar grupos completos | 8, 23, 27 y 28 | Contar `dt`, sumar hijos o dividir por dos |
| Tratar envolturas directas | 18 y HTML | Recorrer arbitrariamente todos los descendientes |
| I por cada término | Expectativa admitida en el cuerpo y petición local | Un destino sintético por grupo o leer todos sus valores como en el 26 |
| Contenedor como `DESCRIPTIONLIST`, con etiqueta inglesa «description list» | Petición local más reciente, no consenso de la issue | Mantener `LIST` como en el parche inicial; no se añade el token ARIA `associationlist` |
| No fabricar listas virtuales | Restricción muchos-a-muchos del 31 | Transformaciones de los comentarios 19 y 30 |

Los 31 comentarios y sus glosas anteriores se conservan como histórico. En particular, la frase «El parche mantiene “lista”» del punto 25 describe el alcance anterior, sustituido por la petición más reciente.

## 4. Del requisito al diseño y al diff

### 4.1. Recorrido de los datos

NVDA no interpreta HTML desde el sintetizador. El navegador construye su árbol accesible, una API lo expone, NVDA lo convierte en objetos/campos y después decide cómo presentarlos y navegar.

- **IA2:** navegador → IAccessible2 → backend C++ `gecko_ia2` → nodos del buffer con atributos → normalizador Python → campos comunes → voz/braille. Chromium IA2 hereda parte de este recorrido aunque el nombre diga Gecko.
- **UIA:** navegador → UI Automation → objetos/rangos → `ChromiumUIATextInfo` → campos comunes → voz/braille. No usa el contador C++ IA2 y necesita recorrer su propio árbol.
- **MSHTML:** mapa de etiquetas del objeto y normalizador de su buffer → campos comunes. Compartir presentación no significa compartir el productor de Gecko.

La navegación I consulta **filtros de búsqueda propios**. Cambiar el rol anunciado no actualiza automáticamente qué nodos encuentra el backend.

### 4.2. Por qué no se arregla únicamente en voz

[source/speech/speech.py](../../source/speech/speech.py) es consumidor de roles y conteos, no un parser del DOM. Si solo se cambiara la frase hablada, braille seguiría recibiendo datos incorrectos y ambos consumidores tendrían que duplicar la lógica.

Los conteos nacen donde hay estructura del proveedor: `_childcontrolcount` comunica grupos de la lista y `definition-count` comunica definiciones del término.
El normalizador base convierte este último a entero para los buffers nativos.
Voz y braille consumen el mismo atributo sin inspeccionar HTML ni contar hermanos.
La cantidad acompaña al marcador del término, no se repite en su continuación ni salida, y se omite si vale cero, uno o es desconocida.

### 4.3. Máquina de estados del conteo

Se acumulan los términos y el número de definiciones del grupo actual:

1. Al comenzar no hay términos ni definiciones pendientes.
2. Los términos consecutivos se guardan sin incrementar el conteo de grupos.
3. Cada definición incrementa el conteo del grupo, sin recorrer su contenido.
4. Un término después de definiciones cierra el grupo anterior: si contiene términos y definiciones, suma un grupo completo y asigna su cantidad a todos sus términos.
5. Al terminar la lista se cierra también el último grupo. Un término huérfano obtiene cero definiciones.
6. Una envoltura directa comparte el estado; no se reinicia ni se desciende arbitrariamente por listas anidadas.

En el test, Student marca y Judy suma uno. Staff y Teacher marcan; Melissa suma el segundo y Robin no otro. Color y Colour marcan; su definición suma el tercero. Resultado: **tres grupos, cinco términos y cinco destinos I**.

C++ usa `fillDescriptionListCounts`, compartido por Gecko/IA2 y MSHTML y llamado después de renderizar los hijos.
Los atributos de invalidación obligan a actualizar juntos la lista y los términos cuando cambia un hermano; se rerenderizan los descendientes para evitar referencias con conteos obsoletos.
Es una decisión de corrección con coste en listas grandes que cambian frecuentemente.
UIA usa `RawViewWalker` y `_DescriptionListInfo`: guarda el conteo por runtime ID, no por texto del término.
Así un rango parcial puede anunciar las definiciones que quedan fuera del rango.
Los datos se recalculan al generar el campo de lista, sin caché persistente; un `COMError` descarta los datos parciales.
UIA distingue `None` (sin señal de lista descriptiva) de una estructura con cero grupos completos; IA2 y MSHTML disponen de la etiqueta `dl`.
La identificación UIA del contenedor se aplica al campo de texto desde esa estructura, no al rol del objeto: consultar un rol no debe recorrer todo el árbol ni alterar la selección de overlays.
Un `dl` nativo y un `role="list"` explícito con descendientes idénticos son indistinguibles en este recorrido y reciben la misma normalización.
Las listas vacías o sin definiciones expuestas conservan `Role.LIST`; no basta con encontrar términos para reclasificarlas.

Un término final huérfano no cuenta. WHATWG contempla grupos incompletos: el algoritmo local no reproduce toda esa recuperación. La prueba con mezcla de hijos directos y envueltos comprueba una política de recuperación, **no demuestra que esa mezcla sea HTML conforme**.

### 4.4. La repetición «Student Student term»

En la fase anterior se observó duplicación al pulsar I. Un campo podía aportar `name` y también texto descendiente ya incluido en el rango. Limpiar el campo evita repetir contenido sin inventar una excepción de voz para una palabra concreta.

Primero se investigó UIA, pero la ejecución real era IA2. El registro `ChromeVBuf` corrigió la suposición. La limpieza de `name` para términos/definiciones en el normalizador Gecko fue la corrección asociada a la prueba real que pasó. Las medidas UIA pertenecen al otro recorrido y no son prueba de la causa del éxito IA2.

Precisión normativa: los borradores actuales ARIA prohíben nombres en esos roles; ARIA 1.2 publicada permite nombre de autor. El anexo cita ambas versiones. No debe justificarse toda eliminación alegando una regla idéntica en todas las versiones: también importan el texto descendiente, la duplicación observada y el alcance del campo modificado.

### 4.5. Guía del anexo línea por línea

[3858-diff-comentado.es.md](3858-diff-comentado.es.md) conserva el diff literal **inicial**, con anotaciones A/N.
La tabla siguiente describe aquella instantánea, no la ampliación actual; sus números de línea pueden haber cambiado.
Las nuevas ubicaciones principales son el helper de [utils.cpp](../../nvdaHelper/vbufBase/utils.cpp), [voz](../../source/speech/speech.py), [braille](../../source/braille/regions/properties.py) y las [regresiones de presentación](../../tests/unit/test_descriptionLists.py).

| Sección del anexo | Archivo y responsabilidad |
| --- | --- |
| 1 | [gecko_ia2.cpp](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp): estado, hermanos, envolturas, momento de cálculo y atributo |
| 2 | [MSHTML.py de objetos](../../source/NVDAObjects/IAccessible/MSHTML.py): mapa de etiquetas |
| 3 | [chromium.py de UIA](../../source/NVDAObjects/UIA/chromium.py): fallbacks, COM, conteo, pila de ancestros, limpieza, integración y búsqueda |
| 4 | [aria.py](../../source/aria.py): token `term` al modelo común |
| 5 | [labels.py](../../source/braille/labels.py): abreviatura braille localizable |
| 6 | [role.py](../../source/controlTypes/role.py): `TERM = 159`, compatibilidad numérica y etiqueta |
| 7 | [textInfos](../../source/textInfos/__init__.py): marcador/disposición y `reportLists` |
| 8 | [MSHTML.py de buffers](../../source/virtualBuffers/MSHTML.py): I por `LI` y `DT`, no `DD` |
| 9 | [gecko_ia2.py](../../source/virtualBuffers/gecko_ia2.py): normalización de rol, conteo y nombres; búsqueda IA2 |
| 10 | [chromeTests.py](../../tests/system/robot/chromeTests.py): HTML, cinco destinos, flechas y salida de lista |
| 11 | [chromeTests.robot](../../tests/system/robot/chromeTests.robot): registro del test y selección |
| 12 | [test_textInfos.py](../../tests/unit/test_textInfos.py): política común de presentación |
| 13 | [changes.md](../../user_docs/en/changes.md): comunicación y límites de su formulación |
| 14 | [test_NVDAObjects_UIA_chromium.py](../../tests/unit/test_NVDAObjects_UIA_chromium.py): 199 líneas nuevas de dobles y pruebas |

El anexo también enlaza código **no modificado** de almacenamiento, normalización base, iteradores, herencia, voz y braille. Eso explica «por qué aquí», más allá de traducir la sintaxis.

## 5. Limitaciones

Estas observaciones distinguen el código actual de la evidencia histórica de pruebas, sin modificarlo silenciosamente:

1. **MSHTML se ha probado en un HTA local.** No se extrapola a todas las aplicaciones anfitrionas ni modos de documento.
2. **UIA real se ha probado en Chrome**, no en todos los navegadores/versiones Chromium.
3. **Fallback y búsqueda difieren.** El helper UIA elige el primer rol reconocido, pero I usa `AriaRole == "term"` exacto. Reconocer una cadena para contar no garantiza encontrarla así. IA2 también tiene condiciones diferentes entre normalización y búsqueda.
4. **La estructura accesible depende del proveedor.** UIA normaliza campos de texto desde la vista cruda, no roles de objetos; no distingue `dl` de `role="list"` con descendientes idénticos. Sin definiciones expuestas conserva `LIST`. Se cuentan contenedores `definition`; `description` es texto estático, no una definición adicional.
5. **IA2 cuenta etiquetas; la normalización también considera ARIA.** No hay una función compartida que haga equivalentes conteo, rol y quicknav para todos los overrides.
6. **Solo grupos completos.** No es la recuperación completa de WHATWG para nombres/valores ausentes.
7. **No hay objetos sintéticos de asociación ni lectura automática del grupo entero con I.** Sí se anuncia «término con N definiciones» cuando N supera uno.
8. **Profundidad limitada no elimina el coste.** UIA recorre hijos/hermanos por COM y los buffers nativos rerenderizan descendientes al actualizar la lista; no hay medición de rendimiento para listas muy grandes.
9. **No se ha probado todo el producto.** Las pruebas reales de Firefox y MSHTML aquí registradas preceden a `DESCRIPTIONLIST`; este documento no afirma nuevas ejecuciones para ese cambio. Faltan dispositivo braille físico y cobertura PDF nueva, y la suite unitaria completa previa no está verde.
10. **Los roles nuevos `TERM` y `DESCRIPTIONLIST` son aditivos**, preservando números previos; eso no acredita cada complemento que enumere exhaustivamente los roles. `DESCRIPTIONLIST` no establece un token ARIA ni garantiza una traducción nueva al español.

Antes de declarar resuelta toda la issue conviene acordar alcance con mantenedores, contrastar el changelog con la matriz de backends y ampliar pruebas. Este documento no inventa ese acuerdo ni convierte una revisión sin hallazgos en prueba de corrección total.

## 6. Fuentes y comprobación

### 6.1. Fuentes primarias

- [Issue #3858](https://github.com/nvaccess/nvda/issues/3858) y los 31 enlaces individuales anteriores.
- [API de la issue](https://api.github.com/repos/nvaccess/nvda/issues/3858) y [comentarios, página 1](https://api.github.com/repos/nvaccess/nvda/issues/3858/comments?per_page=100&page=1); página 2 vacía.
- [WHATWG: `dl`](https://html.spec.whatwg.org/multipage/grouping-content.html#the-dl-element): asociaciones, modelo de contenido y algoritmo; distinguir conformidad y recuperación.
- [ARIA in HTML: `dl`](https://www.w3.org/TR/html-aria/#el-dl), [`dt`](https://www.w3.org/TR/html-aria/#el-dt), [`dd`](https://www.w3.org/TR/html-aria/#el-dd) y [`dfn`](https://www.w3.org/TR/html-aria/#el-dfn): «No corresponding role» para los tres primeros; `term` para `dfn`.
- [Índice actual de roles WAI-ARIA](https://w3c.github.io/aria/#role_definitions): no incluye `associationlist`; no confundir una propuesta histórica con un token estándar vigente.
- [HTML-AAM](https://www.w3.org/TR/html-aam-1.0/) y [Core-AAM](https://www.w3.org/TR/core-aam-1.2/): contexto de mapeos a APIs, no una frase de voz obligatoria.
- [ARIA 1.2 `term`](https://www.w3.org/TR/wai-aria-1.2/#term) y [ARIA 1.2 `definition`](https://www.w3.org/TR/wai-aria-1.2/#definition), frente al [borrador `term`](https://w3c.github.io/aria/#term) y [borrador `definition`](https://w3c.github.io/aria/#definition): versiones diferenciadas para nombres.
- Código base/local y consumidores enlazados en [el anexo](3858-diff-comentado.es.md).

### 6.2. Método y resultado documental

Se ha comprobado el estado de Git; recuperado el cuerpo y todos los comentarios con fechas, enlaces y paginación; leído el comentario extenso sin truncarlo; examinado productores, normalizadores y consumidores; y contrastado los artefactos Robot y el backend registrado.

En la verificación histórica, el anexo se contrastó con **35 hunks de 14 archivos**, con **519 posiciones cambiadas: 500 nuevas y 19 antiguas**. Se comparó literalmente con Git y el test no seguido, normalizando solo finales de línea. Las anotaciones cubrían posiciones sin omisiones ni duplicados. El procedimiento reproducible está al final del anexo; esas cifras no describen el diff actual.

**100 % de cobertura documental** se refería al diff intencional inicial completo, no a las ampliaciones, a todas las ramas de ejecución ni a una auditoría de todo NVDA. El anexo se conserva como instantánea, no se actualiza retroactivamente.

La validación unitaria del nuevo rol y el bloqueo de la repetición en navegadores se describen al principio del documento.

En conclusión: el histórico justifica distinguir papeles y respetar muchos-a-muchos, no sumar hijos. El parche implementa una parte concreta de ese objetivo, añade la etiqueta de contenedor solicitada y mantiene navegación por listas y términos. El diff comentado explica la implementación inicial; este documento describe las ampliaciones, sin afirmar que estén resueltos todos los backends o todas las expectativas históricas.
