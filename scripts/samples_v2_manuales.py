"""Corpus v2: tres manuales casi iguales (Termia K1, K2 y K3 Pro).

Trampa a propósito: las páginas 2, 3 y 6 no nombran el modelo en el cuerpo, y la
cabecera con el nombre se quita al limpiar los bordes repetidos. Solo el nombre del
archivo dice de qué hervidor es cada una de esas páginas.
"""

from sample_content import PdfSpec, _p

MODELOS: dict[str, dict[str, str]] = {
    "k1": {
        "nombre": "Termia K1",
        "capacidad": "1,0",
        "potencia": "1.800",
        "tiempo_hervir": "cuatro",
        "extra_p1": "Es el modelo más compacto de la gama y está pensado para cocinas pequeñas y para una o dos personas.",
        "cable": "75",
        "min_ml": "250",
        "color_piloto": "rojo",
        "temperaturas": "Este modelo solo tiene la función de hervir: el aparato se apaga solo cuando el agua llega a ebullición y no permite elegir otra temperatura.",
        "espera": "cinco",
        "descal_usos": "60",
        "descal_mezcla": "medio litro de agua con dos cucharadas de ácido cítrico",
        "descal_min": "20",
        "e1": "E1: el depósito está vacío o por debajo de la marca MIN. Añade agua y vuelve a encender.",
        "e2": "E2: sobrecalentamiento de la resistencia. Desenchufa el aparato y deja que se enfríe al menos 15 minutos.",
        "e3": "E3: el hervidor no está bien colocado sobre la base. Levántalo y vuelve a apoyarlo hasta oír un clic.",
        "garantia": "dos años",
        "extra_garantia": "La base de conexión del K1 tiene una garantía separada de un año, porque se vende también como recambio independiente.",
        "soporte": "seis",
        "telefono": "900 101 201",
        "horario": "9:00 a 14:00",
        "reparacion": "Las reparaciones se hacen en tienda: lleva el aparato con el ticket al punto de venta y te lo devolveremos reparado en un plazo de diez días laborables.",
    },
    "k2": {
        "nombre": "Termia K2",
        "capacidad": "1,7",
        "potencia": "2.000",
        "tiempo_hervir": "cinco",
        "extra_p1": "Es el modelo familiar de la gama y el más vendido, con selector de temperatura en el asa.",
        "cable": "90",
        "min_ml": "400",
        "color_piloto": "blanco",
        "temperaturas": "Puedes elegir entre cuatro temperaturas con el selector del asa: 70, 80, 90 y 100 grados. Para el té verde se recomiendan 80 grados y para el café de filtro, 90 grados.",
        "espera": "diez",
        "descal_usos": "90",
        "descal_mezcla": "un litro de agua con un vaso de vinagre blanco",
        "descal_min": "30",
        "e1": "E1: el depósito está vacío o por debajo de la marca MIN. Añade agua y vuelve a encender.",
        "e2": "E2: el sensor de temperatura no responde. El aparato no puede calentar con seguridad y tiene que revisarlo el servicio técnico.",
        "e3": "E3: la tapa está abierta o mal cerrada. Ciérrala presionando hasta que encaje y pulsa de nuevo el interruptor.",
        "garantia": "tres años",
        "extra_garantia": "En el K2 la garantía cubre también la base de conexión durante el mismo periodo.",
        "soporte": "doce",
        "telefono": "900 101 202",
        "horario": "9:00 a 18:00",
        "reparacion": "Si el aparato necesita reparación, envíalo por mensajería con el bono de envío gratuito que te mandaremos por correo electrónico al abrir la incidencia.",
    },
    "k3": {
        "nombre": "Termia K3 Pro",
        "capacidad": "1,5",
        "potencia": "2.200",
        "tiempo_hervir": "tres",
        "extra_p1": "Es el modelo de gama alta: tiene pantalla digital, cuerpo de acero con doble pared y se controla también desde la aplicación Termia por Bluetooth.",
        "cable": "100",
        "min_ml": "300",
        "color_piloto": "azul",
        "temperaturas": "Puedes fijar cualquier temperatura entre 40 y 100 grados, en pasos de 5 grados, con los botones de la pantalla o desde la aplicación. La función de mantener calor conserva el agua a la temperatura elegida durante 60 minutos como máximo.",
        "espera": "tres",
        "descal_usos": "120",
        "descal_mezcla": "el sobre de descalcificador Termia disuelto en un litro de agua",
        "descal_min": "15",
        "e1": "E1: el depósito está vacío o por debajo de la marca MIN. Añade agua y vuelve a encender.",
        "e2": "E2: se ha perdido la conexión Bluetooth con la aplicación. El hervidor sigue funcionando con los botones; para recuperar el control remoto, desactiva y activa el Bluetooth del móvil.",
        "e3": "E3: sobrecalentamiento de la resistencia. Desenchufa el aparato y deja que se enfríe al menos 20 minutos.",
        "garantia": "cinco años",
        "extra_garantia": "Si registras el K3 Pro en la aplicación Termia en los 30 días siguientes a la compra, la garantía se amplía un año más.",
        "soporte": "veinticuatro",
        "telefono": "900 101 203",
        "horario": "8:00 a 20:00, también los sábados por la mañana",
        "reparacion": "Durante la garantía recogemos el aparato en tu domicilio en un plazo de 48 horas y te prestamos otro hervidor mientras dura la reparación.",
    },
}


def manual(m: dict[str, str], filename: str) -> PdfSpec:
    """Manual de seis páginas a partir de los datos de un modelo."""
    return PdfSpec(
        filename=filename,
        header=f"{m['nombre']} · Manual de usuario",
        footer="Página {page} de {total}",
        pages=[
            _p(
                f"Gracias por elegir el hervidor {m['nombre']}. Este manual explica cómo usarlo de forma segura y cómo cuidarlo para que dure muchos años. Léelo entero antes del primer uso y guárdalo junto al ticket de compra.",
                f"El {m['nombre']} tiene una capacidad máxima de {m['capacidad']} litros y una potencia de {m['potencia']} vatios. Con el depósito lleno hierve el agua en unos {m['tiempo_hervir']} minutos. {m['extra_p1']}",
                f"Contenido de la caja: el hervidor, la base de conexión con un cable de {m['cable']} centímetros, un filtro antical de malla y este manual. Si falta alguna pieza, ponte en contacto con el servicio técnico antes de usar el aparato.",
            ),
            _p(
                "Uso diario. Llena el depósito por la tapa sin superar la marca MAX ni quedarte por debajo de la marca MIN, que equivale a "
                f"{m['min_ml']} mililitros. Coloca el hervidor sobre la base y pulsa el interruptor: el piloto se encenderá en color {m['color_piloto']} mientras calienta.",
                m["temperaturas"],
                f"No pongas en marcha el aparato vacío. Si se queda sin agua, el sistema de protección lo apaga y hay que esperar {m['espera']} minutos antes de volver a encenderlo. No muevas el hervidor de la base mientras está calentando.",
            ),
            _p(
                "Limpieza y cal. Limpia el exterior con un paño húmedo y sin productos abrasivos. No sumerjas nunca el cuerpo del aparato ni la base en agua y no lo metas en el lavavajillas.",
                f"Descalcifica el depósito cada {m['descal_usos']} usos, o antes si ves manchas blancas en el fondo. Usa {m['descal_mezcla']} y deja actuar la mezcla {m['descal_min']} minutos sin hervir; después aclara dos veces con agua limpia.",
                "El filtro antical de malla se saca tirando hacia arriba y se lava bajo el grifo una vez al mes. Si está roto, pide el recambio en la tienda online: un filtro dañado deja pasar partículas de cal a la taza.",
            ),
            _p(
                f"Códigos de error del {m['nombre']}. Cuando el aparato detecta un problema, el indicador muestra un código. Apaga el hervidor y sigue las indicaciones de esta página.",
                m["e1"],
                m["e2"],
                m["e3"],
                "Si el código vuelve a aparecer después de seguir las indicaciones, no abras el aparato: dentro hay piezas con tensión. Contacta con el servicio técnico.",
            ),
            _p(
                f"Garantía. El {m['nombre']} tiene una garantía de {m['garantia']} desde la fecha de compra que figura en el ticket o en la factura.",
                "La garantía cubre los defectos de fabricación y de materiales. No cubre la cal acumulada por no descalcificar, los golpes, las caídas ni el uso con líquidos distintos del agua.",
                m["extra_garantia"],
            ),
            _p(
                f"Servicio técnico. El soporte telefónico es gratuito durante los {m['soporte']} meses siguientes a la compra en el teléfono {m['telefono']}. Atendemos de lunes a viernes de {m['horario']}.",
                m["reparacion"],
                "Al final de su vida útil, no tires el hervidor a la basura: llévalo a un punto limpio o devuélvelo en la tienda cuando compres uno nuevo.",
            ),
        ],
    )


MANUALES: list[PdfSpec] = [
    manual(MODELOS["k1"], "manual_hervidor_k1.pdf"),
    manual(MODELOS["k2"], "manual_hervidor_k2.pdf"),
    manual(MODELOS["k3"], "manual_hervidor_k3.pdf"),
]
