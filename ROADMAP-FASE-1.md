# Fase 1: diseño y preparación de cortes

Actualizado: 11 de noviembre de 2026. Estado: en desarrollo; los resultados
son borradores hasta su revisión por el taller y el proveedor.

## 1. Instalación y conexión

- [x] Instalar el fork en un entorno `.venv` persistente dentro de este proyecto.
- [x] Registrar `furniture-designer` como servidor MCP de Codex en WSL.
- [x] Probar el ejecutable instalado con un cliente MCP en otro proceso: ocho
  pruebas aprobadas, incluido el despiece provisional del escritorio.
- [ ] Confirmar que las herramientas aparecen y responden desde una sesión de
  Codex que cargue la configuración nueva. El aislamiento de este entorno
  bloqueó anteriormente una prueba entre procesos; fuera de él funcionó.
- [ ] Documentar y comprobar una instalación reproducible en otra máquina.

## 2. Diseño y edición

- [ ] Evaluar cómo crear, visualizar y modificar un escritorio en L, incluyendo
  soporte, dimensiones y uniones. Hasta ahora se probó una lista de piezas;
  no se ha verificado la edición de un modelo 3D en L.
- [ ] Implementar o integrar lo que falte y probar la actualización del despiece.

## 3. Entrega al proveedor

- [x] Prototipo: perfiles de placa y sierra, despiece CSV/XLSX y agrupación que
  considera material, veta y tapacantos.
- [ ] Definir márgenes de escuadrado y medidas antes/después del tapacanto.
- [ ] Incluir en la entrega resumen de placas y diagrama de cortes, y ajustar
  columnas y convenciones al proveedor.

## 4. Validación de cortes

- [x] Prototipo: comparar cuatro órdenes de colocación. No garantiza el óptimo.
- [ ] Probar con varios materiales y espesores, piezas que no caben, veta,
  márgenes y tamaños reales de placa. Evitar aceptar silenciosamente cambios de veta.
- [ ] Revisar que la distribución y la secuencia sean realizables por el proveedor.

## 5. Prueba integral del escritorio

- [ ] Crear el modelo 3D, modificar una medida y comprobar que se actualicen el
  modelo, despiece, distribución y documentos. La prueba previa solo cubrió
  medidas de piezas, distribución y Excel mediante MCP.

## 6. Prueba real del taller

- [ ] Confirmar con un proveedor formato de pedido, placas, sierra, márgenes,
  veta, cantos y criterios de corte.
- [ ] Revisar medidas en sitio, espesor real, herrajes, uniones y estabilidad;
  contrastar documentos con el proveedor antes de fabricar.

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
