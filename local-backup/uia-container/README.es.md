# Preparación de la incidencia: final de contenedores con Chromium UIA

## Estado: falta la comprobación real con Windows desbloqueado

**No enviar todavía el formulario ni presentar el candidato como un arreglo verificado en navegador.**
La copia oficial ya está compilada y las pruebas unitarias están verificadas, pero Windows estaba bloqueado y no se ha intentado eludir ese bloqueo.
El usuario no estaba disponible para desbloquearlo.

Se ha avanzado todo lo que podía comprobarse sin reemplazar el lector ni enviar teclas a la sesión bloqueada:

* El respaldo previo de la funcionalidad y las notas ya está en el fork.
* Hay un candidato independiente sobre el commit oficial `c22a509337c0b94ac5459ab2a749eeeb9cb06116`, en `fix/chromium-uia-container-end`.
Está publicado y verificado en [el fork, commit ae1594bce](https://github.com/kastwey/nvda/commit/ae1594bced4d2ce60dcaa7d1fd975d9f019bb2b8).
* Sus 16 pruebas específicas pasan.
La batería completa ejecutó 1.481 pruebas: cinco omitidas y ninguna fallida.
* Las mismas pruebas específicas, cargando el módulo oficial sin el arreglo en un proceso unitario separado, producen ocho fallos de aserción esperados y ningún error del arnés.
Esto no es una prueba completa de NVDA con Chrome.
* Pasan Ruff, formato, Pyright, ty, comprobación de traducciones y lint del changelog.
* La página adjunta está comprobada en el navegador integrado, en claro/oscuro y a 360 px sin desbordamiento horizontal.
Esto valida su presentación y estructura, no el fallo de UIA con NVDA.

## Archivos para la incidencia

* [uia-container-reproduction.zip](uia-container-reproduction.zip): paquete para adjuntar, con hashes verificados y sin registros privados completos.
* [bug-report.md](bug-report.md): título y contenido para **todos los campos del formulario**, incluidos los desplegables.
Está en inglés y señala expresamente lo pendiente; no inventa pruebas, reinicios ni versiones afectadas.
* [container-navigation.html](container-navigation.html): página autónoma con listas ordinarias y de descripción.
Cada ejemplo tiene su encabezado y un botón después de la lista exterior.
No necesita servidor, Internet, extensiones ni JavaScript.
* [technical-notes.md](technical-notes.md): investigación técnica, procedencia de la copia oficial y límites de la validación.
* [earlier-feature-run-excerpt.log](earlier-feature-run-excerpt.log): extracto acotado del fallo real anterior, con voz y braille.
Está identificado como extracto de la rama de funcionalidad, no como registro de la copia oficial.
* [attachment-readme.md](attachment-readme.md): instrucciones y advertencia de estado que acompañan al paquete para adjuntar.

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
6. Adjuntar el ZIP y el registro fresco de NVDA en el campo de archivos.
GitHub admite ZIP; no es necesario que admita HTML directamente.
Esperar a que finalice la carga y comprobar que GitHub ha insertado el enlace real al adjunto.
7. Revisar la vista previa y que ningún campo obligatorio quede vacío.
8. Enviar personalmente el formulario una vez completada la validación pendiente.
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

## Pendiente antes de enviarlo

* [ ] Desbloquear Windows y ejecutar la misma página con la copia oficial sin el candidato, registrando voz, braille, backend UIA y versión.
* [ ] Ejecutar la página con el candidato y repetir con IA2.
* [ ] Ejecutar la batería `chrome_list` del candidato.
* [ ] Comprobar en el proveedor real una línea vacía posterior, contenido adyacente, fin de documento y contenedores anidados.
* [ ] Añadir un registro fresco de NVDA de la página adjunta, revisado para eliminar datos personales no necesarios.
* [ ] Actualizar versión afectada, salida literal y tabla de resultados del borrador con las mediciones reales.
* [ ] Actualizar la búsqueda de duplicados si ha pasado tiempo.
* [ ] Confirmar los pasos de diagnóstico personales; no marcar reinicio ni reparación si no se han hecho.
* [ ] Tras abrir la incidencia, añadir su número real al changelog del candidato y esperar la discusión/triage correspondiente.

No se puede garantizar que una incidencia sea aceptada.
Sí se ha seguido la plantilla real y se han dejado explícitos los datos que todavía no sería correcto afirmar.
El borrador anuncia que presentarás una PR después de confirmar la reproducción y discutir la incidencia.

## Continuación técnica preparada

[runContainerTests.py](runContainerTests.py) abre la página adjunta con el checkout indicado y guarda la salida de IA2/UIA.
[desktopState.py](desktopState.py) consulta el estado de bloqueo sin interactuar con la pantalla segura; el lanzador se niega a iniciar pruebas si no está disponible la sesión.
El parámetro `--check-only` solo informa del bloqueo; `--official-suite` selecciona las pruebas `chrome_list` del checkout.
[packageReproduction.py](packageReproduction.py) genera el ZIP solo con la página, notas, instrucciones y extracto permitido, y verifica los hashes de sus miembros.

El checkout aislado ha quedado de nuevo en el commit oficial `c22a509337c0b94ac5459ab2a749eeeb9cb06116`, sin el candidato, para que la primera prueba real use la versión sin tocar.
La rama candidata está conservada localmente y en el fork; no se han modificado las dependencias ni los cambios locales de la rama de listas de descripción.

Cuando pueda iniciarse la prueba, habrá silencio temporal porque el sintetizador espía captura la voz sin reproducir audio.
El lanzador restaura el NVDA instalado en un bloque `finally` y solo cierra el Chrome del perfil temporal exacto.
Se debe verificar después que el NVDA instalado sigue activo y que no queda el puerto del espía ni el navegador de pruebas.
