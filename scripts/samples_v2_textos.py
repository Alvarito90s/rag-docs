"""Corpus v2: DOCX (dos versiones de la política de teletrabajo y las tarifas), Markdown y TXT."""

from sample_content import DocxSpec


def teletrabajo(
    anio: str, dias: dict[str, str], compensacion: str, antelacion: str, extra: str
) -> DocxSpec:
    """Política de teletrabajo de un año: mismas secciones, distintas cifras."""
    return DocxSpec(
        filename=f"politica_teletrabajo_{anio}.docx",
        title=f"Política de teletrabajo {anio}",
        sections=[
            (
                "Objeto",
                [
                    f"Esta política fija cuántos días de teletrabajo puede hacer cada colectivo de Termia Hogar durante {anio} y en qué condiciones.",
                    "El teletrabajo es voluntario y reversible: la persona puede volver al trabajo presencial completo avisando con una semana de antelación.",
                ],
            ),
            (
                "Días de teletrabajo por colectivo",
                [
                    "La tabla siguiente recoge el máximo de días de teletrabajo a la semana de cada colectivo."
                ],
            ),
            (
                "Condiciones",
                [
                    f"Las solicitudes se envían a la persona responsable del equipo con {antelacion} días naturales de antelación.",
                    f"La empresa abona una compensación de {compensacion} euros mensuales por gastos de conexión y suministros a quien teletrabaje al menos un día a la semana.",
                    extra,
                ],
            ),
        ],
        table=[
            ["Colectivo", f"Días de teletrabajo a la semana ({anio})"],
            ["Personal de oficina", dias["oficina"]],
            ["Atención al cliente", dias["atencion"]],
            ["Personal de planta", dias["planta"]],
            ["Comité de dirección", dias["direccion"]],
        ],
        table_after_section=1,
    )


DOCXS_V2: list[DocxSpec] = [
    teletrabajo(
        "2025",
        {"oficina": "2 días", "atencion": "1 día", "planta": "0 días", "direccion": "2 días"},
        compensacion="25",
        antelacion="7",
        extra="Los días de teletrabajo se eligen libremente cada semana, siempre que el equipo tenga a alguien presencial cada día.",
    ),
    teletrabajo(
        "2026",
        {"oficina": "3 días", "atencion": "2 días", "planta": "0 días", "direccion": "3 días"},
        compensacion="35",
        antelacion="10",
        extra="Los martes son día presencial obligatorio para toda la plantilla de oficinas, para facilitar las reuniones de equipo.",
    ),
    DocxSpec(
        filename="tarifas_soporte.docx",
        title="Planes de soporte Termia",
        sections=[
            (
                "Planes disponibles",
                [
                    "Termia ofrece tres planes de soporte para sus hervidores. El plan Básico viene incluido con cualquier compra; los planes Plus y Premium se contratan aparte y se pagan cada mes.",
                    "Los planes se pueden contratar en cualquier momento desde la tienda online y se pueden cancelar sin permanencia.",
                ],
            ),
            (
                "Comparativa",
                ["La tabla compara el precio y lo que incluye cada plan."],
            ),
            (
                "Condiciones",
                [
                    "El descuento en reparaciones se aplica sobre la mano de obra y las piezas de las reparaciones fuera de garantía.",
                    "El plan Premium solo se puede contratar para el K3 Pro.",
                ],
            ),
        ],
        table=[
            [
                "Plan",
                "Precio",
                "Tiempo de respuesta",
                "Descuento en reparaciones",
                "Recogida a domicilio",
            ],
            ["Básico", "Gratis", "72 horas", "Sin descuento", "No"],
            ["Plus", "4,99 euros al mes", "24 horas", "20 %", "No"],
            ["Premium", "9,99 euros al mes", "4 horas", "40 %", "Sí"],
        ],
        table_after_section=1,
    ),
]

ONBOARDING = """# Guía de incorporación

Bienvenida a Termia Hogar. Esta guía reúne lo que necesitas saber durante tu primera semana. Si algo no está claro, pregunta a la persona que te acompaña en la incorporación.

## Primer día

El primer día llega a las 9:00 a la recepción de la oficina de Logroño, en la calle Portales 31. Allí te recogerá tu acompañante, que te presentará al equipo y te enseñará la oficina. Por la tarde tendrás una reunión de bienvenida con Recursos Humanos.

## Tarjeta de acceso

La tarjeta de acceso al edificio la entrega la recepción el primer día, a cambio de una fianza de 10 euros que se devuelve al dejar la empresa. Si la pierdes, avisa enseguida a recepción para que la anulen; la nueva cuesta 15 euros.

## Portátil y cuentas

Tu portátil estará preparado en tu puesto. La primera vez que lo enciendas tendrás que cambiar la contraseña temporal y activar la verificación en dos pasos con la aplicación del móvil. Si el portátil falla, abre una incidencia en el portal de soporte informático.

## Conexión desde casa

Para trabajar fuera de la oficina tienes que conectarte a la VPN corporativa. Se instala sola en el portátil y se activa con tu usuario y el código de la verificación en dos pasos. Sin VPN no podrás abrir las carpetas compartidas.

## Wifi

En la oficina hay dos redes. La red Termia-Equipo es para los portátiles de la empresa y se conecta sola. Los invitados y los móviles personales usan la red Termia-Visitas, cuya contraseña cambia cada lunes y está en el cartel de recepción.

## Formación inicial

Durante el primer mes tienes que completar tres cursos en la plataforma de formación: prevención de riesgos, protección de datos y el reglamento interno. Cada curso dura una hora y termina con un test corto.

## Comedor y aparcamiento

La oficina tiene un comedor en la planta baja con microondas y nevera, abierto de 13:00 a 16:00. El aparcamiento del edificio es solo para visitas; el personal puede pedir una plaza en el aparcamiento público de la calle Bretón con un 50 % de descuento.

## Contactos útiles

Recursos Humanos: rrhh@termia.example. Soporte informático: portal de soporte o extensión 400. Prevención de riesgos: extensión 410. Para cualquier urgencia fuera de horario, llama a seguridad del edificio.
"""

FAQ = """# Preguntas frecuentes de clientes

## ¿Puedo calentar leche en el hervidor?

No. Los hervidores Termia están diseñados solo para agua. La leche se pega a la resistencia, se quema y puede estropear el sensor. Ese daño no lo cubre la garantía.

## El agua tiene un sabor raro los primeros días

Es normal en un aparato nuevo. Antes del primer uso, hierve el depósito lleno tres veces y tira el agua cada vez. Si el sabor sigue después de una semana, escríbenos.

## ¿Funciona en otros países?

Los hervidores funcionan con corriente de 220 a 240 voltios y enchufe europeo. No uses adaptadores de tensión: en países con 110 voltios el aparato no calentará bien y puede dañarse.

## ¿Cómo registro mi hervidor en la aplicación?

Solo el K3 Pro se conecta a la aplicación Termia. Descárgala, activa el Bluetooth del móvil y mantén pulsado el botón de encendido del hervidor durante cinco segundos hasta que la pantalla muestre un parpadeo.

## ¿Dónde compro recambios?

Los recambios se compran en la tienda online de Termia o en las tiendas que venden nuestros hervidores. Las referencias y los precios están en el catálogo de recambios.

## ¿Cuánto tarda un pedido?

Los pedidos llegan en 48 a 72 horas a la península. A Baleares tardan unos cinco días laborables y a Canarias, unos diez. De momento no enviamos fuera de España.

## ¿Puedo devolver una compra online?

Sí, tienes 30 días desde que recibes el pedido para devolverlo sin dar explicaciones. El aparato tiene que estar sin usar y en su caja. Te devolvemos el dinero en un máximo de 14 días.

## ¿Qué piezas van al lavavajillas?

Solo el filtro antical de malla se puede lavar en el lavavajillas. El cuerpo del hervidor y la base nunca se mojan por fuera ni se sumergen.

## ¿El hervidor se apaga solo?

Sí. Todos los modelos se apagan solos al terminar de calentar, cuando se levantan de la base y cuando detectan que no tienen agua.
"""

RECAMBIOS = """# Catálogo de recambios

Precios con IVA incluido. Los pedidos de más de 30 euros no pagan gastos de envío; por debajo de esa cantidad, el envío cuesta 3,95 euros.

## Recambios del K1

| Referencia | Pieza | Precio |
| --- | --- | --- |
| FA-10 | Filtro antical de malla | 6,50 euros |
| BC-10 | Base de conexión | 19,90 euros |
| TP-10 | Tapa con bisagra | 9,00 euros |

## Recambios del K2

| Referencia | Pieza | Precio |
| --- | --- | --- |
| FA-20 | Filtro antical de malla | 7,50 euros |
| BC-20 | Base de conexión | 24,90 euros |
| TP-20 | Tapa con bisagra | 11,00 euros |
| SL-20 | Selector de temperatura del asa | 16,00 euros |

## Recambios del K3 Pro

| Referencia | Pieza | Precio |
| --- | --- | --- |
| FA-30 | Filtro antical de malla | 8,50 euros |
| BC-30 | Base de conexión con pantalla | 34,90 euros |
| TP-30 | Tapa de doble pared | 14,00 euros |
| MB-30 | Módulo Bluetooth | 22,00 euros |
"""

ACTA_MARZO = """Acta del comité de dirección
Fecha: 17 de marzo de 2026
Asistentes: Inés Robledo, Tomás Ezquerro, Clara Ibarra, Rubén Lázaro, Alba Quintana

1. Proveedor de nube. Se decide trasladar los servidores de correo y de archivos a Nubeca, un proveedor nacional, antes de septiembre. Tomás Ezquerro coordinará la migración con Redes Arnela.
2. Presupuesto de formación. Recursos Humanos propone 42.000 euros para la formación de 2026. Queda pendiente de aprobar hasta conocer el cierre del primer trimestre.
3. Hervidor de vidrio. El lanzamiento se retrasa al segundo trimestre de 2027 por un problema de proveedor con el cristal templado.
4. Aviso de descalcificación. Se aprueba añadir el aviso en todos los modelos fabricados desde junio.
5. Próxima reunión: 16 de junio de 2026.
"""

ACTA_JUNIO = """Acta del comité de dirección
Fecha: 16 de junio de 2026
Asistentes: Inés Robledo, Tomás Ezquerro, Clara Ibarra, Rubén Lázaro, Alba Quintana

1. Proveedor de nube. La migración a Nubeca está completada al 60 %. La nueva fecha de cierre es el 30 de septiembre de 2026.
2. Presupuesto de formación. Se aprueba un presupuesto de formación de 38.000 euros para 2026, por debajo de lo propuesto en marzo.
3. Calidad. Alba Quintana asume la dirección de calidad tras la jubilación de su predecesor.
4. Italia. Se firma un acuerdo con un distribuidor de Milán para empezar a vender en Italia en octubre.
5. Próxima reunión: 15 de septiembre de 2026.
"""

TEXT_FILES_V2: dict[str, str] = {
    "guia_onboarding.md": ONBOARDING,
    "faq_clientes.md": FAQ,
    "catalogo_recambios.md": RECAMBIOS,
    "acta_comite_2026_03.txt": ACTA_MARZO,
    "acta_comite_2026_06.txt": ACTA_JUNIO,
}
