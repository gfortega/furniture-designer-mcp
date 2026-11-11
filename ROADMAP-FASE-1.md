# Fase 1: diseño y preparación de cortes

Actualizado: 11 de noviembre de 2026. Estado: **cerrada como fase de prueba
del software**, por decisión del usuario. La prueba real del taller, la revisión
constructiva y la propuesta al proyecto original pasan a la fase 2; los diseños
siguen siendo borradores hasta su revisión para fabricación.

## Situación actual

Se realizó una prueba en vivo con el usuario: el escritorio se actualizó a
180 × 200 cm y se generaron el modelo, el Excel y el diagrama. La
configuración genérica utiliza provisionalmente tablero
2600 × 1830 × 18 mm, sierra de 3,2 mm, margen de 5 mm por borde y canto de
1 mm en los bordes seleccionados; sin restricción de veta. Son supuestos, no
condiciones confirmadas de un proveedor. El taller coloca el tapacanto y se
debe descontar su espesor antes de pedir el corte.

Se ejecutaron pruebas automatizadas de geometría, secuencia, exportación y MCP
entre procesos, y se prepararon dos versiones del escritorio para la prueba en
`../evaluacion-furniture-designer/prueba-en-vivo/`. Las cifras del proveedor no
bloquean la prueba de software: se confirmarán en la etapa de taller.

## 1. Instalación y conexión

- [x] Instalar el fork en un entorno `.venv` persistente dentro de este proyecto.
- [x] Registrar `furniture-designer` como servidor MCP de Codex en WSL.
- [x] Probar el ejecutable instalado con un cliente MCP en otro proceso: ocho
  pruebas aprobadas, incluido el despiece provisional del escritorio.
- [x] El usuario confirmó que las herramientas responden desde otra sesión de
  Codex que cargó la configuración nueva. El aislamiento de este entorno
  bloqueó anteriormente una prueba entre procesos; fuera de él funcionó.
- [x] Documentar la instalación y verificarla en un segundo entorno aislado en
  esta misma máquina. La instalación en otra máquina aún no se ha comprobado.

## 2. Diseño y edición

- [x] Crear una plantilla MCP para un escritorio en L provisional y regenerar
  la geometría y el despiece al cambiar sus medidas. Se verificaron dimensiones,
  ausencia de solapamientos entre cajas y consistencia de las orientaciones del
  informe y de FreeCAD, y se generó un informe con dos iteraciones.
- [x] El usuario revisó la visualización 3D y confirmó que es adecuada para la
  prueba. La interfaz existente visualiza el modelo; cambiar medidas se hace
  regenerándolo mediante MCP, no arrastrando piezas.
- [x] Los soportes son suficientes para visualizar el boceto de prueba. La
  validación constructiva corresponde a la etapa 6, antes de fabricar.

## 3. Entrega al proveedor

- [x] Prototipo: perfiles de placa y sierra, despiece CSV/XLSX y agrupación que
  considera material, veta y tapacantos.
- [x] El perfil admite un margen uniforme de escuadrado por cada borde del
  tablero. Si no está definido, el cálculo usa cero con una advertencia.
- [x] Hay un perfil y una plantilla genéricos provisionales; se pueden guardar,
  listar y seleccionar perfiles y plantillas adicionales mediante MCP.
- [x] El paquete preliminar incluye Excel con despiece y resumen de placas, y un
  diagrama SVG calculado para el mismo conjunto de piezas y el mismo perfil.
- [x] El paquete permite descontar el tapacanto que colocará el taller, solo en
  bordes indicados explícitamente, y muestra medidas terminadas y de corte.
- [x] El paquete avisa si hay piezas con cantos sin definir y no aplica
  descuentos supuestos. Una indicación vacía confirma que no llevan canto.
- [x] Usar los valores genéricos para las pruebas; la plantilla es configurable.
  La adaptación y confirmación del proveedor real corresponde a la etapa 6.

## 4. Validación de cortes

- [x] Prototipo: comparar cuatro órdenes de colocación. No garantiza el óptimo.
- [x] Probar perfiles, espesor incompatible, piezas que no caben, veta, márgenes
  y distintos tamaños de placa; se rechazan cambios automáticos de veta.
- [x] Generar una secuencia guillotina numerada y verificar geométricamente las
  regiones, el ancho de sierra y que las piezas no sean atravesadas por los cortes.
- [ ] **Trasladado a fase 2:** confirmar con el proveedor que la secuencia es
  realizable por su máquina; la comprobación geométrica no sustituye esa revisión.

## 5. Prueba integral del escritorio

- [x] Se generaron dos versiones del modelo, despiece, distribución y Excel
  mediante MCP; el usuario aprobó la visualización del informe 3D como prueba.
- [x] Se repitió el flujo mediante MCP con el perfil genérico, un ejemplo de
  descuento de canto y la secuencia; generó informe 3D, Excel y SVG.
- [x] El usuario realizó la prueba de cambio a 180 × 200 cm en otra charla;
  existen el modelo y los documentos generados en `../evaluacion-furniture-designer/escritorio-180/`.

## 6. Prueba real del taller — trasladada a fase 2

- [ ] Confirmar con un proveedor formato de pedido, placas, sierra, márgenes,
  veta, cantos y criterios de corte.
- [ ] Revisar medidas en sitio, espesor real, herrajes, uniones y estabilidad;
  contrastar documentos con el proveedor antes de fabricar.

## 7. Contribución al proyecto original — trasladada a fase 2

- [ ] Revisar el alcance, preparar documentación y pruebas y proponer los
  cambios al proyecto original mediante un pull request. Mantener el fork propio
  independientemente de la decisión del proyecto original.

## Fase 2: prioridad alta

Implementar la conversión asistida de imágenes a diseños 3D mediante IA y MCP,
con generación de documentos. Ver `ROADMAP-FASE-2.md`.

## Instalación de esta máquina

La copia está en `furniture-designer` y el ejecutable MCP en
`furniture-designer/.venv/bin/furniture-designer-mcp`. Codex lo tiene registrado
con el nombre `furniture-designer`; `codex mcp get furniture-designer` muestra
la configuración. Si se mueve el proyecto, se debe recrear el entorno y actualizar
esa ruta. No se ha modificado la configuración del servidor Offcut.

Para reproducir la instalación: disponer de Python 3.12 o superior y `uv`,
crear `.venv` con `uv venv`, instalar con `uv pip install -e .`, y registrar el
ejecutable con `codex mcp add furniture-designer -- /ruta/absoluta/a/.venv/bin/furniture-designer-mcp`.
La configuración de Codex pertenece a la máquina/entorno donde se ejecuta.
