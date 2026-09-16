PRD – Repositorio de Información

1. Propósito

Problema: Necesidad de almacenar, mantener ordenados y poder recuperar a futuro los datos de los pacientes que asisten al consultorio.
Objetivo: Construir un repositorio de datos de fácil acceso para almacenar y consultar los datos personales de los pacientes de forma rápida y eficiente.
2. Usuarios

Tipos: 1 solo tipo de usuario (perfil general/único).
Uso: Almacenar (escribir/ingresar) y leer (consultar) los datos personales de los pacientes.
3. Datos

Tipo: Estructurados.
Dominio: Datos personales, correo de contacto y previsión de salud (Fonasa o Isapre).
Volumen: Aproximadamente 10 pacientes diarios.
4. Fuentes

Origen: Ingreso manual.
5. Arquitectura

Base de datos: SQL
Infraestructura: Local
6. Procesamiento de datos

Extracción: Carga manual por parte del usuario en el sistema.
Frecuencia: Paciente a paciente en el momento de la atención.
Transformación: Validación y estandarización de campos clave (RUT y correo electrónico) antes de ser guardados en la base de datos.
7. Gobernanza

Nivel: Bajo (validaciones básicas para la integridad de los datos, sin control de acceso complejo, sin logs ni auditoría adicional).