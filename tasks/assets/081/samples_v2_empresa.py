"""Corpus v2: documentos PDF de empresa (contrato, adenda, informe anual y reglamento)."""

from sample_content import PdfSpec, _p

CONTRATO = PdfSpec(
    filename="contrato_mantenimiento.pdf",
    header="Contrato de mantenimiento informático · Termia Hogar S.L. y Redes Arnela S.L.",
    footer="Página {page} de {total}",
    pages=[
        _p(
            "En Logroño, a 14 de enero de 2025, se reúnen de una parte Termia Hogar S.L., fabricante de pequeños electrodomésticos, y de otra Redes Arnela S.L., empresa de servicios informáticos, que en adelante se llamarán el cliente y el proveedor.",
            "Objeto del contrato. El proveedor se encarga del mantenimiento preventivo y correctivo de los equipos informáticos del cliente: 85 puestos de trabajo, 4 servidores físicos y la red de las oficinas de Logroño y de la fábrica de Calahorra.",
            "El mantenimiento incluye la instalación de actualizaciones de seguridad, la gestión de las copias de seguridad semanales y la atención de las incidencias que comunique el personal del cliente.",
        ),
        _p(
            "Precio. El cliente pagará al proveedor 6.200 euros anuales, más el IVA correspondiente, en doce cuotas mensuales iguales que se facturarán el primer día laborable de cada mes.",
            "El precio se revisará cada año conforme al índice de precios de consumo publicado por el Instituto Nacional de Estadística. Las piezas de recambio y los equipos nuevos no están incluidos en el precio y se presupuestarán aparte.",
            "Las facturas se pagarán por transferencia bancaria en un plazo de treinta días desde su emisión.",
        ),
        _p(
            "Niveles de servicio. Una incidencia es crítica cuando impide trabajar a más de diez personas o deja sin servicio un servidor. Para las incidencias críticas, el proveedor responderá en un máximo de 2 horas y las resolverá en un máximo de 8 horas.",
            "Para las incidencias normales, el tiempo de respuesta es de 8 horas laborables y el de resolución, de tres días laborables.",
            "El servicio de atención funciona de lunes a viernes de 8:00 a 19:00. Fuera de ese horario solo se atienden incidencias críticas en el teléfono de guardia.",
        ),
        _p(
            "Penalizaciones. Por cada incidencia crítica que se resuelva fuera de plazo, el proveedor descontará un 5 % de la cuota mensual del mes siguiente. El total de descuentos de un mes no podrá superar el 20 % de la cuota.",
            "Confidencialidad. El proveedor guardará secreto sobre toda la información del cliente a la que tenga acceso, también después de terminar el contrato. Su personal firmará un compromiso de confidencialidad individual.",
            "El proveedor solo podrá subcontratar parte del servicio con la autorización previa y por escrito del cliente.",
        ),
        _p(
            "Duración. El contrato dura dos años desde la fecha de firma y se prorrogará automáticamente por periodos de un año si ninguna de las partes lo denuncia.",
            "Cualquiera de las partes puede resolver el contrato comunicándolo por escrito con un preaviso de 60 días.",
            "Al terminar el contrato, el proveedor entregará al cliente toda la documentación técnica, el inventario actualizado de equipos y las contraseñas de administración de los sistemas en un plazo de quince días.",
        ),
    ],
)

ADENDA = PdfSpec(
    filename="adenda_contrato_2026.pdf",
    header="Adenda al contrato de mantenimiento informático",
    footer="Página {page} de {total}",
    pages=[
        _p(
            "En Logroño, a 10 de diciembre de 2025, Termia Hogar S.L. y Redes Arnela S.L. acuerdan modificar el contrato de mantenimiento informático firmado el 14 de enero de 2025.",
            "Primera. A partir del 1 de enero de 2026, el mantenimiento incluye 15 puestos de trabajo más, con lo que el total pasa a 100 puestos, además de los 4 servidores.",
            "Segunda. Por esa ampliación, el precio del contrato pasa a ser de 6.900 euros anuales, más IVA, que se seguirán pagando en doce cuotas mensuales.",
        ),
        _p(
            "Tercera. El tiempo de respuesta para las incidencias críticas se reduce de 2 horas a 1 hora. El tiempo de resolución no cambia.",
            "Cuarta. Las copias de seguridad pasan a ser diarias, y el proveedor comprobará una vez al mes que se pueden restaurar, con un informe escrito.",
            "Quinta. Todo lo que no modifica esta adenda sigue igual que en el contrato original.",
        ),
    ],
)

INFORME = PdfSpec(
    filename="informe_anual_2025.pdf",
    header="Termia Hogar · Informe anual 2025",
    footer="Página {page} de {total}",
    pages=[
        "Carta de la directora general. 2025 ha sido el año en que Termia ha dejado de ser una marca regional. Hemos vendido más que nunca, hemos abierto un mercado nuevo y hemos reducido nuestras emisiones. Nada de eso habría sido posible sin las personas que trabajan en Logroño y en Calahorra. Gracias a todas. Inés Robledo, directora general.",
        "Resumen del año. La facturación de 2025 fue de 18,4 millones de euros, un 9 % más que el año anterior. El beneficio antes de impuestos fue de 1,7 millones de euros. La deuda financiera se redujo hasta los 2,1 millones gracias a la buena marcha de las ventas del segundo semestre.",
        "Ventas por producto. En 2025 vendimos 126.800 hervidores. El Termia K2 fue el más vendido, con 63.500 unidades; el K1 alcanzó 41.000 unidades y el K3 Pro, lanzado en marzo, 22.300 unidades. Los recambios supusieron el 6 % de la facturación.",
        "Mercados. España sigue siendo nuestro mercado principal, con el 71 % de las ventas. Portugal supuso el 14 %, Francia el 9 % y el resto de países el 6 %. En septiembre empezamos a vender en Francia a través de una cadena de tiendas de menaje.",
        "Producción. Todos los hervidores se fabrican en nuestra planta de Calahorra, que trabaja en dos turnos de lunes a viernes. En 2025 se instaló una segunda línea de montaje para el K3 Pro, con una inversión de 850.000 euros. La planta tiene 118 empleados.",
        "Personas. A 31 de diciembre de 2025, la plantilla era de 214 personas, 23 más que un año antes. El 46 % de la plantilla son mujeres, y también lo son 4 de los 7 miembros del comité de dirección. La rotación voluntaria fue del 7,5 %.",
        "Sostenibilidad. Las emisiones directas e indirectas de la empresa bajaron a 1.240 toneladas de CO2, un 11 % menos que en 2024. Las placas solares de la planta de Calahorra cubrieron el 38 % de la electricidad consumida. El 92 % del cartón de nuestros embalajes es reciclado.",
        "Calidad. La tasa de devoluciones fue del 1,9 % de los aparatos vendidos. La causa principal fue la acumulación de cal por no descalcificar, que explica casi la mitad de las devoluciones. Por eso en 2026 incluiremos un aviso de descalcificación en todos los modelos.",
        "Atención al cliente. El equipo de atención recibió 48.000 consultas, un 20 % más que en 2024. El tiempo medio de respuesta fue de 3 horas y 20 minutos y la satisfacción media de los clientes, de 8,6 sobre 10. El 35 % de las consultas trataba sobre la cal.",
        "Innovación. Dedicamos a investigación y desarrollo el 4,1 % de la facturación. La aplicación Termia, que controla el K3 Pro, llegó a 31.000 usuarios activos. Estamos desarrollando un hervidor de vidrio, cuyo lanzamiento está previsto para 2027.",
        "Riesgos. El precio del acero inoxidable subió un 14 % en 2025 y es el principal riesgo para nuestros márgenes. También dependemos de un único proveedor de resistencias, situado en Valencia, por lo que en 2026 homologaremos un segundo proveedor.",
        "Objetivos para 2026. Queremos facturar 20 millones de euros, empezar a vender en Italia, bajar la tasa de devoluciones al 1,5 % y cubrir con energía solar la mitad de la electricidad de la planta.",
    ],
)

REGLAMENTO = PdfSpec(
    filename="reglamento_interno.pdf",
    header="Reglamento interno de trabajo · Termia Hogar S.L.",
    footer="Página {page} de {total}",
    pages=[
        _p(
            "Artículo 1. Objeto. Este reglamento recoge las normas de organización y de convivencia que se aplican en Termia Hogar S.L.",
            "Artículo 2. Ámbito. Se aplica a todas las personas que trabajan en la empresa, en las oficinas de Logroño y en la planta de Calahorra, sea cual sea su tipo de contrato.",
            "Artículo 3. Vigencia. El reglamento entra en vigor el 1 de febrero de 2025 y sustituye al de 2019.",
            "Artículo 4. Comisión de seguimiento. Una comisión con dos personas de la dirección y dos de la representación del personal resolverá las dudas de interpretación.",
        ),
        _p(
            "Artículo 5. Jornada. La jornada ordinaria es de 38 horas y media semanales, de lunes a viernes.",
            "Artículo 6. Horario flexible. En las oficinas, la hora de entrada es flexible entre las 7:30 y las 9:30, y la presencia es obligatoria de 9:30 a 14:00.",
            "Artículo 7. Jornada intensiva. En julio y agosto, la jornada de oficinas es de 8:00 a 15:00.",
            "Artículo 8. Registro. Todas las personas registran su entrada y su salida en la aplicación de fichaje, también los días de teletrabajo.",
        ),
        _p(
            "Artículo 9. Permisos retribuidos. Además de los que fija la ley, se conceden 15 días naturales por matrimonio o registro como pareja de hecho, 2 días por mudanza y 1 día por la boda de un familiar de primer grado.",
            "Artículo 10. Formación. Cada persona tiene derecho a 40 horas anuales de formación dentro de su jornada.",
            "Artículo 11. Dietas. Los viajes de trabajo dentro de España dan derecho a una dieta de 26 euros diarios para comidas.",
            "Artículo 12. Kilometraje. El uso del coche propio en viajes de trabajo se compensa a 0,26 euros por kilómetro.",
        ),
        _p(
            "Artículo 13. Equipos de protección. En la planta es obligatorio usar calzado de seguridad y gafas de protección en las líneas de montaje.",
            "Artículo 14. Simulacros. Se hará un simulacro de evacuación dos veces al año en cada centro. El punto de encuentro es el aparcamiento norte.",
            "Artículo 15. Accidentes. Cualquier accidente, aunque sea leve, se comunica el mismo día a la persona responsable de prevención.",
            "Artículo 16. Contraseñas. Las contraseñas de los equipos informáticos tienen como mínimo 12 caracteres y se cambian cada 180 días.",
        ),
        _p(
            "Artículo 17. Regalos. No se pueden aceptar regalos de clientes ni de proveedores con un valor superior a 50 euros. Los que superen ese valor se devuelven con una nota de agradecimiento.",
            "Artículo 18. Conflictos de interés. Quien tenga un interés personal en una decisión de la empresa debe comunicarlo al comité de ética antes de participar en ella.",
            "Artículo 19. Canal de denuncias. La empresa tiene un canal de denuncias que permite comunicar irregularidades de forma anónima. Ninguna persona puede sufrir represalias por usarlo de buena fe.",
            "Artículo 20. Redes sociales. No se publica en redes sociales información interna de la empresa ni fotos de las líneas de montaje.",
        ),
        _p(
            "Artículo 21. Clases de faltas. Las faltas se clasifican en leves, graves y muy graves.",
            "Artículo 22. Prescripción. Las faltas leves prescriben a los 10 días, las graves a los 20 días y las muy graves a los 60 días desde que la empresa tiene conocimiento de ellas.",
            "Artículo 23. Sanciones. Las sanciones se comunican siempre por escrito y se informa de ellas a la representación del personal.",
            "Artículo 24. Revisión. El reglamento se revisará cada tres años o antes si cambia el convenio colectivo.",
        ),
    ],
)

PDFS_EMPRESA: list[PdfSpec] = [CONTRATO, ADENDA, INFORME, REGLAMENTO]
