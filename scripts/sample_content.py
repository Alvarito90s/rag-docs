"""Contenido ficticio para los documentos de prueba."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfSpec:
    """Un PDF: cabecera/pie opcionales y el texto de cada página."""

    filename: str
    header: str | None
    footer: str | None
    pages: list[str]


@dataclass(frozen=True)
class DocxSpec:
    """Un DOCX: título, secciones (encabezado, párrafos) y una tabla."""

    filename: str
    title: str
    sections: list[tuple[str, list[str]]]
    table: list[list[str]]
    table_after_section: int


def _p(*paras: str) -> str:
    """Une párrafos con salto de párrafo."""
    return "\n\n".join(paras)


PDFS: list[PdfSpec] = [
    PdfSpec(
        filename="contrato_servicios.pdf",
        header="Contrato de prestación de servicios · Nubaria Datos S.L.",
        footer="Página {page} de {total}",
        pages=[
            _p(
                "El presente contrato de prestación de servicios se celebra bajo la legislación vigente en España. El presente contrato se firma en Valladolid el 3 de marzo de 2025. Las partes intervinientes son Nubaria Datos Sociedad Limitada con domicilio en Valladolid.",
                "El alcance del servicio comprende el desarrollo de software personalizado y la prestación de soporte técnico especializado para la infraestructura digital de la organización. Los plazos y hitos de entrega se definirán en un anexo técnico.",
                "Las condiciones de confidencialidad regirán durante toda la vigencia del contrato y cinco años adicionales tras su finalización. Cada parte se compromete a proteger la información confidencial recibida de la otra con el mismo nivel de cuidado.",
            ),
            _p(
                "El precio total del servicio asciende a 4.800 euros anuales, pagaderos por trimestres vencidos. Cada factura generada deberá ser abonada en un plazo máximo de quince días naturales desde su emisión según los términos establecidos.",
                "Las condiciones de pago se regirán por lo establecido en la legislación mercantil vigente y cualquier disputa se resolverá mediante arbitraje conforme a las normas de la institución correspondiente. El cliente dispondrá de un canal de facturación digital.",
                "En caso de retraso en el pago se aplicará un interés de demora equivalente al tipo de referencia oficial más tres puntos porcentuales según normativa vigente en el territorio español. Estas condiciones económicas forman parte esencial del acuerdo.",
            ),
            _p(
                "El proveedor ofrece una garantía de dos años sobre todos los desarrollos entregados. Durante este período se cubrirán las correcciones de errores y las modificaciones necesarias para el correcto funcionamiento de los sistemas informáticos entregados al cliente final.",
                "La garantía no ampara daños causados por uso indebido ni modificaciones no autorizadas del software realizadas por personal ajeno al equipo técnico del proveedor. El cliente deberá notificar cualquier incidencia durante el periodo garantizado mediante el canal oficial.",
                "Los informes mensuales de actividad forman parte de las obligaciones contractuales del proveedor y se entregan en formato digital al cliente cada mes al finalizar el periodo de facturación correspondiente a cada trimestre del año.",
            ),
            _p(
                "Cualquiera de las partes podrá resolver el contrato con un preaviso de 30 días naturales. Comunicado por escrito con validez legal y efectos inmediatos a partir de la fecha de notificación de la resolución, la resolución anticipada implicará la liquidación de los servicios ya prestados hasta la fecha de efecto oficial de la rescisión contractual.",
                "El cliente podrá rescindir unilateralmente sin penalización si el proveedor incumple en tres ocasiones dentro de un mismo trimestre las obligaciones contractuales establecidas. Tras la finalización del contrato el proveedor entregará todos los códigos fuente y documentación.",
                "Se realizará una reunión de cierre para verificar la entrega completa de todos los activos digitales generados durante la vigencia del acuerdo. Las obligaciones de protección de datos seguirán aplicándose conforme al Reglamento General vigente en todo el territorio.",
            ),
        ],
    ),
    PdfSpec(
        filename="manual_cafetera.pdf",
        header="Manual de usuario · Cafetera Brevia X2",
        footer="Brevia X2 · página {page}",
        pages=[
            _p(
                "La cafetera Brevia X2 ha sido diseñada para ofrecer un rendimiento excepcional en hogares y oficinas pequeñas de cualquier tamaño actual. Su construcción robusta combina acero inoxidable con plásticos de alta resistencia tratados antiarañazos para mayor durabilidad y presentación visual atractiva.",
                "El sistema de calentamiento rápido permite preparar una taza de café en apenas un minuto desde el momento del encendido del aparato electrodoméstico. El diseño compacto se adapta a cualquier encimera moderna sin ocupar espacio innecesario en la cocina del hogar.",
                "Cada unidad se entrega con todos los accesorios completos incluidos para un uso inmediato sin necesidad de compras adicionales. La caja contiene la cafetera principal, el filtro permanente de acero inoxidable, el dosificador de café, un paño de limpieza especial.",
            ),
            _p(
                "El depósito de agua tiene una capacidad de 1,8 litros. Esta medida permite preparar aproximadamente doce tazas estándar sin necesidad de rellenar el depósito durante el uso matutino habitual y cotidiano del aparato electrodoméstico en la cocina.",
                "El depósito es completamente extraíble para facilitar el lavado diario bajo el grifo con agua limpia y jabón neutro suave para mantener una higiene óptima en todo momento y evitar acumulaciones de bacterias.",
                "Puede utilizarse agua filtrada, embotellada o del grifo dependiendo de la dureza de la zona donde se instale el aparato electrodoméstico en la cocina del hogar o la oficina del trabajador.",
            ),
            _p(
                "La limpieza diaria consiste en vaciar el posavasos y enjuagarlo con agua tibia bajo el grifo cada mañana antes del primer uso. Retire los residuos del filtro metálico y deseche el café utilizado en el contenedor correspondiente con regularidad para mantener la higiene.",
                "Limpie la superficie exterior con un paño ligeramente humedecido en agua y detergente suave no abrasivo nunca para proteger los acabados metálicos del equipo de preparación.",
                "Nunca utilice productos abrasivos, disolventes fuertes ni lejía que podrían dañar irremediablemente los acabados del aparato electrodoméstico y sus componentes internos de plástico.",
            ),
            _p(
                "Cada semana realice una limpieza profunda retirando todas las piezas desmontables del aparato con cuidado y máxima precaución. Lave el filtro permanente, el posavasos y el depósito con agua templada abundante y jabón neutro líquido suave para eliminar los residuos acumulados.",
                "Enjuague abundantemente bajo el grifo con agua corriendo y seque completamente con un paño limpio antes de volver a montar todos los componentes del equipo con precisión y cuidado.",
                "Pase un paño húmedo por el interior del cabezal de distribución donde se deposita el café molido durante la preparación diaria del mismo para mantener un flujo constante.",
            ),
            _p(
                "Se recomienda descalcificar la cafetera cada 200 ciclos de preparación. El mantenimiento adecuado incluye la descalci-\nficación periódica que previene daños en los componentes internos del equipo de preparación de bebidas calientes.",
                "Prepare la disolución descalcificadora siguiendo las proporciones exactas indicadas por el fabricante del producto químico específico recomendado por el servicio técnico oficial para garantizar resultados óptimos.",
                "Vierta la disolución en el depósito y sitúe un recipiente de al menos dos litros bajo el cabezal de salida principal para recibir todo el líquido de descalcificación eliminado del interior.",
            ),
            _p(
                "El uso de agua filtrada reduce significativamente la frecuencia necesaria de mantenimiento preventivo del sistema interno de tuberías y válvulas. De este modo se prolonga la vida útil del aparato y se mantiene la calidad del café preparado de forma consistente y uniforme en cada taza.",
                "El indicador luminoso se activa automáticamente cuando el sistema detecta un aumento de la resistencia térmica por acumulación de cal en las superficies internas del equipo de calentamiento. Mantener el aparato limpio garantiza un rendimiento óptimo.",
                "Mantener el aparato en un lugar ventilado y alejado de fuentes de calor excesivas contribuye a su buen funcionamiento y extendida duración en el tiempo para el usuario habitual.",
            ),
            _p(
                "El código de error E-17 indica que el depósito de agua está vacío. Verifique primero que el depósito está correctamente encajado en su lugar asignado con firmeza y alineación adecuada antes de continuar.",
                "A continuación rellene el depósito con agua potable hasta la marca máxima visible claramente marcada en el lateral derecho del mismo depósito de agua para permitir el correcto funcionamiento.",
                "Si el error persiste después de rellenar retire el depósito inspeccione el sensor de nivel y vuelva a colocarlo con firmeza para evitar errores persistentes que impidan el funcionamiento.",
            ),
            _p(
                "Los demás códigos de error disponibles incluyen el E-24 para posavasos lleno, E-11 para fallos de calentamiento eléctrico del sistema interno. El E-05 señala problemas con la bomba de presión interna del equipo de preparación del café. El código E-20 indica necesidad de descalcificación.",
                "Cada error viene acompañado de un parpadeo específico del indicador luminoso que facilita la identificación rápida del problema en la cafetera.",
                "Consulte siempre la sección de resolución de problemas del manual antes de solicitar asistencia técnica externa profesional para evitar daños mayores en el sistema interno y prolongar la vida útil del electrodoméstico considerablemente.",
            ),
            _p(
                "La garantía de la cafetera cubre defectos de fabricación durante tres años. Durante este periodo se realizarán las reparaciones necesarias sin coste adicional para el titular del equipo electrodoméstico.",
                "La garantía cubre las piezas defectuosas y la mano de obra en centros autorizados oficialmente por el fabricante español del equipo electrodoméstico con profesionales cualificados.",
                "No cubre daños causados por uso indebido, negligencia grave, accidentes domésticos ni instalación incorrecta del equipo por parte del usuario final del producto.",
            ),
            _p(
                "El servicio técnico ofrece soporte gratuito durante los primeros doce meses completos tras la compra del aparato electrodoméstico Brevia X2. Los profesionales están formados continuamente en las últimas novedades de toda la gama Brevia comercializada actualmente en España y Portugal con cobertura internacional para todos los países miembros de la Unión Europea. Los profesionales están especialmente formados en la gama Brevia X2.",
                "Disponemos de piezas originales en stock permanente para minimizar los tiempos de reparación del equipo defectuoso con máxima eficiencia operativa.",
                "Para consultas adicionales visite nuestra página web oficial o las preguntas frecuentes publicadas periódicamente en nuestro portal de atención al cliente.",
            ),
        ],
    ),
    PdfSpec(
        filename="paper_rag_resumen.pdf",
        header=None,
        footer=None,
        pages=[
            _p(
                "Recent advances in information retrieval have highlighted the benefits of combining multiple ranking strategies to improve overall performance significantly across diverse application domains and practical use cases evaluated in multiple real-world projects conducted by the research group at the university center for information systems.",
                "Hybrid retrieval improved Hit@5 from 0.71 to 0.84 on the internal benchmark. Our approach leverages both dense vector similarity and lexical matching to capture complementary aspects of document relevance effectively across diverse query types and subject matter areas in our experiments.",
            ),
            _p(
                "The authors used a chunk size of 512 tokens with an overlap of 64 tokens. This configuration was selected based on empirical evaluation across multiple document collections and retrieval scenarios with diverse content types and formats.",
                "Smaller chunks capture specific topical signals more precisely while larger chunks improve contextual understanding of complex and ambiguous queries during the ranking phase. We experimented with various configurations and report detailed performance curves for each evaluated parameter setting.",
                "Additional experiments evaluated the impact of different embedding models on retrieval quality. The results demonstrate that hybrid approaches consistently outperform pure dense or pure sparse methods across all evaluated metrics and domains tested in our research.",
            ),
        ],
    ),
]

DOCXS: list[DocxSpec] = [
    DocxSpec(
        filename="politica_vacaciones.docx",
        title="Política de vacaciones 2025",
        sections=[
            (
                "Días de vacaciones",
                [
                    "Cada empleado dispone de 23 días laborables de vacaciones al año.",
                    "Los días se calculan sobre la base del calendario laboral oficial vigente en España para todo el territorio nacional. Las fiestas locales y nacionales no se computan como días de vacaciones adicionales sino como días festivos. El empleado puede solicitar las fechas con una antelación mínima de quince días naturales por escrito.",
                ],
            ),
            (
                "Días adicionales por antigüedad",
                [
                    "Los empleados con más de cinco años en la empresa reciben un día adicional por cada trienio completo acumulado en la organización.",
                    "Los días adicionales se acumulan durante la vigencia del contrato y no se compensan económicamente en ninguna circunstancia particular. En caso de baja voluntaria los días no disfrutados se liquidarían conforme a la legislación vigente en cada momento del año. La antigüedad se verifica trimestralmente con recursos humanos.",
                ],
            ),
            (
                "Solicitudes",
                [
                    "Las solicitudes deben enviarse con al menos 15 días de antelación al responsable directo del equipo de trabajo asignado.",
                    "El responsable aprobará o propondrá otras fechas en un plazo máximo de tres días laborables desde la recepción formal de la solicitud. Las vacaciones podrán disfrutarse de forma continuada o fraccionada según acuerdo mutuo formalizado por escrito entre las partes. En periodos de máxima actividad la empresa propondrá fechas alternativas.",
                ],
            ),
        ],
        table=[
            ["Antigüedad", "Días adicionales"],
            ["Menos de 5 años", "0"],
            ["De 5 a 10 años", "2"],
            ["Más de 10 años", "4"],
        ],
        table_after_section=1,
    ),
]

TEXT_FILES: dict[str, str] = {
    "apuntes_redes.md": (
        "# Apuntes de redes\n"
        "\n"
        "## Modelo OSI\n"
        "\n"
        "El modelo OSI divide la comunicación en siete capas: física, enlace, "
        "red, transporte, sesión, presentación y aplicación.\n"
        "\n"
        "## Puertos habituales\n"
        "\n"
        "| Protocolo | Puerto | Transporte |\n"
        "| --- | --- | --- |\n"
        "| SSH | 22 | TCP |\n"
        "| SMTP | 25 | TCP |\n"
        "| DNS | 53 | UDP |\n"
        "| HTTPS | 443 | TCP |\n"
        "\n"
        "## TCP frente a UDP\n"
        "\n"
        "TCP garantiza la entrega ordenada de los segmentos; UDP no.\n"
    ),
    "glosario_interno.md": (
        "# Glosario interno\n"
        "\n"
        "- **SKU-4471-B**: referencia interna del filtro de agua de la Brevia X2.\n"
        "- **RGPD**: Reglamento General de Protección de Datos.\n"
        "- **KPI-07**: tasa de resolución en primer contacto.\n"
        "- **SLA-Oro**: acuerdo de nivel de servicio con respuesta en menos de 4 horas.\n"
    ),
    "notas_reunion.txt": (
        "Reunión del 12 de mayo de 2025\n"
        "Asistentes: Marta Ibáñez, Jorge Salas, Lucía Pardo\n"
        "\n"
        "1. Se acordó migrar el servidor de pruebas a la versión 3.2 antes del 30 de junio.\n"
        "2. Responsable de la migración: Marta Ibáñez.\n"
        "3. La próxima revisión del presupuesto será en septiembre.\n"
    ),
}
