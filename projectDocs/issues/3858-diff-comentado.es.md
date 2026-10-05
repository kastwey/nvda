<!-- markdownlint-configure-file {"MD004": {"style": "dash"}, "MD050": {"style": "asterisk"}} -->
<!-- Este informe usa guiones para las anotaciones A/N y asteriscos para negrita; la excepción de estilo es local y no altera los bloques diff literales. -->

# #3858: diff intencional comentado, línea por línea

Para la explicación del problema, el estado y los 31 comentarios históricos, véase [3858-explicacion.es.md](3858-explicacion.es.md).

## Alcance y forma de lectura

**Instantánea histórica, anterior a la ampliación «término con N definiciones».**
Los hunks, las cifras de 500/19 líneas y sus anotaciones se conservan para documentar aquella versión, no el árbol de trabajo actual.
Las anclas de línea pueden haberse desplazado.
La implementación posterior sustituye el contador nativo por un helper compartido con MSHTML, usa la vista cruda de UIA y añade conteos por término en voz y braille.
El [documento principal actualizado](3858-explicacion.es.md#2-estado-actual) describe su arquitectura, pruebas y límites.

Documento técnico en español de la instantánea del 12 de septiembre de 2026, comparada con HEAD `c43cf6c1b0518326bd9ff0ed4712474feeb6131c`. No modifica ni propone aplicar la implementación aquí reproducida. No sustituye al documento principal con el histórico de la incidencia.

Se obtuvo `git diff HEAD --` limitado a los trece archivos de la tabla siguiente. El archivo de pruebas UIA nuevo todavía no estaba seguido por Git: se incorpora aparte, íntegro, como un hunk de creación de 199 líneas. No se incluyen submódulos, dependencias ni cambios ajenos a esta selección.

| Archivo | Añadidas | Eliminadas |
| --- | ---: | ---: |
| [../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp) | 48 | 1 |
| [../../source/NVDAObjects/IAccessible/MSHTML.py](../../source/NVDAObjects/IAccessible/MSHTML.py) | 3 | 3 |
| [../../source/NVDAObjects/UIA/chromium.py](../../source/NVDAObjects/UIA/chromium.py) | 122 | 2 |
| [../../source/aria.py](../../source/aria.py) | 2 | 1 |
| [../../source/braille/labels.py](../../source/braille/labels.py) | 3 | 1 |
| [../../source/controlTypes/role.py](../../source/controlTypes/role.py) | 4 | 1 |
| [../../source/textInfos/\_\_init\_\_.py](../../source/textInfos/__init__.py) | 7 | 1 |
| [../../source/virtualBuffers/MSHTML.py](../../source/virtualBuffers/MSHTML.py) | 2 | 2 |
| [../../source/virtualBuffers/gecko_ia2.py](../../source/virtualBuffers/gecko_ia2.py) | 22 | 4 |
| [../../tests/system/robot/chromeTests.py](../../tests/system/robot/chromeTests.py) | 57 | 1 |
| [../../tests/system/robot/chromeTests.robot](../../tests/system/robot/chromeTests.robot) | 5 | 1 |
| [../../tests/unit/test_textInfos.py](../../tests/unit/test_textInfos.py) | 24 | 1 |
| [../../user_docs/en/changes.md](../../user_docs/en/changes.md) | 2 | 0 |
| [../../tests/unit/test_NVDAObjects_UIA_chromium.py](../../tests/unit/test_NVDAObjects_UIA_chromium.py) (nuevo) | 199 | 0 |
| **Total intencional** | **500** | **19** |

Cada bloque `diff` conserva literalmente su cabecera de hunk, contexto, signos, tabulaciones y líneas vacías. Las cabeceras de archivo se conservan al principio de cada archivo seguido. Para el archivo nuevo se usa una cabecera explícita de creación sin inventar un índice de blob. Los comentarios están fuera de los bloques, para no adulterar el diff.

**Convención de anotación:** N significa número en el archivo nuevo del árbol de trabajo; A significa número en la versión antigua de HEAD. Una sustitución tiene dos comentarios: qué se retira y qué lo reemplaza. Los enlaces N llevan al código actual. Los enlaces A son un ancla orientativa en el mismo archivo actual, **no** una vista de HEAD: el contenido antiguo exacto está en la línea con signo menos del hunk. No se agrupan instrucciones, datos de pruebas ni comentarios con contenido; solo se agrupan blancos o cierres cuando se explica expresamente su función. Los marcadores HTML de archivo sirven a la verificación automática y no forman parte del código.

### Qué significa «origen» aquí

Se distingue entre requisito funcional, contrato de API, estructura ya existente y expectativa de prueba. La necesidad de distinguir términos/definiciones y contar grupos está plasmada en el changelog y en las aserciones del diff. La navegación por I conserva elementos ordinarios y añade términos; no añade una categoría de navegación por definiciones. Las medidas para evitar nombres duplicados tienen explicación en el comentario UIA y pruebas de diccionarios. Eso **no permite reconstruir una fecha, un autor de una observación ni una ejecución histórica** a partir de este diff. No se presentan las expectativas de prueba como resultados medidos durante esta tarea: no se ejecutaron pruebas ni navegadores.

## Mapa arquitectónico que justifica las ubicaciones

1. **Modelo semántico común.** `Role` identifica tipos de objetos, no frases de un sintetizador. Su [contrato de compatibilidad](../../source/controlTypes/role.py#L13-L24) exige continuar los valores numéricos. `TERM` se añade al final; `DEFINITION` ya existía. [El diccionario ARIA](../../source/aria.py#L10-L34) traduce nombres de roles a ese modelo. [La categoría de presentación](../../source/textInfos/__init__.py#L53-L84) decide cómo informar de campos para voz y braille.
2. **IA2 y buffer virtual.** El backend C++ construye nodos de control y texto; al terminar `fillVBuf` tiene los hijos disponibles. El almacenamiento genérico [genera un conteo estructural](../../nvdaHelper/vbufBase/storage.cpp#L226-L257), no grupos semánticos de una `dl`. Por eso se introduce un atributo específico en el productor y se copia a `_childcontrolcount` en el normalizador Python. No se redefine la estructura de todos los buffers.
3. **«gecko_ia2» no significa exclusivamente Firefox.** [Chrome importa y hereda ese buffer y su TextInfo](../../source/NVDAObjects/IAccessible/chromium.py#L14-L16), [normaliza mediante `super()`](../../source/NVDAObjects/IAccessible/chromium.py#L43-L81) y [selecciona `ChromeVBuf`](../../source/NVDAObjects/IAccessible/chromium.py#L98-L120). [El constructor heredado](../../source/virtualBuffers/gecko_ia2.py#L293-L297) utiliza el backend nativo `gecko_ia2`. Así, el cambio C++/Python también puede llegar al Chrome real por IA2.
4. **UIA es otro recorrido.** No usa ese buffer C++ para este conteo: `UIAWebTextInfo` obtiene campos de objetos/rangos UIA. [Su conteo previo](../../source/NVDAObjects/UIA/web.py#L256-L264) lee `SizeOfSet` del primer hijo. El archivo Chromium especializa esa conducta con `ControlViewWalker`, y después normaliza un flujo `TextWithFieldsT` completo para conocer la lista antecesora más próxima. [La base procesa `content`](../../source/NVDAObjects/UIA/web.py#L323-L346): eliminarlo antes de esa fase evita que sustituya texto descendiente en los términos ya reconocidos.
5. **MSHTML conserva su separación histórica.** El [normalizador de su buffer](../../source/virtualBuffers/MSHTML.py#L97-L113) usa prioridad ARIA, etiqueta HTML y finalmente rol IAccessible. Reutiliza el diccionario del objeto MSHTML; [el objeto también lo consulta bajo sus condiciones existentes](../../source/NVDAObjects/IAccessible/MSHTML.py#L813-L835). Cambiar ese diccionario evita mantener dos traducciones distintas. Aquí no se incorpora ningún conteo nuevo de grupos MSHTML.
6. **Consumidores sin lógica de navegador nueva.** [Voz lee `_childcontrolcount`](../../source/speech/speech.py#L2289-L2302), decide [orden según motivo de salida](../../source/speech/speech.py#L2239-L2260) y produce [«with … items» para listas de solo lectura](../../source/speech/speech.py#L2409-L2426). [Braille reutiliza el conteo positivo](../../source/braille/regions/properties.py#L307-L310). Por tanto no se debe inferir el HTML desde frases de voz, ni duplicar el conteo en voz y braille. La etiqueta braille sí pertenece a su tabla de presentación, no al backend.
7. **Búsqueda no es presentación.** [El buffer convierte filtros a búsquedas nativas](../../source/virtualBuffers/__init__.py#L710-L738). [La lista de diccionarios representa alternativas y sus claves se combinan](../../source/virtualBuffers/__init__.py#L58-L95). UIA, en cambio, utiliza [condiciones de propiedades y rangos](../../source/UIAHandler/browseMode.py#L233-L264). Cambiar únicamente `role` en un campo hablado no actualiza esos predicados de navegación.

### Fuentes normativas y límites transversales

- [WHATWG: `dl`](https://html.spec.whatwg.org/multipage/grouping-content.html#the-dl-element) define asociaciones de uno o varios nombres y uno o varios valores, permite envolturas `div` directas y describe un algoritmo que también conserva grupos incompletos. **El diff cuenta solo grupos completos**: incrementa al encontrar la primera definición después de términos pendientes. No reproduce toda la recuperación WHATWG; no valida el HTML ni reconstruye el DOM. Mantiene estado al atravesar una envoltura, ignora otros nodos y no baja arbitrariamente por descendientes.
- [WAI-ARIA 1.2: elección del primer rol reconocido](https://www.w3.org/TR/wai-aria-1.2/#roles) fundamenta la precedencia de tokens. La implementación usa el conjunto de roles que NVDA reconoce, no un validador universal de todos los roles normativos.
- El [borrador actual de ARIA: `term`](https://w3c.github.io/aria/#term) y [el de `definition`](https://w3c.github.io/aria/#definition), consultados en esta tarea, indican `Name From: prohibited`. **No atribuir esa regla a ARIA 1.2**: las tablas publicadas de [term en 1.2](https://www.w3.org/TR/wai-aria-1.2/#term) y [definition en 1.2](https://www.w3.org/TR/wai-aria-1.2/#definition) indican `author`. Se documenta la intención del diff con esa precisión de versión, no como una prohibición invariable en todas las versiones.
- **Chrome real: IA2, no validación real UIA.** [El setup Robot](../../tests/system/robot/chromeTests.robot#L30-L34) usa [el perfil estándar](../../tests/system/nvdaSettingsFiles/standard-dontShowWelcomeDialog.ini#L1-L27), que no fuerza UIA. [El valor por defecto](../../source/config/__init__.py#L1556-L1567) y [la selección del backend](../../source/UIAHandler/__init__.py#L1321-L1343) prefieren IA2 cuando está disponible. Este es el recorrido de la prueba Chrome en el entorno ordinario de la tarea; el test no incluye una aserción de identidad de backend. Los tests nuevos UIA son dobles Python, no una sesión de navegador UIA.
- **Quicknav UIA tiene coincidencia exacta `AriaRole == "term"`.** El análisis de fallbacks del conteo no amplía esa condición a cadenas como `unsupported term`. IA2 usa otro filtro por palabra y tampoco comparte exactamente la misma semántica de precedencia.
- **No hay paridad demostrada de todas las definiciones UIA.** `description` sigue asociado a `STATICTEXT` en [el mapa existente](../../source/aria.py#L10-L20). El helper lo reconoce para contar; no lo convierte allí en `DEFINITION`. La normalización nueva posterior convierte términos, no definiciones. Esto limita la lectura universal del changelog.

## 1. Backend nativo IA2: conteo de grupos

<!-- file: nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp -->

### Hunk 1.1: atribución

**Necesidad y origen:** metadatos de autoría incluidos en el diff, sin efecto funcional. Se actualiza la cabecera del archivo efectivamente modificado, no las capas que consumen su resultado. No se deduce de ella la procedencia histórica de cada decisión.

```diff
diff --git a/nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp b/nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp
index 4f8575bff..ac4255930 100755
--- a/nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp
+++ b/nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp
@@ -1,7 +1,7 @@
 /*
 This file is a part of the NVDA project.
 URL: http://www.nvda-project.org/
-Copyright 2007-2023 NV Access Limited, Mozilla Corporation
+Copyright 2007-2026 NV Access Limited, Mozilla Corporation, Juanjo M
     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License version 2.0, as published by
     the Free Software Foundation.
```

- [A4](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L4): retira la atribución con fin en 2023; no elimina ni cambia el texto de licencia.
- [N4](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L4): amplía a 2026 y añade Juanjo M, manteniendo a los titulares previos.

### Hunk 1.2: estado compartido y recorrido limitado

**Necesidad:** el número de hijos del buffer no equivale a asociaciones término-definición. Dos términos y dos definiciones constituyen un grupo, no cuatro elementos semánticos. **Origen:** requisito reflejado en la prueba Chrome; modelo de grupos HTML y API de nodos ya existente. **Ubicación:** aquí están disponibles etiquetas IA2 y relaciones entre nodos ya renderizados. Hacerlo en voz perdería esa estructura y obligaría a repetirlo en braille. El estado por referencia permite atravesar `div` sin reiniciar términos pendientes; no hay una pila ilimitada ni un contador por término.

```diff
@@ -121,6 +121,41 @@ const wchar_t EMBEDDED_OBJ_CHAR = 0xFFFC;
 // text leaf nodes so the user can access them.
 constexpr const wchar_t EMPTY_TEXT_NODE[]{L" "};
 
+struct DescriptionListGroupState {
+	int count = 0;
+	bool hasPendingTerms = false;
+};
+
+/**
+ * Update the count of complete name-value groups among a description list's children.
+ * Recursion is limited to the one direct div wrapper level permitted by HTML.
+ */
+static void updateDescriptionListGroupState(
+	VBufStorage_fieldNode_t* parentNode,
+	const bool allowDivWrappers,
+	DescriptionListGroupState& state
+) {
+	for (
+		VBufStorage_fieldNode_t* child = parentNode->getFirstChild();
+		child;
+		child = child->getNext()
+	) {
+		const auto tag = child->getAttribute(L"IAccessible2::attribute_tag");
+		if (!tag) {
+			continue;
+		}
+		if (*tag == L"dt") {
+			state.hasPendingTerms = true;
+		} else if (*tag == L"dd" && state.hasPendingTerms) {
+			++state.count;
+			state.hasPendingTerms = false;
+		} else if (allowDivWrappers && *tag == L"div") {
+			// HTML permits one level of direct div wrappers around description list groups.
+			updateDescriptionListGroupState(child, false, state);
+		}
+	}
+}
+
 static IAccessible2* IAccessible2FromIdentifier(int docHandle, int ID) {
 	IAccessible* pacc=NULL;
 	IServiceProvider* pserv=NULL;
```

- [N124](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L124): declara un estado específico de esta operación, evitando contadores globales compartidos entre listas.
- [N125](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L125): empieza en cero grupos completos; no estima el resultado a partir de hijos.
- [N126](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L126): registra si hay uno o más términos aún sin una primera definición posterior.
- [N127](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L127): cierra la estructura y su declaración con punto y coma.
- [N128](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L128): blanco de separación entre el tipo y el helper.
- [N129](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L129): abre el comentario documental del helper.
- [N130](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L130): precisa que son grupos completos de nombres y valores entre los hijos; no todos los nodos.
- [N131](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L131): explica el límite de un nivel de envoltura directa; no promete recuperación de HTML arbitrario.
- [N132](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L132): cierra ese comentario documental.
- [N133](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L133): define un helper `static` de esta unidad C++; devuelve `void` porque modifica el estado recibido, sin introducir una API exportada.
- [N134](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L134): recibe el nodo padre del almacenamiento virtual, no un nodo DOM ni un objeto COM que deba volver a consultar.
- [N135](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L135): recibe una bandera constante por llamada para permitir o impedir descender a envolturas.
- [N136](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L136): pasa el estado por referencia, conservándolo entre hermanos y al entrar/salir de una envoltura.
- [N137](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L137): cierra parámetros y abre el cuerpo de la función.
- [N138](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L138): abre un recorrido `for` sobre hijos directos, con sus tres componentes separados.
- [N139](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L139): inicializa el cursor al primer hijo mediante la API del buffer.
- [N140](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L140): termina cuando no hay nodo hijo; funciona también para un padre sin hijos.
- [N141](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L141): avanza al siguiente hermano, no al siguiente descendiente arbitrario.
- [N142](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L142): cierra la cabecera del bucle y abre su cuerpo.
- [N143](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L143): lee la etiqueta guardada en los atributos IA2 del nodo; `L` conserva el tipo de cadena ancha usado por este almacenamiento.
- [N144](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L144): comprueba ausencia de atributo antes de desreferenciar su puntero.
- [N145](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L145): ignora nodos sin etiqueta, incluido texto; no borra términos pendientes.
- [N146](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L146): cierra el filtro de ausencia de etiqueta.
- [N147](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L147): identifica un `dt` por etiqueta; aquí no se inspeccionan overrides ARIA del hijo.
- [N148](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L148): marca términos pendientes. Varios `dt` consecutivos mantienen el mismo booleano, sin aumentar el conteo.
- [N149](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L149): solo acepta un `dd` para completar grupo si había términos pendientes; un `dd` huérfano no suma.
- [N150](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L150): incrementa exactamente al completar una asociación.
- [N151](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L151): consume los términos pendientes; posteriores `dd` del mismo grupo no vuelven a sumar.
- [N152](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L152): permite descender solo si el nodo es `div` y esta llamada aún admite envolturas.
- [N153](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L153): deja junto a la recursión el motivo HTML de su límite.
- [N154](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L154): procesa los hijos del `div` con la misma referencia de estado y con `false`; evita un segundo nivel y no reinicia el grupo al salir.
- [N155-N157](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L155-L157): cierres, respectivamente, de la rama de envoltura, del bucle de hijos y del helper; no añaden operaciones.
- [N158](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L158): blanco antes del helper IAccessible preexistente.

### Hunk 1.3: publicar el resultado al terminar el nodo

**Necesidad y origen:** enlazar el algoritmo con el ciclo real de construcción; sin esta llamada sería código sin efecto. El [contexto final de `fillVBuf`](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1372-L1437) ya ha renderizado hijos, añadido nombre y metadatos ARIA, y aún no ha liberado recursos. **Por qué aquí:** calcular antes de construir hijos produciría un resultado incompleto. Usar una clave propia evita redefinir en el almacenamiento genérico el conteo de todos los controles.

```diff
@@ -1370,6 +1405,18 @@ VBufStorage_fieldNode_t* GeckoVBufBackend_t::fillVBuf(
 		*parentNode
 	);
 
+	if (
+		auto tag = IA2AttribsMap.find(L"tag");
+		tag != IA2AttribsMap.end() && tag->second == L"dl" && role == ROLE_SYSTEM_LIST
+	) {
+		DescriptionListGroupState descriptionListGroupState;
+		updateDescriptionListGroupState(parentNode, true, descriptionListGroupState);
+		parentNode->addAttribute(
+			L"description-list-group-count",
+			std::to_wstring(descriptionListGroupState.count)
+		);
+	}
+
 	// Clean up.
 	if(name)
 		SysFreeString(name);
```

- [N1408](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1408): abre una condición con inicializador local para aplicar el conteo solo a la clase de contenedor prevista.
- [N1409](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1409): busca `tag` en el mapa IA2 sin insertar entradas ausentes.
- [N1410](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1410): exige atributo presente, etiqueta `dl` y rol nativo lista; no altera `ul`, `ol` ni un `dl` expuesto con otro rol.
- [N1411](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1411): cierra la condición y abre el bloque aplicado a esa lista.
- [N1412](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1412): crea estado nuevo inicializado por los miembros de la estructura, independiente de listas anidadas.
- [N1413](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1413): recorre la lista permitiendo envolturas directas desde su raíz.
- [N1414](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1414): inicia la escritura de un atributo del nodo de lista, no de sus términos.
- [N1415](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1415): establece la clave que el normalizador Python leerá exactamente; no es una propiedad estándar del navegador.
- [N1416](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1416): serializa el entero como cadena ancha, incluyendo cero; el consumidor convertirá el conteo cuando corresponda.
- [N1417-N1418](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1417-L1418): cierres de la llamada y del bloque condicional.
- [N1419](../../nvdaHelper/vbufBackends/gecko_ia2/gecko_ia2.cpp#L1419): separa del código de limpieza sin cambiar su orden.

## 2. MSHTML: traducción de etiquetas a roles

<!-- file: source/NVDAObjects/IAccessible/MSHTML.py -->

### Hunk 2.1: atribución

**Necesidad/origen:** actualización de autoría de este archivo, no comportamiento. Pertenece a su cabecera, no al buffer ni a voz.

```diff
diff --git a/source/NVDAObjects/IAccessible/MSHTML.py b/source/NVDAObjects/IAccessible/MSHTML.py
index 630505560..6b0484b2b 100644
--- a/source/NVDAObjects/IAccessible/MSHTML.py
+++ b/source/NVDAObjects/IAccessible/MSHTML.py
@@ -1,6 +1,6 @@
 # NVDAObjects/MSHTML.py
 # A part of NonVisual Desktop Access (NVDA)
-# Copyright (C) 2006-2025 NV Access Limited, Aleksey Sadovoy
+# Copyright (C) 2006-2026 NV Access Limited, Aleksey Sadovoy, Juanjo M
 # This file is covered by the GNU General Public License.
 # See the file COPYING for more details.
 
```

- [A3](../../source/NVDAObjects/IAccessible/MSHTML.py#L3): retira la atribución anterior, que terminaba en 2025.
- [N3](../../source/NVDAObjects/IAccessible/MSHTML.py#L3): extiende a 2026 y añade Juanjo M, sin cambio de licencia.

### Hunk 2.2: separar `DD` de `DT`

**Necesidad/origen:** cumplir la distinción semántica sin perder `DL` como lista ni cambiar `LI`. **Por qué este archivo:** contiene `nodeNamesToNVDARoles`, reutilizado por objeto y buffer según las prioridades descritas arriba. Hacer la traducción solo en voz no cambiaría el rol que recibe braille; repetirla en el buffer duplicaría el mapa. **Límite:** no introduce conteo de grupos ni normalización de nombres MSHTML.

```diff
@@ -132,8 +132,8 @@ def __contains__(self, item):
 	"OL": controlTypes.Role.LIST,
 	"DL": controlTypes.Role.LIST,
 	"LI": controlTypes.Role.LISTITEM,
-	"DD": controlTypes.Role.LISTITEM,
-	"DT": controlTypes.Role.LISTITEM,
+	"DD": controlTypes.Role.DEFINITION,
+	"DT": controlTypes.Role.TERM,
 	"TR": controlTypes.Role.TABLEROW,
 	"THEAD": controlTypes.Role.TABLEHEADER,
 	"TBODY": controlTypes.Role.TABLEBODY,
```

- [A135](../../source/NVDAObjects/IAccessible/MSHTML.py#L135): elimina la equiparación de una definición con un elemento ordinario de lista.
- [A136](../../source/NVDAObjects/IAccessible/MSHTML.py#L136): elimina la misma equiparación para el término.
- [N135](../../source/NVDAObjects/IAccessible/MSHTML.py#L135): asocia la etiqueta mayúscula `DD` al rol ya existente `DEFINITION`.
- [N136](../../source/NVDAObjects/IAccessible/MSHTML.py#L136): asocia `DT` al nuevo `TERM`; la capitalización corresponde al mapa de etiquetas MSHTML.

## 3. Chromium UIA: conteo, contexto y navegación

<!-- file: source/NVDAObjects/UIA/chromium.py -->

### Hunk 3.1: imports y atribución

**Necesidad/origen:** el módulo incorpora helpers con manejo de error COM, consulta de roles, tipos de campos y quicknav. Estas dependencias proceden de la API y de la separación UIA ya existente. **Por qué aquí:** la especialización conoce peculiaridades de Chromium; no necesita que voz importe COM ni que la base web imponga esta heurística a otros proveedores.

```diff
diff --git a/source/NVDAObjects/UIA/chromium.py b/source/NVDAObjects/UIA/chromium.py
index f836b7338..ce42cbb88 100644
--- a/source/NVDAObjects/UIA/chromium.py
+++ b/source/NVDAObjects/UIA/chromium.py
@@ -1,12 +1,17 @@
 # A part of NonVisual Desktop Access (NVDA)
 # This file is covered by the GNU General Public License.
 # See the file COPYING for more details.
-# Copyright (C) 2020-2021 NV Access limited, Leonard de Ruijter
+# Copyright (C) 2020-2026 NV Access limited, Leonard de Ruijter, Juanjo M
 
 
-import UIAHandler  # noqa: I001
+from comtypes import COMError  # noqa: I001
+
+import aria
+import UIAHandler
 from . import web
 import controlTypes
+import textInfos
+from UIAHandler.browseMode import UIAControlQuicknavIterator
 
 """
 This module provides UIA behaviour specific to the chromium family of browsers.
```

- [A4](../../source/NVDAObjects/UIA/chromium.py#L4): retira la cabecera de autoría hasta 2021.
- [N4](../../source/NVDAObjects/UIA/chromium.py#L4): actualiza a 2026 e incorpora Juanjo M; conserva la grafía `limited` del original.
- [A7](../../source/NVDAObjects/UIA/chromium.py#L7): elimina el import de `UIAHandler` en la posición inicial; no elimina esa dependencia del módulo.
- [N7](../../source/NVDAObjects/UIA/chromium.py#L7): importa `COMError` para el fallo recuperable del recorrido. `noqa: I001` suprime el diagnóstico de ordenación de imports en el bloque deliberadamente ordenado.
- [N8](../../source/NVDAObjects/UIA/chromium.py#L8): blanco que separa la dependencia COM de imports internos.
- [N9](../../source/NVDAObjects/UIA/chromium.py#L9): permite consultar el mapa central de roles reconocidos, evitando una segunda lista de fallbacks.
- [N10](../../source/NVDAObjects/UIA/chromium.py#L10): mantiene `UIAHandler`, ahora después de `aria`, para cliente, interfaces y constantes de propiedades.
- [N13](../../source/NVDAObjects/UIA/chromium.py#L13): importa tipos y clases de comandos del flujo de texto; no es un import solo decorativo de anotaciones.
- [N14](../../source/NVDAObjects/UIA/chromium.py#L14): reutiliza el iterador UIA de quicknav, en lugar de reimplementar movimientos y rangos.

### Hunk 3.2: tres helpers, tres responsabilidades

**Necesidad:** reconocer el primer rol utilizable, calcular grupos sin confundir listas ordinarias y corregir términos según su lista contenedora. **Origen:** precedencia ARIA, comportamiento de exposición descrito por el comentario Chromium, contrato `TextWithFieldsT` y casos unitarios añadidos. **Ubicación:** esta capa ve `AriaRole`, `ControlViewWalker` y campos jerárquicos; los consumidores no deberían saber si un término llegó como `listitem`.

`None` significa «no sustituir el conteo heredado», no necesariamente lista vacía. Cero significa «hay definición, pero no grupo completo». El recorrido no baja por el contenido de una definición ni por otra lista; solo por una envoltura `group` directa. La normalización posterior usa una pila de campos, no el DOM: una lista ordinaria anidada corta la herencia semántica de una lista descriptiva exterior. El comentario sobre exposición nativa es una premisa del helper y del doble de prueba, no una medición UIA realizada aquí.

```diff
@@ -15,6 +20,89 @@
 """
 
 
+def _getPrimaryAriaRole(ariaRoles: object) -> str | None:
+	"""Return the first recognized role from a UIA AriaRole fallback list."""
+	if not isinstance(ariaRoles, str):
+		return None
+	return next(
+		(role for role in ariaRoles.lower().split() if role in aria.ariaRolesToNVDARoles),
+		None,
+	)
+
+
+def _getDescriptionListGroupCount(
+	listElement: UIAHandler.IUIAutomationElement,
+) -> int | None:
+	"""Return the number of complete term-definition groups in a Chromium UIA description list.
+
+	Chromium exposes native description-list terms as ``listitem`` and definitions
+	as ``description``. HTML also permits one level of direct ``div`` wrappers,
+	which Chromium exposes as ``group``.
+	"""
+	clientObject = UIAHandler.handler.clientObject
+	walker = clientObject.ControlViewWalker
+	groupCount = 0
+	hasDefinitions = False
+	hasPendingTerms = False
+
+	def processChildren(
+		parentElement: UIAHandler.IUIAutomationElement,
+		allowGroupWrappers: bool,
+	) -> None:
+		nonlocal groupCount, hasDefinitions, hasPendingTerms
+		child = walker.GetFirstChildElement(parentElement)
+		while child:
+			ariaRole = _getPrimaryAriaRole(
+				child.getCurrentPropertyValue(UIAHandler.UIA_AriaRolePropertyId),
+			)
+			if ariaRole in ("listitem", "term"):
+				hasPendingTerms = True
+			elif ariaRole in ("description", "definition"):
+				hasDefinitions = True
+				if hasPendingTerms:
+					groupCount += 1
+					hasPendingTerms = False
+			elif allowGroupWrappers and ariaRole == "group":
+				processChildren(child, False)
+			child = walker.GetNextSiblingElement(child)
+
+	try:
+		processChildren(listElement, True)
+	except COMError:
+		return None
+	return groupCount if hasDefinitions else None
+
+
+def _normalizeDescriptionListTerms(fields: textInfos.TextInfo.TextWithFieldsT) -> None:
+	"""Normalize Chromium description-list terms and remove their prohibited names."""
+	controlFieldStack: list[tuple[textInfos.ControlField, bool]] = []
+	for item in fields:
+		if not isinstance(item, textInfos.FieldCommand):
+			continue
+		if item.command == "controlStart":
+			isDescriptionList = bool(item.field.pop("_isDescriptionList", False))
+			nearestListIsDescription = next(
+				(
+					ancestorIsDescriptionList
+					for field, ancestorIsDescriptionList in reversed(controlFieldStack)
+					if field.get("role") == controlTypes.Role.LIST
+				),
+				False,
+			)
+			role = item.field.get("role")
+			if role == controlTypes.Role.TERM or (
+				role == controlTypes.Role.LISTITEM and nearestListIsDescription
+			):
+				item.field["role"] = controlTypes.Role.TERM
+				# Chromium reports a term's content-derived name separately from its content.
+				# ARIA prohibits accessible names on terms, so discard this duplicate name.
+				item.field.pop("name", None)
+				item.field.pop("alwaysReportName", None)
+			controlFieldStack.append((item.field, isDescriptionList))
+		elif item.command == "controlEnd" and controlFieldStack:
+			controlFieldStack.pop()
+
+
 class ChromiumUIATextInfo(web.UIAWebTextInfo):
 	def expand(self, unit):
 		# #12474: Expanding to line breaks when the underlying text range is empty.
```

#### Anotaciones del selector de rol

- [N23](../../source/NVDAObjects/UIA/chromium.py#L23): declara helper privado con entrada `object`, ya que una propiedad COM no tiene por qué ser una cadena; devuelve token o ausencia.
- [N24](../../source/NVDAObjects/UIA/chromium.py#L24): documenta que el resultado es el primer rol reconocido, no cualquier coincidencia con `term`.
- [N25](../../source/NVDAObjects/UIA/chromium.py#L25): comprueba el tipo antes de llamar a operaciones de cadena.
- [N26](../../source/NVDAObjects/UIA/chromium.py#L26): devuelve ausencia ante valor no textual, sin convertir sentinelas COM a texto.
- [N27](../../source/NVDAObjects/UIA/chromium.py#L27): selecciona el primer resultado de un generador; no necesita crear una lista de coincidencias.
- [N28](../../source/NVDAObjects/UIA/chromium.py#L28): normaliza mayúsculas, divide por espacios en blanco y filtra por el diccionario ARIA de NVDA, conservando el orden.
- [N29](../../source/NVDAObjects/UIA/chromium.py#L29): establece `None` si no hay roles reconocidos; evita `StopIteration`.
- [N30](../../source/NVDAObjects/UIA/chromium.py#L30): cierra la llamada a `next`.
- [N31-N32](../../source/NVDAObjects/UIA/chromium.py#L31-L32): blancos entre funciones de módulo.

#### Anotaciones del conteo

- [N33](../../source/NVDAObjects/UIA/chromium.py#L33): abre el helper privado de conteo, separado del formateo de campos para poder probarlo aisladamente.
- [N34](../../source/NVDAObjects/UIA/chromium.py#L34): tipa el contenedor como elemento UIA, no como `NVDAObject` ni como nodo del buffer IA2.
- [N35](../../source/NVDAObjects/UIA/chromium.py#L35): declara el resultado entero opcional y abre el cuerpo; `None` permite conservar la conducta anterior.
- [N36](../../source/NVDAObjects/UIA/chromium.py#L36): define expresamente el conteo como grupos completos, no términos ni definiciones aisladas.
- [N37](../../source/NVDAObjects/UIA/chromium.py#L37): blanco interno que separa contrato y explicación de exposición.
- [N38](../../source/NVDAObjects/UIA/chromium.py#L38): documenta `listitem` como exposición de términos nativos asumida por el helper.
- [N39](../../source/NVDAObjects/UIA/chromium.py#L39): documenta `description` para definiciones y la posibilidad de un nivel de `div`.
- [N40](../../source/NVDAObjects/UIA/chromium.py#L40): conecta la envoltura HTML con el token UIA `group`; es una heurística específica del proveedor.
- [N41](../../source/NVDAObjects/UIA/chromium.py#L41): cierra el docstring.
- [N42](../../source/NVDAObjects/UIA/chromium.py#L42): toma el cliente UIA ya inicializado por NVDA; no crea otra sesión de automatización.
- [N43](../../source/NVDAObjects/UIA/chromium.py#L43): usa la vista de controles, no todos los nodos de la vista cruda ni el DOM.
- [N44](../../source/NVDAObjects/UIA/chromium.py#L44): inicializa el contador local a cero.
- [N45](../../source/NVDAObjects/UIA/chromium.py#L45): guarda evidencia de definición para distinguir una lista ordinaria de un conteo descriptivo igual a cero.
- [N46](../../source/NVDAObjects/UIA/chromium.py#L46): inicia sin términos pendientes; varios términos se acumulan mediante una sola bandera.
- [N47](../../source/NVDAObjects/UIA/chromium.py#L47): blanco antes de la función anidada.
- [N48](../../source/NVDAObjects/UIA/chromium.py#L48): declara el recorrido anidado, que comparte el estado de esta lista y nada más.
- [N49](../../source/NVDAObjects/UIA/chromium.py#L49): tipa el padre que puede ser la lista o su envoltura directa.
- [N50](../../source/NVDAObjects/UIA/chromium.py#L50): expresa mediante booleano si aún se permite entrar en grupos.
- [N51](../../source/NVDAObjects/UIA/chromium.py#L51): cierra la firma y declara que el recorrido modifica estado, sin valor de retorno.
- [N52](../../source/NVDAObjects/UIA/chromium.py#L52): `nonlocal` permite actualizar las tres variables de la llamada exterior y compartirlas entre envolturas.
- [N53](../../source/NVDAObjects/UIA/chromium.py#L53): obtiene el primer hijo del padre por la API del walker.
- [N54](../../source/NVDAObjects/UIA/chromium.py#L54): itera mientras el proveedor entregue un hijo válido.
- [N55](../../source/NVDAObjects/UIA/chromium.py#L55): inicia la selección del rol primario del hijo, reutilizando el helper anterior.
- [N56](../../source/NVDAObjects/UIA/chromium.py#L56): lee `UIA_AriaRolePropertyId` actual; no depende de un nombre de control localizado.
- [N57](../../source/NVDAObjects/UIA/chromium.py#L57): cierra la llamada de selección.
- [N58](../../source/NVDAObjects/UIA/chromium.py#L58): acepta tanto la exposición nativa `listitem` como el token explícito `term` como candidatos a nombre de grupo.
- [N59](../../source/NVDAObjects/UIA/chromium.py#L59): marca términos pendientes, sin incrementar todavía.
- [N60](../../source/NVDAObjects/UIA/chromium.py#L60): acepta `description` y `definition` como señales de valor de grupo, aunque no tengan el mismo rol NVDA en el mapa central.
- [N61](../../source/NVDAObjects/UIA/chromium.py#L61): registra evidencia descriptiva incluso si no había término; de ahí el retorno cero para una definición huérfana.
- [N62](../../source/NVDAObjects/UIA/chromium.py#L62): exige términos previos para sumar un grupo completo.
- [N63](../../source/NVDAObjects/UIA/chromium.py#L63): suma un grupo al llegar la primera definición asociada.
- [N64](../../source/NVDAObjects/UIA/chromium.py#L64): consume la bandera; definiciones sucesivas no inflan el conteo.
- [N65](../../source/NVDAObjects/UIA/chromium.py#L65): limita la recursión a un hijo `group` cuando la llamada lo permite.
- [N66](../../source/NVDAObjects/UIA/chromium.py#L66): entra en la envoltura con la opción desactivada; conserva estado entre el exterior y su interior.
- [N67](../../source/NVDAObjects/UIA/chromium.py#L67): avanza por hermanos después de cualquier rama; no baja dentro de términos o definiciones.
- [N68](../../source/NVDAObjects/UIA/chromium.py#L68): blanco entre definición del recorrido y su ejecución.
- [N69](../../source/NVDAObjects/UIA/chromium.py#L69): abre protección del recorrido frente a error COM.
- [N70](../../source/NVDAObjects/UIA/chromium.py#L70): inicia desde la lista con un nivel de envolturas permitido.
- [N71](../../source/NVDAObjects/UIA/chromium.py#L71): captura específicamente `COMError`, no todos los errores de programación.
- [N72](../../source/NVDAObjects/UIA/chromium.py#L72): abandona la corrección cuando falla el proveedor, sin publicar un resultado parcial como fiable.
- [N73](../../source/NVDAObjects/UIA/chromium.py#L73): devuelve conteo, incluido cero, solo si hubo definición; una lista con solo `listitem` conserva el conteo de la base mediante `None`.
- [N74-N75](../../source/NVDAObjects/UIA/chromium.py#L74-L75): blancos entre helpers de módulo.

#### Anotaciones de la normalización del flujo

- [N76](../../source/NVDAObjects/UIA/chromium.py#L76): tipa el flujo completo y retorno `None`; modifica los mismos diccionarios, no construye texto hablado.
- [N77](../../source/NVDAObjects/UIA/chromium.py#L77): documenta corrección de términos y supresión de nombres; la referencia normativa debe leerse con el matiz de versión indicado arriba.
- [N78](../../source/NVDAObjects/UIA/chromium.py#L78): declara una pila de parejas campo/bandera descriptiva; guarda contexto eliminado del diccionario público.
- [N79](../../source/NVDAObjects/UIA/chromium.py#L79): recorre comandos y fragmentos de texto en el orden del flujo.
- [N80](../../source/NVDAObjects/UIA/chromium.py#L80): diferencia comandos de los fragmentos textuales.
- [N81](../../source/NVDAObjects/UIA/chromium.py#L81): deja intacto el texto; esta corrección no traduce, concatena ni elimina palabras del contenido.
- [N82](../../source/NVDAObjects/UIA/chromium.py#L82): procesa un nuevo campo de control al entrar en su ámbito.
- [N83](../../source/NVDAObjects/UIA/chromium.py#L83): consume `_isDescriptionList`, con falso por defecto, para que la marca interna no llegue a consumidores; conserva su valor localmente.
- [N84](../../source/NVDAObjects/UIA/chromium.py#L84): inicia la búsqueda de la lista antecesora más próxima, no de cualquier lista descriptiva exterior.
- [N85](../../source/NVDAObjects/UIA/chromium.py#L85): abre la expresión generadora cuyos filtros aparecen a continuación.
- [N86](../../source/NVDAObjects/UIA/chromium.py#L86): produce la bandera del antecesor seleccionado, no su campo ni su nombre.
- [N87](../../source/NVDAObjects/UIA/chromium.py#L87): inspecciona la pila desde el antecesor más interior y desempaqueta campo y bandera.
- [N88](../../source/NVDAObjects/UIA/chromium.py#L88): considera solo antecesores con rol lista; una definición o un grupo intermedio no interrumpe la búsqueda.
- [N89](../../source/NVDAObjects/UIA/chromium.py#L89): cierra el generador pasado a `next`.
- [N90](../../source/NVDAObjects/UIA/chromium.py#L90): da falso si no hay lista antecesora; evita reclasificar elementos ordinarios fuera de listas descriptivas.
- [N91](../../source/NVDAObjects/UIA/chromium.py#L91): cierra `next`.
- [N92](../../source/NVDAObjects/UIA/chromium.py#L92): obtiene el rol actual sin exigir que todo campo contenga esa clave.
- [N93](../../source/NVDAObjects/UIA/chromium.py#L93): acepta un `TERM` ya reconocido sin requerir una lista descriptiva antecesora.
- [N94](../../source/NVDAObjects/UIA/chromium.py#L94): convierte un `LISTITEM` solo cuando la lista más cercana es descriptiva; preserva listas ordinarias anidadas.
- [N95](../../source/NVDAObjects/UIA/chromium.py#L95): cierra la condición compuesta y abre su bloque.
- [N96](../../source/NVDAObjects/UIA/chromium.py#L96): asigna `TERM` en el campo compartido con el flujo.
- [N97](../../source/NVDAObjects/UIA/chromium.py#L97): explica la duplicación que motiva la corrección: nombre derivado del contenido además del propio contenido. No aporta aquí una traza histórica.
- [N98](../../source/NVDAObjects/UIA/chromium.py#L98): expresa la intención normativa de descartar el nombre; es coherente con el borrador ARIA consultado, no con la tabla de ARIA 1.2.
- [N99](../../source/NVDAObjects/UIA/chromium.py#L99): quita `name` si existe, sin `KeyError`; el texto del flujo sigue siendo la fuente de lectura.
- [N100](../../source/NVDAObjects/UIA/chromium.py#L100): quita la orden de forzar ese nombre, evitando que la política heredada solicite un nombre redundante.
- [N101](../../source/NVDAObjects/UIA/chromium.py#L101): apila el campo ya normalizado y su marca, de modo que sus descendientes vean el contexto correcto.
- [N102](../../source/NVDAObjects/UIA/chromium.py#L102): reconoce la salida de control y comprueba que haya algo que desapilar.
- [N103](../../source/NVDAObjects/UIA/chromium.py#L103): restaura el contexto exterior al terminar ese control.
- [N104-N105](../../source/NVDAObjects/UIA/chromium.py#L104-L105): blancos antes de la clase TextInfo existente.

### Hunk 3.3: integración al construir cada campo

**Necesidad/origen:** sustituir `SizeOfSet` cuando hay evidencia descriptiva y evitar que `content` reemplace texto de un término reconocido. La [base web](../../source/NVDAObjects/UIA/web.py#L223-L264) ya decide nombres y contenido; la especialización corrige esa decisión antes de su posterior poda. **Por qué aquí:** este método dispone del objeto UIA del contenedor. El normalizador del flujo posterior necesita esa marca pero no dispone por sí solo del árbol UIA completo. Voz/braille deben recibir campos ya corregidos.

```diff
@@ -54,6 +142,14 @@ def _getControlFieldForUIAObject(self, obj, isEmbedded=False, startOfNode=False,
 		if field["role"] == controlTypes.Role.TABLE:  # noqa: SIM102
 			if not obj._getUIACacheablePropertyValue(UIAHandler.UIA_IsTablePatternAvailablePropertyId):
 				field["table-layout"] = True
+		if obj.role == controlTypes.Role.LIST:
+			descriptionListGroupCount = _getDescriptionListGroupCount(obj.UIAElement)
+			if descriptionListGroupCount is not None:
+				field["_isDescriptionList"] = True
+				field["_childcontrolcount"] = descriptionListGroupCount
+		if field.get("role") == controlTypes.Role.TERM:
+			for attribute in ("name", "content", "alwaysReportName"):
+				field.pop(attribute, None)
 		# Currently no way to tell if author has explicitly set name.
 		# Therefore always report the name if the control is not of a type that
 		# by definition uses its name for content.
```

- [N145](../../source/NVDAObjects/UIA/chromium.py#L145): limita la consulta de grupos a objetos con rol lista; no a cada término o cada fragmento de texto.
- [N146](../../source/NVDAObjects/UIA/chromium.py#L146): entrega el elemento UIA real del objeto al helper.
- [N147](../../source/NVDAObjects/UIA/chromium.py#L147): comprueba ausencia explícita, no valor verdadero, para no perder un conteo cero.
- [N148](../../source/NVDAObjects/UIA/chromium.py#L148): marca transitoriamente la lista para la normalización de descendientes.
- [N149](../../source/NVDAObjects/UIA/chromium.py#L149): sobrescribe el conteo heredado con grupos; mantiene el contrato común `_childcontrolcount`.
- [N150](../../source/NVDAObjects/UIA/chromium.py#L150): detecta términos ya reconocidos al crear el campo, antes del recorrido contextual posterior.
- [N151](../../source/NVDAObjects/UIA/chromium.py#L151): enumera nombre, contenido sustitutivo y orden de anuncio forzado; `content` es un atributo del campo, no el texto de la página.
- [N152](../../source/NVDAObjects/UIA/chromium.py#L152): elimina cada atributo si existe. Así la base no usa un `content` de término reconocido para sustituir descendientes; no hay aquí una corrección equivalente para `DEFINITION`.

### Hunk 3.4: normalización con contexto completo

**Necesidad/origen:** un `LISTITEM` aislado no dice si era un término nativo; el flujo sí contiene sus listas antecesoras. El contrato procede de `getTextWithFields` en la clase base. **Por qué aquí:** ejecutar después de `super()` preserva su lógica general de rangos, estados y espacios; ejecutar antes de consumidores evita duplicar la pila en voz/braille. Esta fase tardía quita nombres de términos convertidos; no recupera contenido que ya hubiera sido sustituido por la base, un límite distinto de la corrección temprana anterior.

```diff
@@ -63,6 +159,14 @@ def _getControlFieldForUIAObject(self, obj, isEmbedded=False, startOfNode=False,
 			field["alwaysReportName"] = True
 		return field
 
+	def getTextWithFields(
+		self,
+		formatConfig: dict | None = None,
+	) -> textInfos.TextInfo.TextWithFieldsT:
+		fields = super().getTextWithFields(formatConfig)
+		_normalizeDescriptionListTerms(fields)
+		return fields
+
 
 class ChromiumUIA(web.UIAWeb):
 	_TextInfo = ChromiumUIATextInfo
```

- [N162](../../source/NVDAObjects/UIA/chromium.py#L162): sobrescribe el punto de obtención de texto y campos; no crea una API alternativa para voz.
- [N163](../../source/NVDAObjects/UIA/chromium.py#L163): recibe la instancia TextInfo y mantiene la firma de método.
- [N164](../../source/NVDAObjects/UIA/chromium.py#L164): admite configuración opcional de formato, con el mismo valor por defecto de la base.
- [N165](../../source/NVDAObjects/UIA/chromium.py#L165): declara el tipo común de flujo devuelto; cierra la firma.
- [N166](../../source/NVDAObjects/UIA/chromium.py#L166): obtiene primero el flujo procesado por la base web, sin duplicar su implementación.
- [N167](../../source/NVDAObjects/UIA/chromium.py#L167): aplica la normalización contextual sobre ese flujo.
- [N168](../../source/NVDAObjects/UIA/chromium.py#L168): devuelve el mismo flujo, con los campos modificados y texto conservado por este helper.
- [N169](../../source/NVDAObjects/UIA/chromium.py#L169): blanco de separación respecto de la clase siguiente.

### Hunk 3.5: navegación por elementos de lista

**Necesidad/origen:** añadir términos que UIA no expone como `ListItem` al gesto ya existente. La base ya posee [iteración por tipos de nodo](../../source/UIAHandler/browseMode.py#L517-L539) y un iterador que respeta posiciones/direcciones. **Por qué aquí:** la consulta debe buscar propiedades del proveedor, no las etiquetas habladas ni el rol de un campo ya extraído. Se añade una alternativa exacta, no un parser de fallbacks en quicknav.

```diff
@@ -75,6 +179,22 @@ def _get_states(self) -> set[controlTypes.State]:
 
 
 class ChromiumUIATreeInterceptor(web.UIAWebTreeInterceptor):
+	def _iterNodesByType(self, nodeType, direction="next", pos=None):
+		if nodeType == "listItem":
+			clientObject = UIAHandler.handler.clientObject
+			condition = clientObject.createOrCondition(
+				clientObject.createPropertyCondition(
+					UIAHandler.UIA_ControlTypePropertyId,
+					UIAHandler.UIA_ListItemControlTypeId,
+				),
+				clientObject.createPropertyCondition(
+					UIAHandler.UIA_AriaRolePropertyId,
+					"term",
+				),
+			)
+			return UIAControlQuicknavIterator(nodeType, self, pos, condition, direction)
+		return super()._iterNodesByType(nodeType, direction=direction, pos=pos)
+
 	def _get_documentConstantIdentifier(self):
 		return self.rootNVDAObject.parent._getUIACacheablePropertyValue(UIAHandler.UIA_AutomationIdPropertyId)
 
```

- [N182](../../source/NVDAObjects/UIA/chromium.py#L182): sobrescribe búsqueda por tipo conservando dirección siguiente y posición opcional.
- [N183](../../source/NVDAObjects/UIA/chromium.py#L183): especializa solo `listItem`; no cambia lista, enlace, encabezado ni otros nodos.
- [N184](../../source/NVDAObjects/UIA/chromium.py#L184): utiliza el cliente UIA existente para construir condiciones nativas.
- [N185](../../source/NVDAObjects/UIA/chromium.py#L185): combina las dos condiciones mediante OR; no exige a los términos tener también control type de elemento de lista.
- [N186](../../source/NVDAObjects/UIA/chromium.py#L186): abre la condición que preserva los elementos ordinarios.
- [N187](../../source/NVDAObjects/UIA/chromium.py#L187): selecciona la propiedad de tipo de control UIA.
- [N188](../../source/NVDAObjects/UIA/chromium.py#L188): exige el valor `ListItem` para esa primera alternativa.
- [N189](../../source/NVDAObjects/UIA/chromium.py#L189): cierra la primera condición.
- [N190](../../source/NVDAObjects/UIA/chromium.py#L190): abre la alternativa nueva para términos ARIA.
- [N191](../../source/NVDAObjects/UIA/chromium.py#L191): consulta la propiedad `AriaRole` del proveedor, no `Role.TERM` de NVDA.
- [N192](../../source/NVDAObjects/UIA/chromium.py#L192): fija coincidencia exacta con `term`; no coincide por esta rama con `unsupported term` ni otras listas de tokens.
- [N193-N194](../../source/NVDAObjects/UIA/chromium.py#L193-L194): cierres de la condición ARIA y de la disyunción.
- [N195](../../source/NVDAObjects/UIA/chromium.py#L195): devuelve el iterador estándar con documento, posición, condición y dirección originales.
- [N196](../../source/NVDAObjects/UIA/chromium.py#L196): delega todos los demás tipos a la base, preservando sus búsquedas.
- [N197](../../source/NVDAObjects/UIA/chromium.py#L197): blanco antes del identificador de documento existente.

## 4. Mapa ARIA compartido

<!-- file: source/aria.py -->

### Hunk 4.1: atribución

**Necesidad/origen:** atribución de la modificación local del diccionario; no cambia la API. Se consigna en el archivo del mapa, no en sus consumidores.

```diff
diff --git a/source/aria.py b/source/aria.py
index 9f07a66ca..1cf11baef 100755
--- a/source/aria.py
+++ b/source/aria.py
@@ -1,5 +1,5 @@
 # A part of NonVisual Desktop Access (NVDA)
-# Copyright (C) 2009-2022 NV Access Limited, Leonard de Ruijter
+# Copyright (C) 2009-2026 NV Access Limited, Leonard de Ruijter, Juanjo M
 # This file is covered by the GNU General Public License.
 # See the file COPYING for more details.
 
```

- [A2](../../source/aria.py#L2): retira la atribución terminada en 2022.
- [N2](../../source/aria.py#L2): amplía a 2026 e incorpora Juanjo M sin modificar las condiciones de licencia.

### Hunk 4.2: reconocer el token `term`

**Necesidad/origen:** el nuevo rol interno necesita una traducción desde ARIA. El mapa ya tenía `definition`. [La clase UIAWeb](../../source/NVDAObjects/UIA/web.py#L364-L375) usa este diccionario para el primer rol reconocido y los nuevos helpers lo reutilizan. **Por qué aquí:** la correspondencia de vocabularios es compartida; no debe escribirse una tabla diferente en voz, braille y cada navegador. Añadirla también cambia qué token se considera reconocido en las búsquedas de fallbacks que consultan este mapa; no convierte automáticamente todos los nodos IA2 sin intervención de sus adaptadores.

```diff
@@ -55,6 +55,7 @@
 	"tab": controlTypes.Role.TAB,
 	"tablist": controlTypes.Role.TABCONTROL,
 	"tabpanel": controlTypes.Role.PROPERTYPAGE,
+	"term": controlTypes.Role.TERM,
 	"textbox": controlTypes.Role.EDITABLETEXT,
 	"toolbar": controlTypes.Role.TOOLBAR,
 	"tooltip": controlTypes.Role.TOOLTIP,
```

- [N58](../../source/aria.py#L58): relaciona el token ARIA `term` con `Role.TERM`; no altera `description`, que sigue siendo `STATICTEXT`, ni `definition`, ya `DEFINITION`.

## 5. Etiqueta braille del término

<!-- file: source/braille/labels.py -->

### Hunk 5.1: atribución

**Necesidad/origen:** reconocer la contribución a la tabla de etiquetas. La cabecera ya incluía 2026; no hay que inferir un cambio de rango de años ni un cambio de licencia. Pertenece al archivo de presentación braille modificado.

```diff
diff --git a/source/braille/labels.py b/source/braille/labels.py
index d909dd91a..52487e48b 100644
--- a/source/braille/labels.py
+++ b/source/braille/labels.py
@@ -1,5 +1,5 @@
 # A part of NonVisual Desktop Access (NVDA)
-# Copyright (C) 2008-2026 NV Access Limited, Joseph Lee, Babbage B.V., Davy Kager, Bram Duvigneau, Leonard de Ruijter, Burman's Computer and Education Ltd., Julien Cochuyt
+# Copyright (C) 2008-2026 NV Access Limited, Joseph Lee, Babbage B.V., Davy Kager, Bram Duvigneau, Leonard de Ruijter, Burman's Computer and Education Ltd., Julien Cochuyt, Juanjo M
 # This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
 # For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt
 
```

- [A2](../../source/braille/labels.py#L2): retira la lista previa de titulares manteniendo su contenido en la sustitución.
- [N2](../../source/braille/labels.py#L2): añade únicamente Juanjo M al final; conserva 2008-2026 y los demás nombres.

### Hunk 5.2: abreviatura localizable

**Necesidad/origen:** un rol nuevo también requiere una representación braille. El patrón existente de `DEFINITION` y `SWITCH` demuestra dónde se mantienen estas etiquetas. **Por qué aquí y no en el backend:** `trm` es una elección de presentación/idioma, mientras que el backend debe emitir `Role.TERM` independiente del dispositivo. No se crea una nueva tabla de traducción braille ni un indicador numérico nuevo.

```diff
@@ -163,6 +163,8 @@
 	controlTypes.Role.DEFINITION: _("definition"),
 	# Translators: Displayed in braille when an object is a switch control
 	controlTypes.Role.SWITCH: _("swtch"),
+	# Translators: Displayed in braille when an object is a term in a description list.
+	controlTypes.Role.TERM: _("trm"),
 }
 
 positiveStateLabels = {
```

- [N166](../../source/braille/labels.py#L166): ofrece contexto a traductores para desambiguar una abreviatura que, aislada, no explicaría su uso.
- [N167](../../source/braille/labels.py#L167): asigna `trm` a `TERM` mediante `_()`, siguiendo la localización de las demás etiquetas; la etiqueta de definición preexistente permanece.

## 6. Rol común `TERM`

<!-- file: source/controlTypes/role.py -->

### Hunk 6.1: atribución

**Necesidad/origen:** metadatos del módulo semántico modificado. Este hunk no decide ni anuncios ni navegación; no necesita reflejarse en cabeceras de consumidores sin cambios.

```diff
diff --git a/source/controlTypes/role.py b/source/controlTypes/role.py
index 22b0fcb3f..ccaeb411c 100644
--- a/source/controlTypes/role.py
+++ b/source/controlTypes/role.py
@@ -1,7 +1,7 @@
 # A part of NonVisual Desktop Access (NVDA)
 # This file is covered by the GNU General Public License.
 # See the file COPYING for more details.
-# Copyright (C) 2007-2022 NV Access Limited, Babbage B.V.
+# Copyright (C) 2007-2026 NV Access Limited, Babbage B.V., Juanjo M
 
 from enum import (
 	unique,
```

- [A4](../../source/controlTypes/role.py#L4): retira la atribución anterior hasta 2022.
- [N4](../../source/controlTypes/role.py#L4): actualiza a 2026 e incorpora Juanjo M, conservando los titulares anteriores.

### Hunk 6.2: identidad numérica compatible

**Necesidad/origen:** distinguir términos de `LISTITEM` y de `DEFINITION` en el modelo común. El [contrato del enum](../../source/controlTypes/role.py#L13-L24) pide continuar la secuencia para compatibilidad con complementos. **Por qué aquí:** un valor ad hoc en cada backend no daría un rol común a presentación, mapas y pruebas. No se renumera ningún miembro existente y no se añade un rol distinto para la lista contenedora.

```diff
@@ -202,6 +202,7 @@ def _displayStringLabels(self):
 	SUGGESTION = 156
 	DEFINITION = 157
 	SWITCH = 158
+	TERM = 159
 
 
 _roleLabels: dict[Role, str] = {
```

- [N205](../../source/controlTypes/role.py#L205): añade `TERM = 159` después de `SWITCH = 158`; `DEFINITION = 157` es contexto, no una adición de este diff. Preserva los números anteriores.

### Hunk 6.3: nombre del rol localizable

**Necesidad/origen:** el nuevo enum requiere texto legible a través de `displayString`; [su propiedad de etiquetas](../../source/controlTypes/role.py#L40-L42) ya apunta a `_roleLabels`. **Por qué aquí:** evita que cada backend o el módulo de voz escriba su propia palabra traducida. Esta etiqueta completa no sustituye la abreviatura específica braille.

```diff
@@ -532,6 +533,8 @@ def _displayStringLabels(self):
 	# Translators: The word role for a switch control
 	# I.e. a control that can be switched on or off.
 	Role.SWITCH: _("switch"),
+	# Translators: Identifies a term in a description list.
+	Role.TERM: _("term"),
 }
 
 
```

- [N536](../../source/controlTypes/role.py#L536): aclara a traductores que se trata del rol término de una lista descriptiva, no de plazo u otro significado de `term`.
- [N537](../../source/controlTypes/role.py#L537): registra la cadena traducible `term` en el catálogo común de etiquetas de rol.

## 7. Presentación compartida de términos y definiciones

<!-- file: source/textInfos/__init__.py -->

### Hunk 7.1: atribución

**Necesidad/origen:** actualización de titulares en una cabecera que ocupa varias líneas. Se mantiene en el módulo de campos; no se modifican cabeceras de voz/braille porque no cambian sus algoritmos.

```diff
diff --git a/source/textInfos/__init__.py b/source/textInfos/__init__.py
index 8cf562724..391aca149 100755
--- a/source/textInfos/__init__.py
+++ b/source/textInfos/__init__.py
@@ -1,6 +1,6 @@
 # A part of NonVisual Desktop Access (NVDA)
 # Copyright (C) 2006-2026 NV Access Limited, Babbage B.V., Accessolutions, Julien Cochuyt, Cyrille Bougot,
-# Leonard de Ruijter
+# Leonard de Ruijter, Juanjo M
 # This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
 # For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt
 
```

- [A3](../../source/textInfos/__init__.py#L3): retira la continuación antigua del copyright, no un comentario de implementación.
- [N3](../../source/textInfos/__init__.py#L3): añade Juanjo M a esa continuación; el rango 2006-2026 del contexto queda intacto.

### Hunk 7.2: respetar `reportLists`

**Necesidad/origen:** al dejar de ser `LISTITEM`, términos y definiciones ya no entran en la condición anterior de listas de solo lectura. Sin una condición propia, podrían seguir anunciándose aunque el usuario desactive listas. El origen verificable es el contrato de verbosidad de `getPresentationCategory` y el test nuevo con `reportLists=False`. **Por qué aquí:** esta clasificación es compartida; ocultar solo la palabra en voz no aplicaría coherentemente la preferencia a braille. La condición nueva no exige `READONLY`, a diferencia de la anterior.

```diff
@@ -133,6 +133,10 @@ def getPresentationCategory(
 				and controlTypes.State.READONLY in states
 				and not formatConfig["reportLists"]
 			)
+			or (
+				role in (controlTypes.Role.TERM, controlTypes.Role.DEFINITION)
+				and not formatConfig["reportLists"]
+			)
 			or (role == controlTypes.Role.ARTICLE and not formatConfig["reportArticles"])
 			or (role == controlTypes.Role.MARKED_CONTENT and not formatConfig["reportHighlight"])
 			or (
```

- [N136](../../source/textInfos/__init__.py#L136): añade otra causa de tratamiento como disposición, mediante OR con las preferencias existentes.
- [N137](../../source/textInfos/__init__.py#L137): limita esta causa a `TERM` y `DEFINITION`; no suprime otros roles de contenido.
- [N138](../../source/textInfos/__init__.py#L138): liga ambos roles al mismo ajuste `reportLists`, sin añadir una nueva opción de interfaz.
- [N139](../../source/textInfos/__init__.py#L139): cierra la condición de esos dos roles; la devolución de `PRESCAT_LAYOUT` permanece en el bloque común existente.

### Hunk 7.3: categoría marcador

**Necesidad/origen:** los roles deben ser perceptibles al entrar en el campo, sin tratarlos como contenedores con anuncios de salida propios. [Voz interpreta marcadores como anuncio de entrada](../../source/speech/speech.py#L2384-L2402). Las nuevas pruebas fijan `PRESCAT_MARKER` al informar listas. **Por qué aquí:** es una política semántica de campos, no una peculiaridad de una voz, navegador o pantalla braille. Afecta también a los `DEFINITION` que ya pudieran existir en otros productores.

```diff
@@ -193,6 +197,8 @@ def getPresentationCategory(
 			controlTypes.Role.ENDNOTE,
 			controlTypes.Role.EMBEDDEDOBJECT,
 			controlTypes.Role.MATH,
+			controlTypes.Role.TERM,
+			controlTypes.Role.DEFINITION,
 		) or (extraDetail and role == controlTypes.Role.LISTITEM):
 			return self.PRESCAT_MARKER
 		elif role in (controlTypes.Role.APPLICATION, controlTypes.Role.DIALOG):
```

- [N200](../../source/textInfos/__init__.py#L200): incluye términos entre los roles marcador, sin exigir `extraDetail` como hace la alternativa de `LISTITEM`.
- [N201](../../source/textInfos/__init__.py#L201): aplica la misma categoría a definiciones; la preferencia anterior sigue pudiendo degradarlos a disposición antes de llegar aquí.

## 8. MSHTML: quicknav sin definiciones

<!-- file: source/virtualBuffers/MSHTML.py -->

### Hunk 8.1: atribución

**Necesidad/origen:** atribución del cambio del filtro en el buffer MSHTML. No corresponde a un cambio de implementación nativa ni a los consumidores finales.

```diff
diff --git a/source/virtualBuffers/MSHTML.py b/source/virtualBuffers/MSHTML.py
index 855b444e1..2acbd62bc 100644
--- a/source/virtualBuffers/MSHTML.py
+++ b/source/virtualBuffers/MSHTML.py
@@ -1,7 +1,7 @@
 # A part of NonVisual Desktop Access (NVDA)
 # This file is covered by the GNU General Public License.
 # See the file COPYING for more details.
-# Copyright (C) 2009-2024 NV Access Limited, Babbage B.V., Accessolutions, Julien Cochuyt, Cyrille Bougot
+# Copyright (C) 2009-2026 NV Access Limited, Babbage B.V., Accessolutions, Julien Cochuyt, Cyrille Bougot, Juanjo M
 
 from comtypes import COMError  # noqa: I001
 from . import VirtualBuffer, VirtualBufferTextInfo, VBufStorage_findMatch_word, VBufStorage_findMatch_notEmpty
```

- [A4](../../source/virtualBuffers/MSHTML.py#L4): retira el copyright hasta 2024.
- [N4](../../source/virtualBuffers/MSHTML.py#L4): actualiza hasta 2026 e incorpora Juanjo M sin cambios en imports o licencia.

### Hunk 8.2: cambiar el predicado de búsqueda, no el texto hablado

**Necesidad/origen:** I debe ir a elementos ordinarios o términos y no detenerse en cada definición. **Por qué aquí:** el filtro se ejecuta sobre `IHTMLDOMNode::nodeName` almacenado; la búsqueda no consulta el rol normalizado para hablar. Por ello la modificación del diccionario del objeto no basta para cambiar quicknav. No añade conteo de grupos MSHTML, ni búsqueda genérica de todos los elementos con `role="term"`.

```diff
@@ -427,7 +427,7 @@ def _searchableAttribsForNodeType(self, nodeType):
 		elif nodeType == "list":
 			attrs = {"IHTMLDOMNode::nodeName": ["UL", "OL", "DL"]}
 		elif nodeType == "listItem":
-			attrs = {"IHTMLDOMNode::nodeName": ["LI", "DD", "DT"]}
+			attrs = {"IHTMLDOMNode::nodeName": ["LI", "DT"]}
 		elif nodeType == "blockQuote":
 			attrs = {"IHTMLDOMNode::nodeName": ["BLOCKQUOTE"]}
 		elif nodeType == "annotation":
```

- [A430](../../source/virtualBuffers/MSHTML.py#L430): retira el conjunto que incluía `DD` y por tanto hacía navegables las definiciones con I.
- [N430](../../source/virtualBuffers/MSHTML.py#L430): conserva `LI` y `DT` como coincidencias por etiqueta; la búsqueda de contenedores `UL`/`OL`/`DL` del contexto no cambia.

## 9. Buffer IA2 Python: normalización y filtros

<!-- file: source/virtualBuffers/gecko_ia2.py -->

### Hunk 9.1: atribución

**Necesidad/origen:** reconocimiento del cambio de esta capa; copyright ya fechado hasta 2026 en la línea anterior. No cambia el backend seleccionado ni los consumidores.

```diff
diff --git a/source/virtualBuffers/gecko_ia2.py b/source/virtualBuffers/gecko_ia2.py
index db439d0af..d02091c9e 100755
--- a/source/virtualBuffers/gecko_ia2.py
+++ b/source/virtualBuffers/gecko_ia2.py
@@ -1,6 +1,6 @@
 # A part of NonVisual Desktop Access (NVDA)
 # Copyright (C) 2008-2026 NV Access Limited, Babbage B.V., Mozilla Corporation, Accessolutions,
-# Julien Cochuyt, Noelia Ruiz Martínez, Leonard de Ruijter
+# Julien Cochuyt, Noelia Ruiz Martínez, Leonard de Ruijter, Juanjo M
 # This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
 # For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt
 
```

- [A3](../../source/virtualBuffers/gecko_ia2.py#L3): retira la continuación antigua de los titulares.
- [N3](../../source/virtualBuffers/gecko_ia2.py#L3): añade Juanjo M a esa lista sin modificar el rango de años ni licencia.

### Hunk 9.2: roles nativos, precedencia y puente de conteo

**Necesidad:** el rol IA2 numérico no basta para diferenciar `dt`/`dd`, y el conteo nativo específico todavía tiene una clave propia. **Origen:** semántica HTML, precedencia de roles reconocidos y contrato común `_childcontrolcount`. **Por qué aquí:** `_normalizeControlField` ya adapta propiedades IA2 y luego [entrega `role` y `states` al campo](../../source/virtualBuffers/gecko_ia2.py#L220-L236). Es la frontera correcta entre datos específicos del proveedor y consumidores comunes. Se preserva la regla previa de `blockquote`.

No confundir este ajuste de etiquetas con una traducción general de cualquier rol ARIA IA2: un elemento que no sea `dt` o `dd` no entra en las dos ramas nuevas solo por tener `xml-roles="term"`. El filtro quicknav posterior y esta normalización son distintos. Tampoco el contador C++ por etiqueta inspecciona `primaryXmlRole`: sus criterios y los de presentación no son idénticos.

```diff
@@ -128,8 +128,20 @@ def _normalizeControlField(self, attrs):
 			attrs["placeholder"] = placeholder
 
 		role = IAccessibleHandler.NVDARoleFromAttr(attrs["IAccessible::role"])
-		if attrs.get("IAccessible2::attribute_tag", "").lower() == "blockquote":
+		htmlTag = attrs.get("IAccessible2::attribute_tag", "").lower()
+		xmlRoles = attrs.get("IAccessible2::attribute_xml-roles", "").split(" ")
+		primaryXmlRole = next((xmlRole for xmlRole in xmlRoles if xmlRole in aria.ariaRolesToNVDARoles), None)
+		if htmlTag == "blockquote":
 			role = controlTypes.Role.BLOCKQUOTE
+		elif htmlTag == "dt" and primaryXmlRole in (None, "term"):
+			role = controlTypes.Role.TERM
+		elif htmlTag == "dd" and primaryXmlRole in (None, "description", "definition"):
+			role = controlTypes.Role.DEFINITION
+		if role in (controlTypes.Role.TERM, controlTypes.Role.DEFINITION):
+			attrs.pop("name", None)
+		descriptionListGroupCount = attrs.get("description-list-group-count")
+		if descriptionListGroupCount is not None:
+			attrs["_childcontrolcount"] = descriptionListGroupCount
 
 		states = IAccessibleHandler.getStatesSetFromIAccessibleAttrs(attrs)
 		states |= IAccessibleHandler.getStatesSetFromIAccessible2Attrs(attrs)
```

- [A131](../../source/virtualBuffers/gecko_ia2.py#L131): retira la consulta en línea de etiqueta usada solo por `blockquote`; se extrae para reutilizarla, no se elimina esa semántica.
- [N131](../../source/virtualBuffers/gecko_ia2.py#L131): guarda etiqueta normalizada en minúsculas, con cadena vacía por defecto.
- [N132](../../source/virtualBuffers/gecko_ia2.py#L132): adelanta la lectura de `xml-roles`, separando por espacio literal; esta versión no aplica `.lower()` ni el `.split()` general del helper UIA.
- [N133](../../source/virtualBuffers/gecko_ia2.py#L133): elige el primer token conocido por NVDA, con `None` si no existe; `button term` preserva `button`, mientras `unsupported term` permite `term`.
- [N134](../../source/virtualBuffers/gecko_ia2.py#L134): conserva la comprobación de `blockquote`, ahora sobre la variable compartida.
- [N136](../../source/virtualBuffers/gecko_ia2.py#L136): solo trata `dt` como término cuando no hay override reconocido o el primario es `term`.
- [N137](../../source/virtualBuffers/gecko_ia2.py#L137): sustituye el rol genérico derivado de IA2 por el nuevo rol de término en ese caso.
- [N138](../../source/virtualBuffers/gecko_ia2.py#L138): acepta `dd` sin override reconocido o con `description`/`definition`; no pisa un primario conocido distinto.
- [N139](../../source/virtualBuffers/gecko_ia2.py#L139): asigna el rol NVDA de definición; aquí sí se trata la etiqueta `dd` con `description` como `DEFINITION`.
- [N140](../../source/virtualBuffers/gecko_ia2.py#L140): aplica supresión de nombre a los roles finales de término o definición calculados hasta ese punto.
- [N141](../../source/virtualBuffers/gecko_ia2.py#L141): quita el atributo `name`, con ausencia tolerada; no borra texto descendiente ni atributos `content`/`alwaysReportName`. La intención evita duplicación y sigue el criterio de nombres del borrador ARIA, con el límite normativo ya señalado.
- [N142](../../source/virtualBuffers/gecko_ia2.py#L142): obtiene la clave específica escrita por el backend C++ después de renderizar hijos.
- [N143](../../source/virtualBuffers/gecko_ia2.py#L143): distingue ausencia de un valor cero serializado; no depende de la veracidad del conteo.
- [N144](../../source/virtualBuffers/gecko_ia2.py#L144): reemplaza el conteo estructural por el semántico para los consumidores. Mantiene la cadena recibida; voz/braille convierten a entero al usarla.

### Hunk 9.3: eliminar la lectura ahora duplicada

**Necesidad/origen:** `xmlRoles` ya se calculó antes de asignar roles de `dt`/`dd`; volver a leerlo sería redundante. **Por qué aquí:** las reglas posteriores de landmarks siguen en el mismo normalizador y necesitan la misma lista. No se trasladan landmarks a otra capa ni se altera su prioridad.

```diff
@@ -176,7 +188,6 @@ def _normalizeControlField(self, attrs):
 			) is not None:
 				states.add(linkType)
 		level = attrs.get("IAccessible2::attribute_level", "")
-		xmlRoles = attrs.get("IAccessible2::attribute_xml-roles", "").split(" ")
 		landmark = next((xr for xr in xmlRoles if xr in aria.landmarkRoles), None)
 		if landmark and role != controlTypes.Role.LANDMARK and landmark != xmlRoles[0]:
 			# Ignore the landmark role
```

- [A179](../../source/virtualBuffers/gecko_ia2.py#L179): elimina exclusivamente la asignación repetida, trasladada al comienzo del procesamiento de roles. Las referencias posteriores a `xmlRoles` permanecen válidas; el ancla actual no representa la ubicación antigua exacta.

### Hunk 9.4: alternativas de quicknav IA2

**Necesidad/origen:** el filtro exclusivo por `ROLE_SYSTEM_LISTITEM` no alcanza todos los términos, por lo que se añaden etiqueta nativa y rol ARIA expuesto como marco de texto. **Por qué aquí:** [el motor de filtros](../../source/virtualBuffers/__init__.py#L58-L95) entiende alternativas y coincidencias por palabra sobre atributos nativos; cambiar el texto de voz no cambiaría las posiciones encontradas.

El objetivo es LI más términos, no añadir definiciones. Pero el filtro mantiene toda la alternativa `ROLE_SYSTEM_LISTITEM`: no contiene una exclusión absoluta por etiqueta `dd`. Si un proveedor expusiera una definición con ese rol, también cumpliría esa alternativa. Igualmente, la coincidencia por palabra `term` no aplica por sí sola la precedencia del primer rol reconocido. Estas son fronteras de la implementación literal, no promesas generales sobre todas las versiones de navegadores.

```diff
@@ -448,7 +459,14 @@ def _searchableAttribsForNodeType(self, nodeType):
 		elif nodeType == "list":
 			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_LIST]}
 		elif nodeType == "listItem":
-			attrs = {"IAccessible::role": [oleacc.ROLE_SYSTEM_LISTITEM]}
+			attrs = [
+				{"IAccessible::role": [oleacc.ROLE_SYSTEM_LISTITEM]},
+				{"IAccessible2::attribute_tag": ["dt"], "IAccessible2::attribute_xml-roles": [None]},
+				{
+					"IAccessible::role": [IA2.IA2_ROLE_TEXT_FRAME],
+					"IAccessible2::attribute_xml-roles": [VBufStorage_findMatch_word("term")],
+				},
+			]
 		elif nodeType == "button":
 			attrs = {
 				"IAccessible::role": [
```

- [A451](../../source/virtualBuffers/gecko_ia2.py#L451): retira la forma de filtro único, no la compatibilidad con elementos ordinarios de lista.
- [N462](../../source/virtualBuffers/gecko_ia2.py#L462): cambia a lista de alternativas, que el motor une mediante OR.
- [N463](../../source/virtualBuffers/gecko_ia2.py#L463): conserva el predicado anterior de rol `LISTITEM` como primera alternativa.
- [N464](../../source/virtualBuffers/gecko_ia2.py#L464): añade `dt` sin `xml-roles`; dentro del diccionario ambas propiedades se exigen conjuntamente. `[None]` expresa ausencia para el serializador de búsqueda, no cualquier override.
- [N465](../../source/virtualBuffers/gecko_ia2.py#L465): abre el diccionario de una tercera alternativa conjunta; esta apertura introduce la agrupación AND, por eso se comenta individualmente.
- [N466](../../source/virtualBuffers/gecko_ia2.py#L466): restringe esa tercera alternativa al rol IA2 de marco de texto.
- [N467](../../source/virtualBuffers/gecko_ia2.py#L467): exige `term` como palabra del atributo `xml-roles` mediante la clase especial de coincidencia; no es la igualdad exacta usada en UIA.
- [N468-N469](../../source/virtualBuffers/gecko_ia2.py#L468-L469): cierres del diccionario de la tercera alternativa y de la lista de alternativas.

## 10. Prueba de sistema Chrome: experiencia completa de lectura

<!-- file: tests/system/robot/chromeTests.py -->

### Hunk 10.1: atribución

**Necesidad/origen:** metadatos de autoría de la nueva prueba. Ya figuraba 2026. Se modifica la cabecera de la biblioteca de pruebas, no la implementación bajo prueba.

```diff
diff --git a/tests/system/robot/chromeTests.py b/tests/system/robot/chromeTests.py
index 9ec9898c4..933a77f4d 100644
--- a/tests/system/robot/chromeTests.py
+++ b/tests/system/robot/chromeTests.py
@@ -1,5 +1,5 @@
 # A part of NonVisual Desktop Access (NVDA)
-# Copyright (C) 2020-2026 NV Access Limited, Leonard de Ruijter, Cyrille Bougot
+# Copyright (C) 2020-2026 NV Access Limited, Leonard de Ruijter, Cyrille Bougot, Juanjo M
 # This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
 # For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt
 
```

- [A2](../../tests/system/robot/chromeTests.py#L2): retira la lista previa de titulares.
- [N2](../../tests/system/robot/chromeTests.py#L2): añade Juanjo M, conservando autores y rango 2020-2026.

### Hunk 10.2: fixture, cinco saltos y lectura secuencial

**Necesidad/origen:** un test de diccionarios no demuestra que Chrome, buffer, gestos y voz produzcan juntos lo esperado. Este test materializa el requisito en tres grupos: Student/Judy; Staff+Teacher/Melissa+Robin; Color+Colour/A visual characteristic. Son cinco términos y cuatro definiciones, **tres asociaciones**, no nueve elementos ni la mitad del número de nodos. **Por qué aquí:** [la biblioteca de pruebas Chrome](../../tests/system/robot/chromeTests.py#L6-L36) ya proporciona `_chrome` y aserciones Robot; es una prueba de consumidor de extremo a extremo, no código de producción encargado de deducir roles.

La fixture mezcla hijos directos y envolturas, comportamiento tratado por el algoritmo de extracción HTML, pero no debe describirse como ejemplo del modelo de contenido estricto que elige entre grupos directos o `div`. Las salidas con doble espacio siguen [la convención de separación de voz de esta biblioteca](../../tests/system/robot/chromeTests.py#L30-L36). El orden «Student term» en quicknav frente a «term Student» con flechas resulta de la política existente de `OutputReason`, no de reordenar el HTML.

**Alcance de la evidencia:** es código de una prueba, no un registro de ejecución de esta tarea. La ruta Chrome ordinaria es IA2, como se justificó antes; no valida el backend UIA real. No hay aserciones braille, Firefox, MSHTML, fallo COM, ni configuración de listas desactivada en este test. Tampoco se pulsa I una sexta vez para comprobar ausencia de más destinos.

```diff
@@ -884,6 +884,62 @@ def test_i7562():
 	)
 
 
+def test_definitionList_semantics() -> None:
+	"""Definition lists should expose their terms, definitions, and semantic item count."""
+	_chrome.prepareChrome(
+		"""
+			<h1>Description list</h1>
+			<dl>
+				<dt>Student</dt>
+				<dd>Judy</dd>
+				<div>
+					<dt>Staff</dt>
+					<dt>Teacher</dt>
+					<dd>Melissa</dd>
+					<dd>Robin</dd>
+				</div>
+				<div>
+					<dt>Color</dt>
+					<dt>Colour</dt>
+					<dd>A visual characteristic</dd>
+				</div>
+			</dl>
+			<p>After list</p>
+		""",
+	)
+	actualSpeech = [_chrome.getSpeechAfterKey("h")]
+	actualQuickNavSpeech = [_chrome.getSpeechAfterKey("i") for _ in range(5)]
+	_builtIn.should_be_equal(
+		actualQuickNavSpeech,
+		[
+			"list  with 3 items  Student  term",
+			"Staff  term",
+			"Teacher  term",
+			"Color  term",
+			"Colour  term",
+		],
+	)
+	actualSpeech = [_chrome.getSpeechAfterKey("shift+h")]
+	for _ in range(10):
+		actualSpeech.append(_chrome.getSpeechAfterKey("downArrow"))
+	_builtIn.should_be_equal(
+		actualSpeech,
+		[
+			"Description list  heading  level 1",
+			"list  with 3 items  term  Student",
+			"definition  Judy",
+			"term  Staff",
+			"term  Teacher",
+			"definition  Melissa",
+			"definition  Robin",
+			"term  Color",
+			"term  Colour",
+			"definition  A visual characteristic",
+			"out of list  After list",
+		],
+	)
+
+
 def test_pr11606():
 	"""
 	Announce the correct line when placed at the end of a link at the end of a list item in a contenteditable
```

- [N887](../../tests/system/robot/chromeTests.py#L887): declara el keyword Python de prueba con retorno `None`; Robot lo invocará por su nombre.
- [N888](../../tests/system/robot/chromeTests.py#L888): documenta los tres objetivos: términos, definiciones y conteo semántico.
- [N889](../../tests/system/robot/chromeTests.py#L889): prepara un caso HTML mediante la infraestructura Chrome existente.
- [N890](../../tests/system/robot/chromeTests.py#L890): abre el literal multilínea que contiene la fixture; no es un docstring de función.
- [N891](../../tests/system/robot/chromeTests.py#L891): crea un encabezado único anterior a la lista para colocar y recuperar el cursor con H.
- [N892](../../tests/system/robot/chromeTests.py#L892): abre la lista descriptiva que debe anunciar tres grupos.
- [N893](../../tests/system/robot/chromeTests.py#L893): añade el primer término directo, Student; es el primer destino de I.
- [N894](../../tests/system/robot/chromeTests.py#L894): añade Judy como definición directa, completando el primer grupo sin ser destino deseado de I.
- [N895](../../tests/system/robot/chromeTests.py#L895): abre una envoltura directa para ejercitar el descenso permitido.
- [N896](../../tests/system/robot/chromeTests.py#L896): añade Staff, primer nombre del segundo grupo.
- [N897](../../tests/system/robot/chromeTests.py#L897): añade Teacher como segundo nombre consecutivo; debe tener destino propio pero no sumar otro grupo.
- [N898](../../tests/system/robot/chromeTests.py#L898): añade Melissa, primera definición del segundo grupo, que produce su incremento de conteo.
- [N899](../../tests/system/robot/chromeTests.py#L899): añade Robin, segunda definición del mismo grupo; comprueba que no vuelve a sumar.
- [N900](../../tests/system/robot/chromeTests.py#L900): cierra la primera envoltura, delimitando qué hijos se visitan en la recursión.
- [N901](../../tests/system/robot/chromeTests.py#L901): abre una segunda envoltura hermana, no anidada dentro de la primera.
- [N902](../../tests/system/robot/chromeTests.py#L902): añade Color como primer nombre del tercer grupo.
- [N903](../../tests/system/robot/chromeTests.py#L903): añade Colour como nombre alternativo, manteniendo un solo grupo.
- [N904](../../tests/system/robot/chromeTests.py#L904): aporta la definición común a ambos nombres; completa el tercer grupo.
- [N905](../../tests/system/robot/chromeTests.py#L905): cierra la segunda envoltura.
- [N906](../../tests/system/robot/chromeTests.py#L906): cierra la lista, permitiendo probar un anuncio de salida al avanzar al párrafo siguiente.
- [N907](../../tests/system/robot/chromeTests.py#L907): agrega contenido fuera de la lista como destino final verificable.
- [N908-N909](../../tests/system/robot/chromeTests.py#L908-L909): cierres del literal HTML y de la llamada de preparación, con coma de argumento multilínea.
- [N910](../../tests/system/robot/chromeTests.py#L910): pulsa H para situarse antes de la lista y recoge voz. Esta primera asignación a `actualSpeech` se sobrescribe después, sin aserción propia; el efecto relevante es mover el cursor.
- [N911](../../tests/system/robot/chromeTests.py#L911): recoge cinco respuestas a I, una por cada término; `_` indica que no se usa el índice de repetición.
- [N912](../../tests/system/robot/chromeTests.py#L912): inicia la comparación exacta de la secuencia quicknav mediante Robot.
- [N913](../../tests/system/robot/chromeTests.py#L913): pasa como resultado real la lista capturada, no una cadena concatenada.
- [N914](../../tests/system/robot/chromeTests.py#L914): abre la lista ordenada de resultados esperados.
- [N915](../../tests/system/robot/chromeTests.py#L915): exige anuncio de lista con tres elementos semánticos y Student seguido del rol término; detecta tanto conteo erróneo como falta de rol o duplicación textual.
- [N916](../../tests/system/robot/chromeTests.py#L916): exige que el segundo salto vaya a Staff, saltándose Judy.
- [N917](../../tests/system/robot/chromeTests.py#L917): exige otro destino para Teacher aunque comparta grupo con Staff.
- [N918](../../tests/system/robot/chromeTests.py#L918): exige Color a continuación, sin paradas intermedias en Melissa o Robin.
- [N919](../../tests/system/robot/chromeTests.py#L919): exige el término alternativo Colour como quinto destino.
- [N920-N921](../../tests/system/robot/chromeTests.py#L920-L921): cierres de expectativas quicknav y de su aserción.
- [N922](../../tests/system/robot/chromeTests.py#L922): vuelve al encabezado con Mayús+H e inicia una captura nueva para lectura por líneas.
- [N923](../../tests/system/robot/chromeTests.py#L923): programa diez avances: nueve nodos textuales término/definición y el párrafo exterior.
- [N924](../../tests/system/robot/chromeTests.py#L924): captura la respuesta de cada flecha abajo; comprueba la experiencia secuencial y no solo búsquedas semánticas.
- [N925](../../tests/system/robot/chromeTests.py#L925): inicia la comparación exacta de esa segunda secuencia.
- [N926](../../tests/system/robot/chromeTests.py#L926): pasa la captura que contiene el encabezado y diez avances.
- [N927](../../tests/system/robot/chromeTests.py#L927): abre los once resultados esperados en orden.
- [N928](../../tests/system/robot/chromeTests.py#L928): valida encabezado, texto y nivel al reposicionarse.
- [N929](../../tests/system/robot/chromeTests.py#L929): valida lista con tres grupos y rol término antes de Student al moverse con flecha, distinto del orden quicknav.
- [N930](../../tests/system/robot/chromeTests.py#L930): valida que Judy sí se lee secuencialmente y se identifica como definición.
- [N931](../../tests/system/robot/chromeTests.py#L931): valida Staff como término dentro de la primera envoltura.
- [N932](../../tests/system/robot/chromeTests.py#L932): valida Teacher como segundo término del mismo grupo.
- [N933](../../tests/system/robot/chromeTests.py#L933): valida Melissa como definición, sin repetir el contenedor lista.
- [N934](../../tests/system/robot/chromeTests.py#L934): valida la segunda definición Robin sin perder su rol.
- [N935](../../tests/system/robot/chromeTests.py#L935): valida Color al entrar en la segunda envoltura.
- [N936](../../tests/system/robot/chromeTests.py#L936): valida Colour como término alternativo separado.
- [N937](../../tests/system/robot/chromeTests.py#L937): valida la definición compartida completa y su rol.
- [N938](../../tests/system/robot/chromeTests.py#L938): exige «out of list» y el párrafo exterior; no exige anuncios «out of term» o «out of definition».
- [N939-N940](../../tests/system/robot/chromeTests.py#L939-L940): cierres de la lista esperada y de la segunda aserción.
- [N941-N942](../../tests/system/robot/chromeTests.py#L941-L942): blancos entre funciones de pruebas; la prueba siguiente no cambia.

## 11. Registro de la prueba en Robot

<!-- file: tests/system/robot/chromeTests.robot -->

### Hunk 11.1: atribución

**Necesidad/origen:** atribuir la incorporación del caso a la suite. La prueba Python y su registro Robot son archivos distintos; ambos reciben autoría, sin modificar setup/teardown.

```diff
diff --git a/tests/system/robot/chromeTests.robot b/tests/system/robot/chromeTests.robot
index 87c4dcd02..189d74255 100644
--- a/tests/system/robot/chromeTests.robot
+++ b/tests/system/robot/chromeTests.robot
@@ -1,5 +1,5 @@
 # A part of NonVisual Desktop Access (NVDA)
-# Copyright (C) 2019-2026 NV Access Limited, Cyrille Bougot, Leonard de Ruijter
+# Copyright (C) 2019-2026 NV Access Limited, Cyrille Bougot, Leonard de Ruijter, Juanjo M
 # This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
 # For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt
 
```

- [A2](../../tests/system/robot/chromeTests.robot#L2): retira la lista de titulares anterior.
- [N2](../../tests/system/robot/chromeTests.robot#L2): añade Juanjo M, conservando el rango de años y autores existentes.

### Hunk 11.2: caso ejecutable y etiqueta de selección

**Necesidad/origen:** una función en la biblioteca no se convierte por sí sola en un caso de esta suite. [Robot ya importa la biblioteca y define setup/teardown](../../tests/system/robot/chromeTests.robot#L6-L17), y [agrupa las pruebas de listas](../../tests/system/robot/chromeTests.robot#L36-L48). **Por qué aquí:** este archivo es la capa de descubrimiento/selección; no corresponde a código de producción ni a un test unitario. Hereda el perfil estándar sin forzar UIA.

```diff
@@ -46,6 +46,10 @@ i7562
 	[Documentation]	List should not be announced on every line of a ul in a contenteditable
 	[Tags]	chrome_list
 	test_i7562
+Definition list semantics
+	[Documentation]	Definition lists expose terms, definitions, and a semantic item count.
+	[Tags]	chrome_list
+	test_definitionList_semantics
 pr11606
 	[Documentation]	Announce the correct line when placed at the end of a link at the end of a list item in a contenteditable
 	[Tags]	chrome_list
```

- [N49](../../tests/system/robot/chromeTests.robot#L49): declara un caso Robot con nombre legible en informes, separado del caso anterior.
- [N50](../../tests/system/robot/chromeTests.robot#L50): explica su objetivo en metadatos de documentación; no constituye una aserción adicional.
- [N51](../../tests/system/robot/chromeTests.robot#L51): lo incluye en `chrome_list`, como sus vecinos, para selección de la suite/grupo.
- [N52](../../tests/system/robot/chromeTests.robot#L52): invoca el keyword Python añadido; es el enlace que hace ejecutable la fixture en este caso Robot.

## 12. Tests unitarios de categoría de presentación

<!-- file: tests/unit/test_textInfos.py -->

### Hunk 12.1: atribución

**Necesidad/origen:** metadatos de la ampliación del módulo de pruebas de campos. No modifica ninguna prueba previa ni el código de implementación.

```diff
diff --git a/tests/unit/test_textInfos.py b/tests/unit/test_textInfos.py
index 0cdee9ffb..8d406455d 100644
--- a/tests/unit/test_textInfos.py
+++ b/tests/unit/test_textInfos.py
@@ -1,5 +1,5 @@
 # A part of NonVisual Desktop Access (NVDA)
-# Copyright (C) 2018-2026 NV Access Limited, Babbage B.V., Leonard de Ruijter
+# Copyright (C) 2018-2026 NV Access Limited, Babbage B.V., Leonard de Ruijter, Juanjo M
 # This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
 # For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt
 
```

- [A2](../../tests/unit/test_textInfos.py#L2): retira la atribución anterior de las pruebas.
- [N2](../../tests/unit/test_textInfos.py#L2): añade Juanjo M sin cambiar 2018-2026 ni la licencia.

### Hunk 12.2: dependencia de los roles comunes

**Necesidad/origen:** los casos nuevos parametrizan `TERM` y `DEFINITION`; deben usar sus valores reales. **Por qué aquí:** importar el modelo semántico en el test evita constantes numéricas duplicadas y permite probar la API de `ControlField` sin un navegador ni un sintetizador.

```diff
@@ -9,6 +9,7 @@
 from unittest.mock import patch
 
 import config
+import controlTypes
 from .textProvider import BasicTextInfo, BasicTextProvider, MockBlackBoxTextInfo
 import textInfos
 from textInfos.offsets import Offsets
```

- [N12](../../tests/unit/test_textInfos.py#L12): importa `controlTypes` para construir campos y subcasos con los roles reales, no un doble del enum.

### Hunk 12.3: dos ajustes por dos roles

**Necesidad/origen:** regresión de verbosidad al abandonar `LISTITEM`, y categoría visible de ambos roles. **Por qué aquí:** la unidad responsable es `ControlField.getPresentationCategory`, compartida por salida; el test no necesita Windows UIA, COM de navegador ni una voz concreta. Usa razón por defecto CARET y sin antecesores; no demuestra todos los motivos de salida o combinaciones de estados. La configuración mínima es suficiente porque las condiciones de otros roles se cortocircuitan.

```diff
@@ -22,6 +23,28 @@
 _PARAGRAPH_OFFSETS = (25, 30)
 
 
+class TestDescriptionListPresentation(unittest.TestCase):
+	def test_termsAndDefinitionsAreMarkersWhenListsAreReported(self) -> None:
+		formatConfig = {"reportLists": True}
+		for role in (controlTypes.Role.TERM, controlTypes.Role.DEFINITION):
+			with self.subTest(role=role):
+				field = textInfos.ControlField(role=role)
+				self.assertEqual(
+					textInfos.ControlField.PRESCAT_MARKER,
+					field.getPresentationCategory([], formatConfig),
+				)
+
+	def test_termsAndDefinitionsAreLayoutWhenListsAreNotReported(self) -> None:
+		formatConfig = {"reportLists": False}
+		for role in (controlTypes.Role.TERM, controlTypes.Role.DEFINITION):
+			with self.subTest(role=role):
+				field = textInfos.ControlField(role=role)
+				self.assertEqual(
+					textInfos.ControlField.PRESCAT_LAYOUT,
+					field.getPresentationCategory([], formatConfig),
+				)
+
+
 class _LineOnlyTextInfo(BasicTextInfo):
 	"""A fake offsets TextInfo whose sentence and paragraph support is not implemented."""
 
```

- [N26](../../tests/unit/test_textInfos.py#L26): agrupa el nuevo contrato de presentación en una clase descubrible por `unittest`.
- [N27](../../tests/unit/test_textInfos.py#L27): declara el caso que debe producir marcadores cuando se informan listas; no devuelve datos.
- [N28](../../tests/unit/test_textInfos.py#L28): habilita explícitamente `reportLists` para no depender de la configuración del usuario.
- [N29](../../tests/unit/test_textInfos.py#L29): prueba por separado término y definición con la misma expectativa.
- [N30](../../tests/unit/test_textInfos.py#L30): etiqueta cada subcaso con su rol para localizar fallos.
- [N31](../../tests/unit/test_textInfos.py#L31): construye un campo real mínimo, sin imponer `READONLY` ni un antecesor lista.
- [N32](../../tests/unit/test_textInfos.py#L32): abre la aserción de igualdad de categoría.
- [N33](../../tests/unit/test_textInfos.py#L33): fija `PRESCAT_MARKER` como contrato esperado, no una palabra de voz.
- [N34](../../tests/unit/test_textInfos.py#L34): consulta la categoría con lista vacía de antecesores y configuración local; usa el motivo por defecto.
- [N35](../../tests/unit/test_textInfos.py#L35): cierra la primera aserción.
- [N36](../../tests/unit/test_textInfos.py#L36): blanco entre los dos métodos de test.
- [N37](../../tests/unit/test_textInfos.py#L37): declara el caso inverso, que debe ocultar la estructura cuando no se informan listas.
- [N38](../../tests/unit/test_textInfos.py#L38): deshabilita explícitamente `reportLists`.
- [N39](../../tests/unit/test_textInfos.py#L39): repite la comprobación para los dos roles, no solo el enum recién creado.
- [N40](../../tests/unit/test_textInfos.py#L40): identifica cada subcaso por rol en los informes de unittest.
- [N41](../../tests/unit/test_textInfos.py#L41): crea de nuevo un campo sin estados, comprobando que la supresión no requiera solo lectura.
- [N42](../../tests/unit/test_textInfos.py#L42): inicia la aserción de la categoría suprimida.
- [N43](../../tests/unit/test_textInfos.py#L43): espera `PRESCAT_LAYOUT`, cuyo valor es `None`; no significa que desaparezca el texto del documento.
- [N44](../../tests/unit/test_textInfos.py#L44): consulta la misma API con la opción desactivada y antecesores vacíos.
- [N45](../../tests/unit/test_textInfos.py#L45): cierra la aserción inversa.
- [N46-N47](../../tests/unit/test_textInfos.py#L46-L47): blancos entre la clase nueva y el proveedor de texto de pruebas existente.

## 13. Changelog para usuarios

<!-- file: user_docs/en/changes.md -->

### Hunk 13.1: anunciar el cambio observable

**Necesidad/origen:** los roles y el significado del número anunciado cambian la experiencia de navegación; debe quedar constancia para usuarios. La entrada se sitúa bajo [2027.1, correcciones, navegadores](../../user_docs/en/changes.md#L1-L22), no en la guía ni en un comentario interno. **Por qué aquí:** es una comunicación de resultado, no código consumidor. No se cambian formatos de frases de voz ni se introduce una opción de configuración nueva.

**Precisión importante:** la frase es amplia. Este diff no implementa conteo MSHTML nuevo; UIA nativo `description` no se normaliza aquí a `DEFINITION`; y los contadores solo suman grupos completos. Por ello no debe tomarse esta entrada como garantía de paridad universal entre backends. Se reproduce literalmente, sin corregirla en una tarea exclusivamente documental.

```diff
diff --git a/user_docs/en/changes.md b/user_docs/en/changes.md
index 283e8f164..1adc31ea7 100644
--- a/user_docs/en/changes.md
+++ b/user_docs/en/changes.md
@@ -17,6 +17,8 @@
 
 #### Web browsers
 
+* Description lists now expose terms and definitions as distinct roles, and their reported item count reflects groups of associated terms and definitions. (#3858)
+
 #### Applications
 
 * Fixed an issue where formulas and notes were not listed in Excel's elements list when it was opened from a sheet with multiple cells selected. (#20806, @CyrilleB79)
```

- [N20](../../user_docs/en/changes.md#L20): comunica separación de roles y conteo de asociaciones y lo vincula a #3858. Es texto inglés del changelog traducible en el proceso habitual, no un literal pasado a `_()` ni prueba de que todos los backends ya hagan lo mismo.
- [N21](../../user_docs/en/changes.md#L21): blanco que separa la entrada nueva del encabezado de aplicaciones siguiente.

## 14. Archivo nuevo completo: tests unitarios Chromium UIA

<!-- file: tests/unit/test_NVDAObjects_UIA_chromium.py -->

### Hunk 14.1: creación íntegra, 199 líneas

**Necesidad/origen:** la prueba de sistema Chrome ordinaria recorre IA2; no basta como regresión de los helpers UIA. Este archivo comprueba sus contratos con dobles de elementos y walker, además de campos reales de `textInfos`. **Por qué aquí:** separa la unidad de traducción específica de Chromium del test común de categorías y del test de navegador. No agrega lógica a los consumidores ni requiere un proveedor UIA real para explorar las combinaciones de conteo.

El hunk único reproduce el archivo entero, incluidas licencia, imports, anotaciones de tipos, datos de casos, blancos y cierres. Los apartados de comentario separan sus responsabilidades, **no omiten líneas del hunk**. No se agrega un bloque `unittest.main`: la infraestructura de descubrimiento de tests es la existente.

**Lo que estos dobles no demuestran:** `_Element.getCurrentPropertyValue` devuelve siempre el rol e ignora el identificador solicitado; no valida la constante UIA ni el protocolo COM. `_Walker` modela hijos y hermanos, no la poda real de `ControlViewWalker`. La marca descriptiva se introduce manualmente en los tests de campos, así que no se comprueba aquí la integración de `_getControlFieldForUIAObject` con `getTextWithFields`. No hay caso de `COMError`, condición exacta de quicknav, `content` sustituido por la base ni navegador UIA real. Los dos casos de rol primario no cubren explícitamente valores no textuales, mayúsculas o toda variante de espacios.

```diff
diff --git a/tests/unit/test_NVDAObjects_UIA_chromium.py b/tests/unit/test_NVDAObjects_UIA_chromium.py
new file mode 100644
--- /dev/null
+++ b/tests/unit/test_NVDAObjects_UIA_chromium.py
@@ -0,0 +1,199 @@
+# A part of NonVisual Desktop Access (NVDA)
+# Copyright (C) 2026 NV Access Limited, Juanjo M
+# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
+# For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt
+
+"""Unit tests for NVDAObjects.UIA.chromium."""
+
+import unittest
+from types import SimpleNamespace
+from unittest.mock import patch
+
+import controlTypes
+import textInfos
+from NVDAObjects.UIA import chromium
+
+
+class _Element:
+	def __init__(self, role: str, children: list["_Element"] | None = None) -> None:
+		self.role = role
+		self.children = children or []
+		for index, child in enumerate(self.children):
+			child.nextSibling = self.children[index + 1] if index + 1 < len(self.children) else None
+		self.nextSibling: _Element | None = None
+
+	def getCurrentPropertyValue(self, _propertyId: int) -> str:
+		return self.role
+
+
+class _Walker:
+	@staticmethod
+	def GetFirstChildElement(element: _Element) -> _Element | None:
+		return element.children[0] if element.children else None
+
+	@staticmethod
+	def GetNextSiblingElement(element: _Element) -> _Element | None:
+		return element.nextSibling
+
+
+def _fieldCommands(*fields: textInfos.ControlField) -> list[textInfos.FieldCommand | str]:
+	return [
+		*(textInfos.FieldCommand("controlStart", field) for field in fields),
+		"content",
+		*(textInfos.FieldCommand("controlEnd", None) for _ in fields),
+	]
+
+
+def _listElement(*roles: str) -> _Element:
+	return _Element("list", [_Element(role) for role in roles])
+
+
+class TestDescriptionListGroupCount(unittest.TestCase):
+	def setUp(self) -> None:
+		self.handlerPatch = patch.object(
+			chromium.UIAHandler,
+			"handler",
+			SimpleNamespace(clientObject=SimpleNamespace(ControlViewWalker=_Walker())),
+		)
+		self.handlerPatch.start()
+		self.addCleanup(self.handlerPatch.stop)
+
+	def test_groupCounts(self) -> None:
+		self.assertEqual("term", chromium._getPrimaryAriaRole("unsupported term"))
+		self.assertEqual("button", chromium._getPrimaryAriaRole("button term"))
+		testCases = (
+			("ordinary list", _listElement("listitem", "listitem"), None),
+			(
+				"ordinary list with group",
+				_Element("list", [_Element("group", [_Element("listitem")])]),
+				None,
+			),
+			(
+				"many-to-many direct groups",
+				_listElement(
+					"listitem",
+					"description",
+					"listitem",
+					"listitem",
+					"definition",
+					"definition",
+				),
+				2,
+			),
+			(
+				"direct div wrappers",
+				_Element(
+					"list",
+					[
+						_Element("group", [_Element("listitem"), _Element("description")]),
+						_Element(
+							"group",
+							[_Element("listitem"), _Element("listitem"), _Element("definition")],
+						),
+					],
+				),
+				2,
+			),
+			(
+				"mixed direct and wrapped groups",
+				_Element("list", [_Element("listitem"), _Element("group", [_Element("definition")])]),
+				1,
+			),
+			(
+				"fallback roles",
+				_listElement("unsupported listitem", "unsupported definition"),
+				1,
+			),
+			(
+				"valid role override",
+				_listElement("button term", "button definition"),
+				None,
+			),
+			(
+				"nested div wrapper",
+				_Element(
+					"list",
+					[_Element("group", [_Element("group", [_Element("term"), _Element("definition")])])],
+				),
+				None,
+			),
+			(
+				"unpaired trailing term",
+				_listElement("listitem", "description", "listitem"),
+				1,
+			),
+			("definition without term", _listElement("definition"), 0),
+		)
+		for description, listElement, expectedCount in testCases:
+			with self.subTest(description=description):
+				self.assertEqual(expectedCount, chromium._getDescriptionListGroupCount(listElement))
+
+	def test_nestedDescriptionListIsIndependent(self) -> None:
+		innerList = _Element("list", [_Element("listitem"), _Element("description")])
+		outerList = _Element(
+			"list",
+			[
+				_Element("listitem"),
+				_Element("description", [innerList]),
+			],
+		)
+
+		self.assertEqual(1, chromium._getDescriptionListGroupCount(outerList))
+		self.assertEqual(1, chromium._getDescriptionListGroupCount(innerList))
+		ordinaryList = _Element("list", [_Element("listitem", [innerList])])
+		self.assertIsNone(chromium._getDescriptionListGroupCount(ordinaryList))
+
+
+class TestNormalizeDescriptionListTerms(unittest.TestCase):
+	def test_ordinaryListItemIsUnchanged(self) -> None:
+		listField = textInfos.ControlField(role=controlTypes.Role.LIST)
+		itemField = textInfos.ControlField(role=controlTypes.Role.LISTITEM, name="Item")
+		fields = _fieldCommands(listField, itemField)
+
+		chromium._normalizeDescriptionListTerms(fields)
+
+		self.assertEqual(controlTypes.Role.LISTITEM, itemField["role"])
+		self.assertEqual("Item", itemField["name"])
+
+	def test_termNameIsRemoved(self) -> None:
+		for initialRole in (controlTypes.Role.LISTITEM, controlTypes.Role.TERM):
+			with self.subTest(initialRole=initialRole):
+				listField = textInfos.ControlField(role=controlTypes.Role.LIST, _isDescriptionList=True)
+				itemField = textInfos.ControlField(role=initialRole, name="Term", alwaysReportName=True)
+				fields = _fieldCommands(listField, itemField)
+
+				chromium._normalizeDescriptionListTerms(fields)
+
+				self.assertEqual(controlTypes.Role.TERM, itemField["role"])
+				self.assertNotIn("name", itemField)
+				self.assertNotIn("alwaysReportName", itemField)
+				self.assertNotIn("_isDescriptionList", listField)
+
+	def test_nestedListsUseTheirOwnSemantics(self) -> None:
+		descriptionListField = textInfos.ControlField(role=controlTypes.Role.LIST, _isDescriptionList=True)
+		definitionField = textInfos.ControlField(role=controlTypes.Role.DEFINITION)
+		ordinaryListField = textInfos.ControlField(role=controlTypes.Role.LIST)
+		itemField = textInfos.ControlField(role=controlTypes.Role.LISTITEM, name="Nested item")
+		ordinaryListFields = _fieldCommands(
+			descriptionListField,
+			definitionField,
+			ordinaryListField,
+			itemField,
+		)
+		chromium._normalizeDescriptionListTerms(ordinaryListFields)
+		self.assertEqual(controlTypes.Role.LISTITEM, itemField["role"])
+		self.assertEqual("Nested item", itemField["name"])
+
+		outerListField = textInfos.ControlField(role=controlTypes.Role.LIST, _isDescriptionList=True)
+		innerListField = textInfos.ControlField(role=controlTypes.Role.LIST, _isDescriptionList=True)
+		innerItemField = textInfos.ControlField(role=controlTypes.Role.LISTITEM, name="Inner term")
+		descriptionListFields = _fieldCommands(
+			outerListField,
+			definitionField,
+			innerListField,
+			innerItemField,
+		)
+		chromium._normalizeDescriptionListTerms(descriptionListFields)
+		self.assertEqual(controlTypes.Role.TERM, innerItemField["role"])
+		self.assertNotIn("_isDescriptionList", outerListField)
+		self.assertNotIn("_isDescriptionList", innerListField)
```

#### Cabecera, imports y dobles de infraestructura

- [N1](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L1): identifica el archivo como parte de NVDA.
- [N2](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L2): consigna copyright 2026 de NV Access Limited y Juanjo M en un archivo nuevo.
- [N3](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L3): declara GPL versión 2 o posterior con las modificaciones de la licencia NVDA; no introduce una licencia particular para el test.
- [N4](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L4): remite al texto completo de licencia y permisos adicionales; forma parte literal de la cabecera nueva.
- [N5](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L5): blanco entre licencia y documentación del módulo.
- [N6](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L6): documenta el módulo de producción cubierto, sin declarar que se prueba toda su funcionalidad.
- [N7](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L7): separa docstring de imports.
- [N8](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L8): importa el marco de casos, subcasos y aserciones.
- [N9](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L9): importa contenedores sencillos de atributos para imitar la ruta del cliente UIA sin implementar un cliente completo.
- [N10](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L10): importa sustitución temporal de atributos para aislar `UIAHandler.handler`.
- [N11](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L11): separa biblioteca estándar de imports de NVDA.
- [N12](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L12): aporta los roles reales usados al construir campos y validar resultados.
- [N13](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L13): aporta `ControlField` y `FieldCommand` reales, no mocks de su estructura.
- [N14](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L14): importa el módulo bajo prueba y accede a sus helpers privados mediante el módulo.
- [N15-N16](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L15-L16): blancos antes de la primera clase de módulo.
- [N17](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L17): declara un doble mínimo de elemento; el prefijo privado evita presentarlo como API de producción.
- [N18](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L18): constructor con rol textual e hijos opcionales; la referencia adelantada `"_Element"` permite tipar hijos de la clase aún en definición, y `None` evita un argumento lista mutable compartido.
- [N19](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L19): almacena el valor que se devolverá como propiedad ARIA.
- [N20](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L20): conserva los hijos proporcionados o crea una lista vacía para un nodo hoja.
- [N21](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L21): enumera hijos para construir sus enlaces de hermano con índice y objeto.
- [N22](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L22): enlaza cada hijo con el siguiente o con `None` al final, reproduciendo la navegación que solicita el helper.
- [N23](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L23): inicializa el hermano del propio elemento a ausencia, con tipo opcional; el padre lo podrá asignar al incorporarlo.
- [N24](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L24): separa constructor y método de propiedad.
- [N25](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L25): imita la firma usada para obtener una propiedad; `_propertyId` deja explícito que el doble no valida ese identificador.
- [N26](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L26): devuelve siempre el rol almacenado, sin COM, caché ni otras propiedades.
- [N27-N28](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L27-L28): blancos entre clases auxiliares.
- [N29](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L29): declara el walker falso que opera sobre el árbol de `_Element`.
- [N30](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L30): hace estática la operación de primer hijo, pues el walker no almacena estado propio.
- [N31](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L31): conserva el nombre de método que invoca la API UIA y tipa el elemento o ausencia devueltos.
- [N32](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L32): devuelve el primer hijo o `None`, permitiendo listas vacías sin error de índice.
- [N33](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L33): blanco entre operaciones del walker.
- [N34](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L34): declara estática también la operación de siguiente hermano.
- [N35](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L35): reproduce el segundo método del walker usado por el algoritmo, con resultado opcional.
- [N36](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L36): lee el enlace previamente preparado por el padre, no recorre descendientes.
- [N37-N38](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L37-L38): blancos antes de los constructores de fixtures.
- [N39](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L39): recibe campos variables y declara un flujo de comandos/cadenas; no devuelve objetos UIA.
- [N40](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L40): abre la lista que materializa el flujo completo para normalizar.
- [N41](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L41): expande un generador de aperturas para todos los campos, creando anidamiento en el orden de argumentos.
- [N42](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L42): inserta un fragmento textual para que el normalizador atraviese también contenido no `FieldCommand`; no se comprueba su valor mediante una aserción posterior.
- [N43](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L43): genera tantos cierres como aperturas; no llevan campo y la pila los interpreta en orden LIFO. `_` expresa que solo importa su cantidad.
- [N44](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L44): cierra la lista de flujo devuelta.
- [N45-N46](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L45-L46): blancos entre helpers de fixtures.
- [N47](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L47): recibe una secuencia de roles para simplificar listas de hijos directos; devuelve el doble de elemento contenedor.
- [N48](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L48): crea raíz `list` y un elemento hoja por token, preservando su orden.
- [N49-N50](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L49-L50): blancos antes de la clase de pruebas de conteo.

#### Conteos y contrato de ausencia

- [N51](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L51): agrupa las pruebas del conteo específico UIA en una clase `unittest.TestCase`.
- [N52](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L52): prepara el aislamiento antes de cada método de esa clase.
- [N53](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L53): guarda un patcher para sustituir un atributo de módulo y restaurarlo después.
- [N54](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L54): selecciona el módulo `UIAHandler` visto por el código bajo prueba; no sustituye el algoritmo del conteo.
- [N55](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L55): identifica `handler` como atributo sustituido.
- [N56](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L56): reproduce exactamente la ruta `handler.clientObject.ControlViewWalker` con namespaces y walker falso.
- [N57](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L57): cierra la construcción del patcher.
- [N58](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L58): activa la sustitución antes de llamar a los helpers.
- [N59](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L59): registra la restauración con `addCleanup`, también ante fallos de aserción; evita contaminar otros casos con el handler falso.
- [N60](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L60): blanco entre preparación y prueba parametrizada.
- [N61](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L61): declara el método que comprueba roles primarios y la matriz de conteos.
- [N62](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L62): exige ignorar un primer token desconocido y seleccionar `term` como fallback reconocido.
- [N63](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L63): exige conservar `button` cuando precede a `term`; impide interpretar cualquier aparición de `term` como rol principal.
- [N64](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L64): inicia una tabla de tuplas descripción/elemento/conteo esperado.
- [N65](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L65): lista ordinaria con dos elementos espera `None`, no cero ni dos; conserva el conteo heredado.
- [N66](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L66): abre el segundo caso, separado para legibilidad de la fixture anidada.
- [N67](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L67): da nombre al caso ordinario con envoltura para identificarlo en un fallo.
- [N68](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L68): crea lista/grupo/listitem sin definición; un `group` por sí solo no prueba semántica descriptiva.
- [N69](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L69): espera ausencia de corrección pese a la envoltura.
- [N70](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L70): cierra el segundo caso.
- [N71](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L71): abre el caso de grupos directos con cardinalidades distintas.
- [N72](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L72): identifica la relación muchos-a-muchos que debe evitar contar por nodo.
- [N73](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L73): inicia una lista de hijos directos por roles, sin envolturas.
- [N74](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L74): primer término nativo supuesto, que deja términos pendientes.
- [N75](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L75): primera definición `description`, que completa el primer grupo.
- [N76](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L76): primer término del segundo grupo.
- [N77](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L77): segundo término consecutivo del mismo grupo; no debe incrementar solo.
- [N78](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L78): primera definición explícita del segundo grupo; además cubre el token alternativo `definition`.
- [N79](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L79): segunda definición consecutiva que no debe volver a sumar.
- [N80](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L80): cierra la construcción de la lista directa.
- [N81](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L81): exige dos grupos, no tres términos ni seis hijos.
- [N82](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L82): cierra el caso muchos-a-muchos.
- [N83](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L83): abre el caso de envolturas directas hermanas.
- [N84](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L84): etiqueta ese caso como envolturas `div`; el doble representa su supuesta exposición UIA como `group`, no HTML real.
- [N85](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L85): comienza la construcción explícita del contenedor con árbol de hijos.
- [N86](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L86): asigna rol lista a la raíz.
- [N87](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L87): abre la colección de envolturas hijas.
- [N88](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L88): primera envoltura con término y definición; aporta un grupo completo.
- [N89](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L89): abre la segunda envoltura, hermana de la primera.
- [N90](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L90): asigna `group` al nodo de envoltura.
- [N91](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L91): coloca dos términos y una definición en esa envoltura, que deben sumar un solo grupo.
- [N92-N94](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L92-L94): cierres de la segunda envoltura, colección de hijos y raíz.
- [N95](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L95): exige dos grupos al atravesar ambas envolturas directas.
- [N96](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L96): cierra el caso de envolturas hermanas.
- [N97](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L97): abre el caso que mezcla profundidad directa y envuelta.
- [N98](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L98): identifica el caso mixto en el informe de subtests.
- [N99](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L99): sitúa un término directo antes de una envoltura que solo contiene la definición; exige compartir estado al entrar en ella.
- [N100](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L100): espera un grupo; reiniciar términos pendientes en la recursión haría fallar este contrato.
- [N101](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L101): cierra el caso mixto.
- [N102](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L102): abre el caso de fallbacks de roles.
- [N103](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L103): da nombre a la expectativa de ignorar tokens desconocidos.
- [N104](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L104): crea término y definición precedidos de `unsupported`, probando selección del primer rol reconocido dentro del conteo.
- [N105](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L105): espera un grupo completo tras resolver ambos fallbacks.
- [N106](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L106): cierra el caso de fallbacks.
- [N107](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L107): abre el caso de override reconocido.
- [N108](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L108): identifica que un rol válido anterior debe prevalecer.
- [N109](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L109): antepone `button` tanto a `term` como a `definition`, de modo que ninguno debe actuar como parte de grupo.
- [N110](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L110): exige `None` por falta de evidencia descriptiva reconocida, no cero.
- [N111](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L111): cierra el caso de override.
- [N112](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L112): abre el caso de profundidad no permitida.
- [N113](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L113): etiqueta la envoltura anidada que debe quedar fuera del descenso.
- [N114](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L114): inicia la raíz explícita de ese árbol.
- [N115](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L115): asigna rol lista a la raíz del caso.
- [N116](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L116): sitúa `term` y `definition` dentro de dos niveles de `group`; un recorrido ilimitado los encontraría indebidamente.
- [N117](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L117): cierra la construcción del árbol.
- [N118](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L118): espera `None`, pues el nivel permitido no alcanza ninguna definición.
- [N119](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L119): cierra el caso de profundidad limitada.
- [N120](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L120): abre el caso con término final incompleto.
- [N121](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L121): describe explícitamente el término sin definición posterior.
- [N122](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L122): construye un grupo completo seguido de otro término pendiente.
- [N123](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L123): espera un solo grupo; no implementa el conteo de grupos incompletos del algoritmo WHATWG completo.
- [N124](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L124): cierra el caso de término final.
- [N125](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L125): definición huérfana espera cero: hay evidencia descriptiva, pero ninguna asociación completa. Fija la distinción entre cero y `None`.
- [N126](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L126): cierra la tabla de diez casos.
- [N127](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L127): desempaqueta y recorre cada descripción, árbol y resultado esperado.
- [N128](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L128): identifica fallos por la descripción sin crear diez métodos repetitivos.
- [N129](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L129): compara el resultado real del helper no sustituido con el contrato de cada fixture.
- [N130](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L130): blanco antes del caso de independencia de listas.
- [N131](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L131): declara la regresión que impide que una lista interior infle o convierta a la exterior.
- [N132](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L132): crea una lista descriptiva interior con un grupo propio.
- [N133](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L133): inicia la lista exterior que contendrá la interior dentro de una definición.
- [N134](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L134): asigna el rol de lista a la raíz exterior.
- [N135](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L135): abre sus hijos directos.
- [N136](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L136): crea el término propio de la lista exterior.
- [N137](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L137): crea su definición con la lista interior como descendiente; el contador exterior no debe bajar a ese contenido.
- [N138-N139](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L138-L139): cierres de hijos y construcción de la lista exterior.
- [N140](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L140): separa preparación y aserciones.
- [N141](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L141): exige un grupo exterior, no la suma exterior más interior.
- [N142](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L142): consulta separadamente la interior y exige su grupo propio; cada llamada tiene estado nuevo.
- [N143](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L143): reutiliza la lista interior dentro de un elemento de lista ordinaria, sin definición exterior.
- [N144](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L144): exige no corregir esa lista ordinaria por una definición que solo aparece en sus descendientes profundos.
- [N145-N146](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L145-L146): blancos entre clases de pruebas.

#### Campos, nombres y listas anidadas

- [N147](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L147): agrupa las pruebas del normalizador de flujo, sin usar el handler falso de la otra clase.
- [N148](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L148): declara el caso de no regresión para un elemento ordinario.
- [N149](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L149): crea una lista sin marca descriptiva.
- [N150](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L150): crea un `LISTITEM` con nombre para comprobar que no se convierte ni pierde ese dato.
- [N151](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L151): anida el elemento dentro de la lista mediante comandos reales.
- [N152](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L152): blanco entre preparación y operación bajo prueba.
- [N153](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L153): aplica el normalizador real al flujo preparado.
- [N154](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L154): blanco antes de comprobar el resultado.
- [N155](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L155): exige conservar el rol de elemento ordinario de lista.
- [N156](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L156): exige conservar su nombre, evitando una eliminación global de nombres de `LISTITEM`.
- [N157](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L157): separa métodos de prueba.
- [N158](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L158): declara el caso de conversión y supresión de nombre de términos.
- [N159](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L159): cubre tanto entrada nativa supuesta `LISTITEM` como un `TERM` ya reconocido.
- [N160](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L160): identifica el rol inicial en el subtest que falle.
- [N161](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L161): marca manualmente la lista como descriptiva; no prueba cómo se obtuvo esa marca de un elemento UIA real.
- [N162](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L162): aporta nombre y orden de anunciarlo siempre, reproduciendo los atributos que el helper debe retirar.
- [N163](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L163): construye el flujo de lista y elemento para que la pila conozca el antecesor.
- [N164](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L164): blanco antes de la llamada.
- [N165](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L165): normaliza el flujo mediante el helper real.
- [N166](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L166): blanco antes de las cuatro comprobaciones.
- [N167](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L167): exige `TERM` como rol final en ambos subcasos.
- [N168](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L168): exige desaparición de `name`, no únicamente una cadena vacía.
- [N169](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L169): exige retirar la orden `alwaysReportName` que podría causar anuncio redundante.
- [N170](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L170): exige consumir la marca privada de lista antes de devolver campos a consumidores.
- [N171](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L171): blanco antes de la prueba de contexto anidado.
- [N172](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L172): declara dos escenarios para la política de lista antecesora más próxima.
- [N173](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L173): prepara una lista descriptiva exterior marcada.
- [N174](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L174): crea una definición intermedia; demuestra que buscar contexto no equivale a mirar solo el padre inmediato.
- [N175](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L175): crea una lista ordinaria interior que debe cortar la herencia descriptiva exterior.
- [N176](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L176): crea el elemento ordinario interior con un nombre distintivo.
- [N177](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L177): abre la construcción del primer flujo anidado.
- [N178](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L178): coloca la lista descriptiva como ámbito exterior.
- [N179](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L179): anida la definición dentro de ella.
- [N180](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L180): anida la lista ordinaria dentro de la definición, más próxima al elemento final.
- [N181](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L181): añade ese elemento como ámbito más interior del flujo.
- [N182](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L182): cierra la construcción del primer flujo.
- [N183](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L183): aplica la normalización al escenario de lista ordinaria anidada.
- [N184](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L184): exige que el rol siga siendo `LISTITEM` pese a existir una lista descriptiva más lejana.
- [N185](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L185): exige que conserve el nombre; valida que tampoco se aplicó la limpieza de términos por herencia incorrecta.
- [N186](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L186): separa los dos escenarios dentro del mismo método.
- [N187](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L187): crea una lista exterior descriptiva nueva, porque la marca anterior ya fue consumida.
- [N188](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L188): crea ahora una lista interior también descriptiva, con marca propia.
- [N189](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L189): prepara el elemento interior que sí debe convertirse en término.
- [N190](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L190): inicia el segundo flujo anidado.
- [N191](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L191): coloca la nueva lista exterior en la pila.
- [N192](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L192): reutiliza el campo de definición como contexto intermedio; ese campo no depende de una marca descriptiva propia.
- [N193](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L193): introduce la lista interior marcada como la lista más próxima al elemento.
- [N194](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L194): coloca el elemento interior tras sus antecesores.
- [N195](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L195): cierra la construcción del segundo flujo.
- [N196](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L196): normaliza el escenario de listas descriptivas anidadas.
- [N197](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L197): exige conversión a `TERM` por la semántica propia de la lista interior; no comprueba aquí de nuevo su nombre.
- [N198](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L198): exige retirar la marca privada de la lista exterior.
- [N199](../../tests/unit/test_NVDAObjects_UIA_chromium.py#L199): exige retirar también la de la interior, cerrando la cobertura literal del archivo nuevo.

## 15. Balance de cobertura y límites de la solución documentada

| Aspecto | Evidencia incluida | Lo que no permite afirmar |
| --- | --- | --- |
| Roles comunes | Enum estable, mapa ARIA, etiqueta localizable y braille | Traducciones ya completadas o compatibilidad de todo complemento con el nuevo rol |
| IA2 | Productor C++, normalizador Python, filtros y fixture Chrome | Prueba real Firefox en este diff o equivalencia absoluta entre criterios de conteo, rol y quicknav |
| MSHTML | Mapa `DT`/`DD` y filtro `LI`/`DT` | Conteo semántico nuevo, supresión de nombres nueva o prueba real MSHTML |
| UIA | Helpers, dos puntos de integración de campos, filtro y dobles unitarios | Ejecución de navegador UIA, fallo COM probado, poda de `content` validada o búsqueda de todos los fallbacks |
| Grupos | Muchos-a-muchos, envolturas directas, estado compartido, anidamiento independiente | Recuperación WHATWG completa, validación HTML o descenso ilimitado |
| Presentación | Categorías marcador/disposición y expectativas de voz Chrome | Captura braille real, todas las razones de salida o todas las combinaciones de ajustes |
| Registro y comunicación | Keyword Python, caso Robot, etiqueta `chrome_list`, changelog | Ejecución efectiva de CI o resultados de pruebas durante esta tarea |

La distribución responde a responsabilidades distintas: el productor detecta asociaciones donde existe estructura del proveedor; el normalizador entrega roles y conteo comunes; la navegación consulta atributos buscables; la política de campos y etiquetas sirve a voz y braille. No hay que implementar agrupación HTML en cada consumidor. Los tests son verificadores de esos contratos, no la fuente de los datos de producción.

Los matices detectados se documentan sin modificar implementación: versión normativa de la prohibición de nombres; amplitud del changelog; diferencias IA2/UIA/MSHTML; conteo exclusivo de grupos completos; condiciones distintas entre quicknav y normalización; primera captura Chrome sobrescrita; y ausencia de pruebas de integración UIA. Ninguno se convierte aquí en una afirmación de fallo observado durante ejecución.

## 16. Método de verificación documental

La comprobación documental es de solo lectura: no importa módulos NVDA, no ejecuta tests, no compila ni abre navegadores. Trabaja con Git, texto UTF-8 y números de línea. El procedimiento reproducible es:

1. Leer los comentarios HTML cuyo contenido empieza por `file:` y extraer, en cada sección de archivo, todos los bloques cercados `diff` en orden. Concatenarlos conservando el salto final de cada bloque, sin añadir una línea vacía entre bloques.
2. Para los trece archivos seguidos, obtener `git diff HEAD --` con su ruta explícita y comparar el texto completo —cabeceras, índices, contexto y hunks— con los bloques concatenados. La lectura normaliza solo terminadores CRLF/LF; no recorta tabulaciones, espacios ni blancos de los hunks.
3. Para el archivo nuevo, construir en memoria la cabecera de creación mostrada y prefijar con `+` cada una de sus 199 líneas reales. Comparar literalmente con el bloque del documento. No depender de `git diff` para un archivo aún no seguido.
4. Analizar las cabeceras `@@`: iniciar contadores antiguos/nuevos; el contexto incrementa ambos, `-` solo el antiguo y `+` solo el nuevo. Construir el conjunto esperado `(archivo, A/N, número)`, **incluyendo blancos**. Contrastar longitudes declaradas de cada hunk con sus líneas efectivas.
5. Extraer las viñetas de anotación `[A…]` y `[N…]`, expandir sus rangos y exigir coincidencia exacta con el conjunto anterior, sin omisiones, extras ni duplicados. Además, comprobar que la ruta y el ancla del enlace corresponden al archivo y número anotados. Un comentario A usa deliberadamente el ancla orientativa del archivo actual, como se advierte al inicio.
6. Revisar cada rango agrupado: solo blancos o cierres sintácticos sin instrucciones/datos. Las explicaciones de esos cierres se encuentran junto al hunk; ninguna línea de lógica, import, atribución, dato o aserción se considera cubierta por un comentario global del bloque.
7. Resolver todos los enlaces relativos locales del documento respecto de esta carpeta y verificar existencia de archivos y límites de las líneas citadas. Esto comprueba integridad de enlaces, no la exactitud semántica del párrafo enlazado, revisada mediante lectura de fuentes.
8. Contrastar los totales con el inventario: 14 archivos, 500 líneas nuevas y 19 antiguas. Registrar por separado resultados documentales y límites de pruebas de ejecución; no usar la fidelidad del diff como prueba de corrección funcional.

Las cabeceras `index` y los números se refieren a esta instantánea: si cambia cualquiera de los catorce archivos, debe regenerarse y verificarse la parte correspondiente, no actualizar solo la tabla de totales.

### Resultado de la comprobación

La comparación automática de los 35 hunks con sus fuentes no encontró diferencias en cabeceras, índices, contexto, tabulaciones ni líneas añadidas/eliminadas. Las 519 posiciones de cambio (500 N y 19 A), incluidos los blancos, tienen cobertura exacta mediante anotaciones individuales o rangos exclusivos de blancos/cierres: sin omisiones, extras ni duplicados. El hunk de creación coincide con las 199 líneas del archivo UIA nuevo. Los enlaces locales comprobados existen y sus números de línea están dentro de los archivos correspondientes.

En la revisión documental se corrigieron dos detalles del propio documento: el número de casos tabulados UIA es diez, y el ejemplo textual de un marcador de archivo se reformuló para no confundirse con un decimoquinto archivo al extraer secciones. Un intento de ajuste automático de estilo alteró accidentalmente partes del informe; la comparación lo detectó y se restauraron los bloques, las explicaciones y los enlaces afectados desde la copia anterior. Se mantiene una configuración de estilo local explícita para las viñetas y la negrita, sin reformatear los diffs. No se modificó implementación ni se ejecutaron pruebas. La cobertura del 100 % aquí acreditada es **cobertura documental del diff seleccionado**, no cobertura de ramas, corrección funcional ni resultado de tests.
