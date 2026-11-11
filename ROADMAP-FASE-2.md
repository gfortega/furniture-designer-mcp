# Fase 2: imagen a diseño de mueble

Prioridad: **alta**. Estado: planificación. Acordado el 11 de noviembre de 2026.

## Objetivo

Permitir que una persona comparta una o más imágenes de referencia y medidas
disponibles en una conversación; un asistente con visión interpretará la imagen,
propondrá un mueble editable y usará Furniture Designer mediante MCP para crear
un modelo 3D y generar despiece, distribución de placas y documentos. El flujo
debe poder producir un primer borrador automáticamente y dejar visibles sus
suposiciones y datos pendientes.

Una imagen por sí sola no establece con precisión dimensiones, profundidad,
piezas ocultas, uniones, resistencia ni materiales. Ningún resultado se tratará
como listo para fabricar sin confirmar los datos necesarios y revisar la
construcción. Respetar las medidas proporcionadas; no presentar estimaciones
como si fueran medidas verificadas.

## Prioridad alta: flujo de imagen a modelo

- [ ] Definir el primer caso de prueba y las clases de mueble admitidas. Empezar
  por muebles de tablero de melamina y ampliar según resultados.
- [ ] Analizar imágenes y extraer una propuesta estructurada de forma, piezas,
  orientación y características visibles, junto con las incertidumbres.
- [ ] Recibir medidas conocidas y marcar lo que no se puede deducir. Usar
  supuestos configurables cuando sea posible y pedir información cuando impida
  construir un modelo coherente.
- [ ] Ampliar las herramientas de Furniture Designer donde las plantillas
  actuales no cubran la geometría requerida; admitir modificaciones posteriores.
- [ ] Generar por MCP el modelo 3D y sus documentos con perfiles de proveedor,
  tapacantos y advertencias. Mostrar las diferencias entre dimensiones estimadas,
  terminadas y de corte.
- [ ] Probar con imágenes reales: comparar imagen y modelo, corregir medidas,
  revisar piezas y confirmar la coherencia del despiece y los cortes.

## Conexión con ChatGPT

- [ ] Validar primero el flujo con Codex y el servidor MCP local existente.
- [ ] Investigar y configurar, si se desea usar ChatGPT directamente, un
  transporte y autenticación compatibles. La conexión local por stdio ya
  probada en Codex no demuestra por sí sola que ChatGPT web pueda acceder a WSL.
- [ ] Probar el flujo completo en la superficie elegida, incluida la entrega de
  la imagen, la ejecución de herramientas y la visualización del resultado.

## Pendientes trasladados desde la fase 1

- [ ] Confirmar con el proveedor formato de pedido, placas, sierra, márgenes,
  veta y criterios de corte; adaptar la plantilla cuando se disponga de ellos.
- [ ] Verificar que la secuencia numerada es ejecutable con la máquina y los
  procedimientos del proveedor; la verificación geométrica no basta.
- [ ] Revisar medidas en sitio, espesor real, tapacantos, herrajes, uniones,
  anclajes, refuerzos y estabilidad. El taller colocará el tapacanto y se
  descontará de las dimensiones terminadas antes de pedir las piezas.
- [ ] Realizar la prueba real de taller y contrastar los documentos con el
  proveedor antes de fabricar.
- [ ] Revisar documentación y pruebas y, cuando corresponda, proponer los
  cambios al proyecto original mediante un pull request; conservar el fork.

## Criterios de aceptación

Con una imagen de prueba y las medidas necesarias, el flujo genera un modelo
editable que refleja las características confirmadas, señala las incertidumbres,
permite cambiar una medida y actualiza de forma coherente la geometría, el
despiece, los cortes y los documentos. Se comprueban las advertencias y se deja
constancia de qué información requiere validación antes de fabricar.
