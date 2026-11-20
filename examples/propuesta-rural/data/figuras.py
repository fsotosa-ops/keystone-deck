#!/usr/bin/env python3
"""Escribe evidence.json para «Cosecha Cerca» (iniciativa ficticia).

Tier V: cifras publicadas por fuentes públicas (se citan en la lámina).
Tier D: metas del piloto que el equipo decide (la lámina dice «meta»).
Uso: python3 data/figuras.py
"""
import json
from pathlib import Path

REFS = {
    "odepa-caf2021": "ODEPA (2024). Censo Agropecuario y Forestal 2021: distribución de las unidades productivas, con datos INE. odepa.gob.cl",
    "subtel-2025": "SUBTEL (nov. 2025). XII Encuesta de acceso, usos y usuarios de Internet. subtel.gob.cl",
    "indap-2015": "INDAP–USACH (2015). Mercados públicos de alimentos y la AFC. Serie Estudios N° 5. indap.gob.cl",
    "odepa-cc-2015": "ODEPA–Rimisp (2015). Agricultura familiar y circuitos cortos en Chile: situación actual, restricciones y potencialidades, cuadro 7, p. 51 (catastro INDAP 2014 y Censo Agropecuario 2007). odepa.gob.cl",
    "latercera-2024": "La Tercera (27-02-2024), con datos de INDAP y JUNAEB: récord de ventas de la AFC al PAE en 2023. latercera.com",
}


def num_cl(x, dec=0):
    """Formato chileno: punto de miles, coma decimal."""
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# --- Cifras públicas (V) -------------------------------------------------
upa_2021 = 175_556                 # UPA totales, CAF 2021
barreras = [                        # INDAP 2015, resumen ejecutivo
    "desconocimiento del sistema de compras públicas", "falta de información de mercado",
    "deficiencias en la gestión comercial y financiera", "informalidad comercial",
    "desconocimiento de los requerimientos de los clientes", "deficiente planificación de producción y entregas",
    "bajos volúmenes de producción", "limitado uso de tecnologías de información",
    "dificultad para cumplir exigencias de inocuidad y calidad",
]
demanda_publica_usd_mm = 450        # US$ millones/año, alimentos frescos
rural_internet = 95.1               # % hogares rurales con acceso a Internet
rural_smartphone = 99.2             # % hogares rurales con Internet que usan teléfono móvil o smartphone
afc_pae_2023 = 4_126_300_744        # CLP, ventas brutas de la AFC al PAE en 2023
afc_pae_crec = 42                   # % de alza vs 2022
afc_pae_kg = 6_539_771              # kg de hortalizas, frutas y miel
pae_local, pae_afc = 5, 2.5
# ODEPA–Rimisp 2015, cuadro 7: productores en circuitos cortos (catastro INDAP 2014)
# sobre explotaciones de la agricultura familiar (Censo 2007; máx. un trabajador no familiar).
# Circuito corto = venta directa o con un solo intermediario, así que «venden directo» es aún menos.
cc_productores, afc_explotaciones = 13_706, 239_469
afc_cc_pct = 100 * cc_productores / afc_explotaciones   # 5,72 → «6 de cada 100»         # % de compras locales en bases PAE, y piso AFC

# --- Metas del piloto (D) ------------------------------------------------
piloto = {"productores": 25, "restoranes": 6, "colegios": 4, "meses": 6, "radio_km": 30,
          "comision": 6, "meta_directa": 30}

F = {
    "upa-2021": dict(value=upa_2021, display=num_cl(upa_2021), tier="V", source="odepa-caf2021", asOf="2021"),
    "barreras-afc": dict(value=len(barreras), display=f"{len(barreras)} barreras", tier="V", source="indap-2015", asOf="2015",
                         note="; ".join(barreras)),
    "demanda-publica": dict(value=demanda_publica_usd_mm, display=f"US$ {demanda_publica_usd_mm} millones", tier="V",
                            source="indap-2015", asOf="2015"),
    "rural-internet": dict(value=rural_internet, display=num_cl(rural_internet, 1) + "%", tier="V", source="subtel-2025", asOf="2025"),
    "rural-smartphone": dict(value=rural_smartphone, display=num_cl(rural_smartphone, 1) + "%", tier="V", source="subtel-2025", asOf="2025"),
    "afc-pae-2023": dict(value=afc_pae_2023, display=f"${num_cl(afc_pae_2023 / 1e6)} millones", tier="V", source="latercera-2024", asOf="2023"),
    "pae-local": dict(value=pae_local, display=f"{pae_local}%", tier="V", source="latercera-2024", asOf="2024"),
    "afc-cc": dict(value=round(afc_cc_pct, 2), display=str(round(afc_cc_pct)), tier="V", source="odepa-cc-2015", asOf="2014",
                   note=f"{cc_productores} productores en circuitos cortos / {afc_explotaciones} explotaciones AFC"),
    "piloto-productores": dict(value=piloto["productores"], display=str(piloto["productores"]), tier="D"),
    "piloto-restoranes": dict(value=piloto["restoranes"], display=str(piloto["restoranes"]), tier="D"),
    "piloto-colegios": dict(value=piloto["colegios"], display=str(piloto["colegios"]), tier="D"),
    "piloto-compradores": dict(value=piloto["restoranes"] + piloto["colegios"],
                               display=str(piloto["restoranes"] + piloto["colegios"]), tier="D"),
    "piloto-meses": dict(value=piloto["meses"], display=f"{piloto['meses']} meses", tier="D"),
    "piloto-radio": dict(value=piloto["radio_km"], display=f"{piloto['radio_km']} km", tier="D"),
    "comision": dict(value=piloto["comision"], display=f"{piloto['comision']}%", tier="D"),
    "meta-directa": dict(value=piloto["meta_directa"], display=f"{piloto['meta_directa']}%", tier="D"),
}

out = Path(__file__).resolve().parent.parent / "evidence.json"
out.write_text(json.dumps({"figures": F, "refs": {k: {"text": v} for k, v in REFS.items()}},
                          indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"wrote {out} ({len(F)} figures, {len(REFS)} refs)")
