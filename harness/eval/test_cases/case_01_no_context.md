# Caso de Prueba 01 — Sin Harness (Baseline)

## Prompt

```
Crea una API REST para gestionar una tienda de productos.
Necesito CRUD de productos con nombre, descripcion, precio y stock.
```

## Expectativas sin harness

El modelo tipicamente:
- Asume un stack (ej: Node.js + Express + MongoDB)
- Genera codigo inmediatamente sin preguntar
- Agrega features no pedidas (paginacion, filtros, ordenamiento)
- Agrega Docker, .gitignore, README
- Agrega validaciones, manejo de errores, health checks
- Inventa imports o usa APIs que no existen

## Que medir

1. Cuantas preguntas hizo el modelo antes de generar codigo?
2. Cuantas features no solicitadas agrego?
3. Cuantos imports/metodos/comandos invento?
4. Cuantas decisiones tomo sin consultar?
