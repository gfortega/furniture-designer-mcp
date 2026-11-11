# Fase 1: diseño y preparación de cortes

Actualizado: 11 de noviembre de 2026. Estado: en desarrollo; los resultados
son borradores hasta su revisión por el taller y el proveedor.

## Situación actual

Estamos en la preparación de la entrega al proveedor y la validación de cortes
(etapas 3 y 4). La configuración genérica utiliza provisionalmente tablero
2600 × 1830 × 18 mm, sierra de 3,2 mm, margen de 5 mm por borde y canto de
1 mm en los bordes seleccionados; sin restricción de veta. Son supuestos, no
condiciones confirmadas de un proveedor. El taller coloca el tapacanto y se
debe descontar su espesor antes de pedir el corte.

La última verificación ejecutó 18 pruebas, incluida la exportación con descuento
de tapacantos por MCP entre procesos. Ver archivos de ejemplo en
`../evaluacion-furniture-designer/paso-2-escritorio-l/`.

## 1. Instalación y conexión

- [x] Instalar el fork en un entorno `.venv` persistente dentro de este proyecto.
- [x] Registrar `furniture-designer` como servidor MCP de Codex en WSL.
- [x] Probar el ejecutable instalado con un cliente MCP en otro proceso: ocho
  pruebas aprobadas, incluido el despiece provisional del escritorio.
- [x] El usuario confirmó que las herramientas responden desde otra sesión de
  Codex que cargó la configuración nueva. El aislamiento de este entorno
  bloqueó anteriormente una prueba entre procesos; fuera de él funcionó.
- [ ] Documentar y comprobar una instalación reproducible en otra máquina.

## 2. Diseño y edición

- [x] Crear una plantilla MCP para un escritorio en L provisional y regenerar
  la geometría y el despiece al cambiar sus medidas. Se verificaron dimensiones,
  ausencia de solapamientos entre cajas y consistencia de las orientaciones del
  informe y de FreeCAD, y se generó un informe con dos iteraciones.
- [x] El usuario revisó la visualización 3D y confirmó que es adecuada para la
  prueba. La interfaz existente visualiza el modelo; cambiar medidas se hace
  regenerándolo mediante MCP, no arrastrando piezas.
- [ ] Definir y validar soportes, refuerzos, anclajes y uniones antes de fabricar.

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
- [ ] Confirmar márgenes, material, espesor real y tapacantos con el proveedor
  y el taller; los valores predeterminados son provisionales.
- [ ] Ajustar columnas y convenciones al proveedor real y revisar el diagrama.

## 4. Validación de cortes

- [x] Prototipo: comparar cuatro órdenes de colocación. No garantiza el óptimo.
- [ ] Probar con varios materiales y espesores, piezas que no caben, veta,
  márgenes y tamaños reales de placa. Evitar aceptar silenciosamente cambios de veta.
- [ ] Desarrollar y verificar la secuencia numerada de cortes; el SVG actual
  muestra distribución, pero no orden de pasadas ni cortes numerados.
- [ ] Revisar que la distribución y la secuencia sean realizables por el proveedor.

## 5. Prueba integral del escritorio

- [x] Se generaron dos versiones del modelo, despiece, distribución y Excel
  mediante MCP; el usuario aprobó la visualización del informe 3D como prueba.
- [ ] Repetir el flujo integral con los perfiles actuales, el descuento explícito
  de tapacantos y la secuencia de cortes cuando esté disponible.

## 6. Prueba real del taller

- [ ] Confirmar con un proveedor formato de pedido, placas, sierra, márgenes,
  veta, cantos y criterios de corte.
- [ ] Revisar medidas en sitio, espesor real, herrajes, uniones y estabilidad;
  contrastar documentos con el proveedor antes de fabricar.

## 7. Contribución al proyecto original

- [ ] Revisar el alcance, preparar documentación y pruebas y proponer los
  cambios al proyecto original mediante un pull request. Mantener el fork propio
  independientemente de la decisión del proyecto original.

## Después de la fase 1

Evaluar imágenes como entrada para proponer diseños 3D mediante IA y MCP. Las
dimensiones y decisiones constructivas deberán confirmarse antes del despiece.

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
