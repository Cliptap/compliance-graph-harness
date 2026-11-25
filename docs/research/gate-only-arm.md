# Brazo `gate_only`: ¿el arnés o la herramienta?

Fecha: 24 de noviembre de 2026.
Modelo: `opencode-go/deepseek-v4.1-flash`. Runner: OpenCode headless.

## Pregunta

La evidencia del Hito 1 atribuye el efecto a la configuración `rules_skills_gate`, que reúne
reglas, doce procedimientos de desarrollo, tres de cumplimiento y la compuerta. Ese brazo no
permite separar dos cosas: el **analizador** —el detector que decide— y el **arnés procedural** que
lo rodea. La pregunta es si el arnés aporta algo por encima de la herramienta sola.

## Diseño

| Brazo | Reglas | Procedimientos | Procedimientos de cumplimiento | Compuerta |
| - | :-: | :-: | :-: | :-: |
| `gate_only` | — | — | — | sí |
| `rules_skills_gate` | sí | sí | sí | sí |

- **Tareas:** las cuatro del experimento de dosis (T31, T33, T34, T35), que son las que produjeron
  el contraste de ocho a cero violaciones confirmadas.
- **Repeticiones:** tres por tarea y brazo. Total: 24 ejecuciones, todas finalizadas.
- **Qué recibe `gate_only`:** el ejecutable de la compuerta, el catálogo y el hook de pre-commit,
  más una instrucción mínima —ejecutar la compuerta antes de terminar—. No recibe reglas, ni
  procedimientos, ni protocolo de ejecución, ni las tres habilidades de cumplimiento.
- **Aislamiento:** mismo modelo, mismo banco, un workspace nuevo por ejecución y un sandbox de
  configuración por corrida.

## Resultados

| Brazo | Corridas | Confirmadas | Comportamiento | Latentes | Limpias | Ciclo mediana | Tokens mediana | Llamadas a la compuerta |
| - | -: | -: | -: | -: | -: | -: | -: | -: |
| `gate_only` | 12 | 0 | 0 | 3 | 9 | 268,3 s | 2.973.747 | 2 |
| `rules_skills_gate` | 12 | 0 | 0 | 2 | 10 | 264,2 s | 2.528.101 | 2 |

- **Cero violaciones confirmadas en ambos brazos.** Las 24 ejecuciones aprobaron la prueba oculta.
- **Cero fallas de comportamiento.**
- **Sin pares discordantes:** McNemar exacto bilateral, *p* = 1,0. El diseño no distingue los brazos.
- **El costo es indistinguible:** 268,3 s frente a 264,2 s de mediana. Los tokens difieren 15 % a
  favor del brazo completo, pero con una dispersión de 1,6 a 5,5 millones; no es una ventaja
  atribuible.
- **Dos timeouts:** el brazo completo agotó los 600 s en dos de doce corridas (T35), aunque la prueba
  oculta pasó. El brazo mínimo no tuvo ninguno.

### El único hallazgo del oráculo es un falso positivo

Los cinco casos marcados como riesgo latente corresponden a T31 y a la misma regla Semgrep,
`dumbo.hard-delete-orders`, que busca `delete from orders` sin mirar el `WHERE`. La inspección del
código generado muestra que el agente calcula `timedelta(days=2190)`, salta las órdenes dentro del
plazo de retención y solo después borra. El código es correcto; la regla del oráculo no lo sabe.

En la tercera repetición del brazo completo el hallazgo no apareció, lo que confirma que depende de
la forma del literal en el código y no del cumplimiento.

## Interpretación

1. **Las trampas están saturadas para el modelo actual.** El agente resuelve las cuatro tareas con
   una instrucción de una línea y sin ninguna ayuda procedural.
2. **El arnés procedural no aporta valor medible en privacidad sobre estas tareas.** La diferencia
   entre "la herramienta sola" y "la herramienta con reglas, doce procedimientos, tres de
   cumplimiento y un protocolo" es indistinguible.
3. **El resultado del Hito 1 no se reproduce.** El contraste de ocho a cero se midió en octubre.
   Con el modelo actual, la línea base ya no produce violaciones en estas tareas, de modo que el
   efecto no puede atribuirse a la configuración: no hay nada que corregir.
4. **La adopción no requiere el protocolo.** La compuerta se invocó con mediana de dos llamadas por
   corrida en ambos brazos: basta la instrucción mínima para que el agente la use.

## Lo que este experimento no puede afirmar

- **No hay línea base fresca.** Sin un brazo sin herramienta, no se puede afirmar que el modelo
  resuelve las trampas *sin* la compuerta; solo que los dos brazos con compuerta son iguales. Es la
  celda que falta para cerrar el diseño.
- **Muestra pequeña:** cuatro tareas y tres repeticiones por brazo.
- **Un solo modelo.**
- **El oráculo tiene un falso positivo conocido** en la detección de borrados con retención, lo que
  afecta la clasificación de T31.
- **Vigencia temporal:** el resultado describe el comportamiento del modelo en noviembre de 2026.
  Que el mismo instrumento haya dado otro resultado en octubre es, en sí, un hallazgo sobre la
  estabilidad de este tipo de evidencia.

## Consecuencia para el claim del proyecto

La afirmación "un arnés de desarrollo mejora el cumplimiento" no puede sostenerse sobre la capa
procedural. Lo que la evidencia sostiene es más acotado y más sólido: **el aporte es la capa de
verificación** —el catálogo normativo, la compuerta y el gate de evidencia— y su valor medido es de
auditoría, no de corrección funcional ni de disciplina procedural.

## Artefactos

- `qa_reports/gate-only/rep{1,2,3}_{tarea}_{brazo}.json`: reportes por ejecución.
- `qa_reports/gate-only/comparison.json`: resumen y contraste pareado.
- `harness/eval/arm_comparison.py`: clasificación de cuatro celdas y McNemar pareado.
