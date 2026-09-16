---
name: prd-generation
version: 1.0.0
depends_on: []
stage: 1
governance: all
description: Generación interactiva de PRD para repositorio de información, definiendo propósito, usuarios, arquitectura y nivel de gobernanza.
---
# Skill: Generación de PRD para repositorio de información

## Objetivo
Construir un PRD básico y claro para un repositorio de información.
________________________________________
Instrucciones
•	No generar el PRD al inicio 
•	Hacer preguntas por sección 
•	No avanzar si falta información 
•	Al final, generar el PRD 
________________________________________
Flujo de interacción

0. Contexto Normativo (OBLIGATORIO — preguntar primero)
Solicitar si el sistema maneja datos sensibles sujetos a regulación. Esto condiciona la arquitectura completa:
- HIPAA (EE.UU.): cifrado en tránsito (TLS 1.2+) y reposo (AES-256), BAA requerido, audit trail completo.
- GDPR (UE): derecho al olvido (hard delete debe ser posible), consentimiento explícito registrable, data portability.
- Ley 20.584 (Chile): derechos del paciente, ficha clínica obligatoria, retención mínima de 15 años.
- LGPD (Brasil): similar a GDPR, aplica a datos de salud.
- Ninguna: sin restricciones normativas, pero se recomienda seguir mejores prácticas de todos modos.

No avanzar sin respuesta. Si el usuario no sabe, preguntar el país de operación y el tipo de datos (salud, financieros, educacionales) para inferir la regulación aplicable.

________________________________________
1.	Problema y propósito
Solicitar información sobre el problema a resolver y el propósito del repositorio. 
________________________________________
2.	Usuarios y uso
Solicitar quién usará el sistema y qué necesita hacer (ej: cargar datos, consultar, reportar). 
________________________________________
3.	Datos
Solicitar tipo de datos (estructurados, semi estructurados, no estructurados), dominio y volumen aproximado. 
________________________________________
4.	Fuentes de datos
Solicitar de dónde provienen los datos (manual, sistemas, APIs, sensores). 
________________________________________
5.	Arquitectura
Solicitar: 
•	Base de datos: ¿Los datos requieren integridad transaccional ACID (PostgreSQL, SQL Server) o priorizas escalabilidad horizontal y esquema flexible (MongoDB, DynamoDB)? Esto determina SQL vs NoSQL.
•	Infraestructura: nube (AWS/GCP/Azure) o local (on-premise) 
________________________________________
6.	Procesamiento de datos (ETL)
Solicitar: 
•	Cómo se obtienen los datos (manual o automático) 
•	Cada cuánto se cargan 
•	Si se transforman los datos antes de guardarlos 
________________________________________
7.	Gobernanza (obligatoria) 
Solicitar nivel de gobernanza:
Bajo
•	validaciones básicas 
•	sin control de acceso 
•	sin logs ni auditoría 
Medio
•	validaciones de datos 
•	logs de ejecución 
•	control de acceso básico 
Alto
•	validaciones completas 
•	control por roles 
•	auditoría y trazabilidad 
________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que el PRD generado:
- [ ] Incluye la sección de Contexto Normativo (regulación aplicable)
- [ ] Especifica SQL vs NoSQL con justificación
- [ ] Define tipo de datos (estructurados, semi, no estructurados)
- [ ] Indica fuente, frecuencia y transformaciones ETL
- [ ] Establece nivel de gobernanza (Bajo/Medio/Alto) explícitamente
- [ ] No contiene información inventada ni asumida

________________________________________
Condición de cierre
Antes de generar el PRD:
“Voy a generar el PRD. Confirma si la información es correcta.”
________________________________________
Formato de salida
PRD – Repositorio de Información
0. Contexto Normativo
• Regulación aplicable:
• Requisitos específicos:
1.	Propósito 
•	Problema: 
•	Objetivo: 
2.	Usuarios 
•	Tipos: 
•	Uso: 
3.	Datos 
•	Tipo: 
•	Dominio: 
•	Volumen: 
4.	Fuentes 
•	Origen: 
5.	Arquitectura 
•	Base de datos: (SQL / NoSQL) 
•	Infraestructura: (nube / local) 
6.	Procesamiento de datos 
•	Extracción: 
•	Frecuencia: 
•	Transformación: 
7.	Gobernanza 
•	Nivel: (Bajo / Medio / Alto) 
________________________________________
Reglas
•	No inventar información
•	No omitir contexto normativo
•	No omitir SQL vs NoSQL
•	No omitir ETL
•	No omitir gobernanza
•	No generar PRD incompleto