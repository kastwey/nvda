# Preparación de la incidencia: final de contenedores con Chromium UIA

## Estado: reproducción oficial y corrección verificadas

**Ya puedes revisar el borrador y abrir personalmente la incidencia mediante el formulario oficial.**
La comparación real se ha completado con Windows desbloqueado, NVDA y Chrome reales y la página que se adjunta.
No se ha abierto ninguna incidencia ni PR automáticamente.

Resultados:

* El respaldo previo de la funcionalidad y las notas ya está en el fork.
* Hay un candidato independiente sobre el commit oficial `c22a509337c0b94ac5459ab2a749eeeb9cb06116`, en `fix/chromium-uia-container-end`.
Está publicado y verificado en [el fork, commit ae1594bce](https://github.com/kastwey/nvda/commit/ae1594bced4d2ce60dcaa7d1fd975d9f019bb2b8).
* Sus 16 pruebas específicas pasan.
La batería completa ejecutó 1.481 pruebas: cinco omitidas y ninguna fallida.
* Las mismas pruebas específicas, cargando el módulo oficial sin el arreglo en un proceso unitario separado, producen ocho fallos de aserción esperados y ningún error del arnés.
Esto no es una prueba completa de NVDA con Chrome.
* La prueba completa en navegador ahora también está hecha: la copia oficial pasa los ocho recorridos con IA2 y falla los ocho con UIA.
Con el candidato, pasan los ocho recorridos con cada API, en voz y braille al llegar al botón posterior.
* Pasan las seis pruebas `chrome_list` del repositorio, incluidas las dos nuevas.
* Pasan Ruff, formato, Pyright, ty, comprobación de traducciones y lint del changelog.
* La página adjunta está comprobada en el navegador integrado, en claro/oscuro y a 360 px sin desbordamiento horizontal.
Esto valida su presentación y estructura, no el fallo de UIA con NVDA.

## Archivos para la incidencia

* [uia-container-reproduction.zip](uia-container-reproduction.zip): paquete para adjuntar, con hashes verificados y sin registros privados completos.
* [bug-report.md](bug-report.md): título y contenido para **todos los campos del formulario**, incluidos los desplegables.
Está en inglés y contiene los resultados reales; no inventa reinicios ni versiones afectadas.
* [container-navigation.html](container-navigation.html): página autónoma con listas ordinarias y de descripción.
Cada ejemplo tiene su encabezado y un botón después de la lista exterior.
No necesita servidor, Internet, extensiones ni JavaScript.
* [technical-notes.md](technical-notes.md): investigación técnica, procedencia de la copia oficial y límites de la validación.
* [official-reproduction.log](official-reproduction.log) y [candidate-reproduction.log](candidate-reproduction.log): extractos de registros frescos de la página adjunta, con versión, API, teclas y salidas.
Se conservan las entradas originales relevantes; se omite contenido personal de otras ventanas y de configuración.
* [browser-observations.json](browser-observations.json): los 32 recorridos medidos y los hashes de los registros originales.
* [earlier-feature-run-excerpt.log](earlier-feature-run-excerpt.log): extracto acotado del fallo real anterior, con voz y braille.
Está identificado como extracto de la rama de funcionalidad, no como registro de la copia oficial.
* [attachment-readme.md](attachment-readme.md): instrucciones y resultados que acompañan al paquete para adjuntar.

La copia oficial presenta además una excepción distinta al mostrar el número de elementos de una lista en braille.
Se ha documentado sin ocultarla ni mezclarla con el arreglo de la coma: el candidato no corrige esa excepción al entrar en las listas.
Sí se comprueba la salida de voz y braille correcta en el botón posterior.

La página utiliza texto oscuro sobre blanco en modo claro y texto blanco sobre fondo muy oscuro en modo oscuro.
Tiene una columna, títulos distinguibles y listas anidadas con sangrías; los botones están inmediatamente después de cada contenedor.
En pantalla estrecha el texto se adapta sin desplazamiento horizontal.

## Cómo usar el formulario correcto

1. Abrir [el selector oficial de incidencias](https://github.com/nvaccess/nvda/issues/new/choose) y elegir **Bug report**.
También se puede usar [el enlace al formulario verificado](https://github.com/nvaccess/nvda/issues/new?template=01-bug_report.yaml).
La plantilla real empieza por **01**, aunque una página de ayuda antigua enlaza a una variante sin ese cero.
2. No usar una incidencia en blanco ni confiar en que pegar un Markdown completo asignará el tipo y las etiquetas.
El formulario declara el tipo **Bug** y la etiqueta **bug**; el cuerpo Markdown no los establece por sí mismo.
3. Copiar el título propuesto al título de GitHub.
4. Copiar el contenido de cada apartado al campo con el mismo nombre.
No pegar las instrucciones de este documento ni el borrador entero dentro de “Brief summary”.
5. Seleccionar los desplegables exactamente como se indican abajo, salvo que se hayan realizado y verificado nuevos pasos de diagnóstico.
6. Adjuntar el ZIP en el campo de archivos; ya contiene los extractos de registros frescos, la página y las observaciones.
GitHub admite ZIP; no es necesario que admita HTML directamente.
Esperar a que finalice la carga y comprobar que GitHub ha insertado el enlace real al adjunto.
No sustituir ese enlace por una ruta local ni borrarlo al pegar el texto descriptivo.
7. Revisar la vista previa y que ningún campo obligatorio quede vacío.
8. Enviar personalmente el formulario tras revisar los datos y las respuestas de diagnóstico.
No se ha abierto ninguna incidencia ni PR automáticamente.

### Respuestas actuales de los desplegables

| Campo | Selección honesta a día de hoy |
| --- | --- |
| NVDA type | source copy |
| Reinicio del equipo | I have not restarted my computer |
| Reinicio de NVDA con complementos deshabilitados | I have not restarted NVDA with add-ons disabled |
| Herramienta de reparación de accesibilidad | I have not run the System Accessibility Repair Tool |

El perfil de pruebas no tenía complementos de usuario instalados, pero sí instrumentación scratchpad del repositorio.
Por eso no se convierte ese hecho en una afirmación de haber realizado un reinicio con complementos deshabilitados.

## Comprobaciones y siguiente paso

* [x] Ejecutar la página con la copia oficial sin el candidato y confirmar el fallo UIA y el control IA2.
* [x] Ejecutar la misma página con el candidato: ambas APIs pasan.
* [x] Ejecutar la batería `chrome_list` del candidato: seis pruebas pasan.
* [x] Añadir extractos de registros frescos, sin contenido personal ajeno a la prueba.
* [x] Actualizar versión afectada, salida literal y tabla de resultados con las mediciones reales.
* [x] Incluir los 14 campos reales y las opciones exactas del formulario.
* [ ] Revisar el borrador y adjuntar el ZIP al formulario; actualizar la búsqueda de duplicados si ha pasado tiempo.
* [ ] Confirmar los pasos de diagnóstico personales; no marcar reinicio ni reparación si no se han hecho.
* [ ] Tras abrir la incidencia, añadir su número real al changelog del candidato y esperar la discusión/triage correspondiente.

No se puede garantizar que una incidencia sea aceptada.
Sí se ha seguido la plantilla real, se aporta reproducción oficial verificada y se distingue lo probado de lo no probado.
Las líneas vacías independientes, EOF y otros casos límite tienen cobertura unitaria, pero no una matriz propia de pruebas con el proveedor real.
El borrador anuncia que presentarás una PR después de discutir/triagear la incidencia.

## Continuación técnica preparada

[runContainerTests.py](runContainerTests.py) abre la página adjunta con el checkout indicado y guarda la salida de IA2/UIA.
[desktopState.py](desktopState.py) consulta el estado de bloqueo sin interactuar con la pantalla segura; el lanzador se niega a iniciar pruebas si no está disponible la sesión.
El parámetro `--check-only` solo informa del bloqueo; `--official-suite` selecciona las pruebas `chrome_list` del checkout.
[chromeWindow.py](chromeWindow.py) comprueba el proceso de Chrome y el foco antes de enviar gestos; sus siete regresiones pasan.
[collectEvidence.py](collectEvidence.py) verifica los resultados y genera extractos acotados de registros originales.
[packageReproduction.py](packageReproduction.py) genera el ZIP solo con los materiales permitidos y verifica los hashes de sus miembros.

El checkout aislado ha quedado en la rama candidata, commit `ae1594bced4d2ce60dcaa7d1fd975d9f019bb2b8`, después de repetir el control oficial con el mismo arnés final.
La rama candidata está conservada localmente y en el fork; no se han modificado las dependencias ni los cambios locales de la rama de listas de descripción.

Las pruebas ya han terminado y el NVDA instalado se ha restaurado y comprobado.
La restauración usa el lanzador de Windows compatible con UIAccess y espera a la ventana de NVDA antes de comprobar que está activo.
El Chrome de pruebas se cierra por su perfil temporal exacto; no se cierran las otras aplicaciones.
