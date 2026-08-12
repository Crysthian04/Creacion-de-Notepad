"""`INICIO`: cover sheet and console.

Phase 9 turns this into the real console -- role selector, stage traffic lights
and the command buttons. Until then it carries the identification of the
workbook and states plainly which sheets already exist, so a half-built template
is never mistaken for a finished one.
"""

from __future__ import annotations

from openpyxl.worksheet.worksheet import Worksheet

from src.common import styles
from src.common.layout import SheetLayout
from src.sheets.base import VISIBLE, BuildContext, SheetSpec

SPEC = SheetSpec(key="inicio", title="INICIO", visibility=VISIBLE, role="LECTOR")

_NOTE = (
    "Este libro se compila desde el repositorio; no se edita a mano su estructura. "
    "Los botones de la consola requieren Excel de escritorio con macros habilitadas."
)


class InicioSheetBuilder:
    """Builds the cover sheet."""

    spec = SPEC

    def build(self, worksheet: Worksheet, context: BuildContext) -> None:
        layout = SheetLayout(worksheet, first_column=2)
        layout.title(
            context.label("app.titulo"),
            context.label("app.subtitulo"),
        )

        layout.section("Identificación del libro", width=3)
        layout.key_values(
            [
                ("Versión de la plantilla", context.config.version, ""),
                ("Adaptador CMMS activo", "=PARAM_ADAPTADOR_ACTIVO", "Se configura en Parametros."),
                ("Tipo de plan SAP", "=PARAM_SAP_TIPO_PLAN", "Estrategia o ciclo individual."),
            ],
            value_style=styles.READONLY,
        )

        layout.section("Consola", width=3)
        layout.note(_NOTE)
        layout.blank()
        layout.note(
            "Hojas disponibles en esta versión: "
            + ", ".join(spec.title for spec in _built_specs(context))
        )

        worksheet.column_dimensions["A"].width = 3


def _built_specs(context: BuildContext) -> list[SheetSpec]:
    """Specs of the sheets registered in this build, for the cover listing."""
    from src.sheets import registry

    return [builder.spec for builder in registry()]
