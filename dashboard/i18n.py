"""Dashboard internationalisation — English plus the country's own language.

Every user-facing string in ``dashboard/`` is looked up here via ``t(key)``.
The active language lives in ``st.session_state["lang"]`` (mirrored to the
``?lang=`` query param so links are shareable) and defaults to the country's
``default_lang`` from ``config.COUNTRIES`` — Spanish for El Salvador, French
for Haiti. The sidebar toggle (``language_toggle``) switches between that
language and English.

Outside a Streamlit runtime (pytest) the language is English unless a test
calls ``set_offline_lang``; that keeps the pure-logic tests' English
assertions meaningful.

Adding a string: add one entry to ``STRINGS`` with all three languages. The
``tests/test_i18n.py`` suite fails if a language or a ``{placeholder}`` is
missing from any entry.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from .. import config

LANGS: dict[str, str] = {"en": "English", "es": "Español", "fr": "Français"}
FALLBACK_LANG = "en"

# Language used when there is no Streamlit session (tests, scripts).
_offline_lang = FALLBACK_LANG


# ---------------------------------------------------------------------------
# Language state
# ---------------------------------------------------------------------------


def _runtime_exists() -> bool:
    try:
        from streamlit import runtime

        return bool(runtime.exists())
    except Exception:
        return False


def country_default_lang() -> str:
    lang = config.CC.get("default_lang", FALLBACK_LANG)
    return lang if lang in LANGS else FALLBACK_LANG


def country_langs() -> list[str]:
    """Languages offered by the toggle: the country's own language first,
    then English."""
    native = country_default_lang()
    return [native, "en"] if native != "en" else ["en"]


def current_lang() -> str:
    if _runtime_exists():
        return st.session_state.get("lang") or country_default_lang()
    return _offline_lang


def set_offline_lang(lang: str) -> None:
    """Force the language when no Streamlit session exists (tests)."""
    global _offline_lang
    _offline_lang = lang if lang in LANGS else FALLBACK_LANG


def init() -> str:
    """Resolve the session language once per session: ``?lang=`` query param
    if valid for this country, else the country default. Call before the
    first translated string (i.e. before ``st.set_page_config``)."""
    if "lang" not in st.session_state:
        try:
            qp = st.query_params.get("lang")
        except Exception:
            qp = None
        st.session_state["lang"] = (
            qp if qp in country_langs() else country_default_lang()
        )
    return st.session_state["lang"]


def _on_toggle_change() -> None:
    new = st.session_state.get("lang_choice")
    if new is None:
        # Clicking the already-selected pill deselects a segmented control;
        # treat that as "keep the current language".
        st.session_state["lang_choice"] = st.session_state["lang"]
        return
    st.session_state["lang"] = new
    try:
        st.query_params["lang"] = new
    except Exception:
        pass


_TOGGLE_CSS = """
<style>
/* Compact language pill toggle — "direct" scheme: the selected option gets a
   light tint, a bold label and a darker border (not an inverted dark fill). */
[data-testid="stSidebar"] [data-testid="stSegmentedControl"] {
  display: flex; justify-content: flex-end;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-segmented_control"],
[data-testid="stSidebar"] [data-testid="stBaseButton-segmented_controlActive"] {
  font-size: 0.78rem; line-height: 1; min-height: 1.75rem;
  padding: 0.15rem 0.6rem; letter-spacing: 0.03em;
  border: 1px solid rgba(26, 74, 110, 0.35); color: #4a5a68;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-segmented_controlActive"] {
  font-weight: 700; color: #1a4a6e;
  background-color: rgba(26, 74, 110, 0.10);
  border-color: #1a4a6e;
}
</style>
"""


def language_toggle(container) -> str:
    """Render the ES|EN / FR|EN pill toggle into ``container`` and return the
    active language. Drives ``st.session_state["lang"]`` via its callback."""
    opts = country_langs()
    if st.session_state.get("lang_choice") not in opts:
        st.session_state["lang_choice"] = st.session_state["lang"]
    container.markdown(_TOGGLE_CSS, unsafe_allow_html=True)
    container.segmented_control(
        t("language"),
        opts,
        format_func=lambda k: k.upper(),
        key="lang_choice",
        on_change=_on_toggle_change,
        label_visibility="collapsed",
    )
    return st.session_state["lang"]


# ---------------------------------------------------------------------------
# Lookup
# ---------------------------------------------------------------------------


def t(key: str, **fmt) -> str:
    """Translate ``key`` into the active language, formatting ``{placeholders}``
    with ``fmt``. Falls back to English for a language that lacks the key."""
    entry = STRINGS[key]
    s = entry.get(current_lang()) or entry[FALLBACK_LANG]
    return s.format(**fmt) if fmt else s


def dep_display(departamento: str, all_sentinel: str) -> str:
    """Display label for a departamento value — translates the 'All (country
    mean)' sentinel, leaves real department names alone."""
    return t("all_country_mean") if departamento == all_sentinel else departamento


def phase_label(phase: str) -> str:
    return {
        "El Niño": t("phase_el_nino"),
        "La Niña": t("phase_la_nina"),
        "Neutral": t("phase_neutral"),
    }.get(phase, phase)


def crop_caption() -> str:
    return t(f"crop_caption_{config.COUNTRY}")


def priority_label() -> str:
    return t(f"priority_label_{config.COUNTRY}")


# ---------------------------------------------------------------------------
# Dates
# ---------------------------------------------------------------------------

MONTHS: dict[str, list[str]] = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "es": ["ene", "feb", "mar", "abr", "may", "jun",
           "jul", "ago", "sep", "oct", "nov", "dic"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin",
           "juil.", "août", "sept.", "oct.", "nov.", "déc."],
}


def month_abbr(month: int) -> str:
    return MONTHS.get(current_lang(), MONTHS["en"])[month - 1]


def _ts(d) -> pd.Timestamp:
    return pd.Timestamp(d)


def fmt_mon_day(d) -> str:
    """'Jul 15' / '15 jul' / '15 juil.'"""
    ts = _ts(d)
    if current_lang() == "en":
        return f"{month_abbr(ts.month)} {ts.day:02d}"
    return f"{ts.day:02d} {month_abbr(ts.month)}"


def fmt_mon_year(d) -> str:
    """'Aug 2026' / 'ago 2026' / 'août 2026'"""
    ts = _ts(d)
    return f"{month_abbr(ts.month)} {ts.year}"


def fmt_day_mon_year(d) -> str:
    """'07 Sep 2026' / '07 sep 2026' / '07 sept. 2026'"""
    ts = _ts(d)
    return f"{ts.day:02d} {month_abbr(ts.month)} {ts.year}"


# ---------------------------------------------------------------------------
# Strings
# ---------------------------------------------------------------------------

STRINGS: dict[str, dict[str, str]] = {
    # ---- chrome ----
    "language": {"en": "Language", "es": "Idioma", "fr": "Langue"},
    "page_title": {
        "en": "{name} Drought Monitor",
        "es": "Monitor de sequía — {name}",
        "fr": "Moniteur de sécheresse — {name}",
    },
    "sidebar_title": {
        "en": "{code} Drought Monitor",
        "es": "Monitor de sequía {code}",
        "fr": "Moniteur de sécheresse {code}",
    },
    "crop_caption_el_salvador": {
        "en": "maize-season indicators",
        "es": "indicadores de la temporada de maíz",
        "fr": "indicateurs de la saison du maïs",
    },
    "crop_caption_haiti": {
        "en": "printemps/été drought indicators",
        "es": "indicadores de sequía printemps/été",
        "fr": "indicateurs de sécheresse printemps/été",
    },
    "priority_label_el_salvador": {
        "en": "Eastern Dry Corridor",
        "es": "Corredor Seco oriental",
        "fr": "Corridor sec oriental",
    },
    "priority_label_haiti": {
        "en": "Drought-vulnerable departments",
        "es": "Departamentos vulnerables a la sequía",
        "fr": "Départements vulnérables à la sécheresse",
    },
    "icon_attribution": {
        "en": "Icon: {link}",
        "es": "Ícono: {link}",
        "fr": "Icône : {link}",
    },
    "no_data_sidebar": {
        "en": "No data found. Run the ETL first:\n\n`python -m el_nino.etl.run_etl synth`",
        "es": "No se encontraron datos. Ejecute primero el ETL:\n\n`python -m el_nino.etl.run_etl synth`",
        "fr": "Aucune donnée trouvée. Lancez d'abord l'ETL :\n\n`python -m el_nino.etl.run_etl synth`",
    },
    "no_data_main": {
        "en": "No indicator data available yet. The ETL needs to populate `data/raw/`. See sidebar.",
        "es": "Aún no hay datos de indicadores. El ETL debe poblar `data/raw/`. Vea la barra lateral.",
        "fr": "Aucune donnée d'indicateur pour l'instant. L'ETL doit remplir `data/raw/`. Voir la barre latérale.",
    },
    # ---- sidebar controls ----
    "all_country_mean": {
        "en": "All (country mean)",
        "es": "Todos (promedio nacional)",
        "fr": "Tous (moyenne nationale)",
    },
    "dep_select_help": {
        "en": "Pick a {country} {dept}, or '{all}' for a nationwide average. "
              "You can also click any {dept} on the map. {priority} focus: {names}.",
        "es": "Elija un {dept} de {country}, o '{all}' para el promedio nacional. "
              "También puede hacer clic en cualquier {dept} en el mapa. Enfoque en {priority}: {names}.",
        "fr": "Choisissez un {dept} de {country}, ou « {all} » pour la moyenne nationale. "
              "Vous pouvez aussi cliquer sur un {dept} sur la carte. Priorité : {priority} ({names}).",
    },
    "indicator": {"en": "Indicator", "es": "Indicador", "fr": "Indicateur"},
    "indicator_help": {
        "en": "Pick which indicator to feature in Indicator Detail and Year Compare.",
        "es": "Elija el indicador que se mostrará en Detalle del indicador y Comparar años.",
        "fr": "Choisissez l'indicateur affiché dans Détail de l'indicateur et Comparer les années.",
    },
    "ind_chirps": {"en": "Rainfall (SPI-3)", "es": "Lluvia (SPI-3)", "fr": "Pluie (SPI-3)"},
    "ind_smap": {
        "en": "Soil moisture (root-zone)",
        "es": "Humedad del suelo (zona radicular)",
        "fr": "Humidité du sol (zone racinaire)",
    },
    "ind_wapor": {
        "en": "Evapotranspiration (WAPOR ETa)",
        "es": "Evapotranspiración (ETa WAPOR)",
        "fr": "Évapotranspiration (ETa WAPOR)",
    },
    "ind_imerg": {
        "en": "Daily rainfall (event scale)",
        "es": "Lluvia diaria (escala de eventos)",
        "fr": "Pluie journalière (échelle des événements)",
    },
    "ind_chirps_help": {
        "en": "**SPI-3** (Standardized Precipitation Index, 3-month) — how unusual the "
              "last 3 months of rainfall have been compared to 1981–present at this "
              "location and time of year. **0 = typical**, **−1 = moderate drought**, "
              "**−1.5 = severe drought**. Source: CHIRPS v3. "
              "**15-day forecast** is from NOAA GFS 0.25° (raw, not bias-corrected to "
              "CHIRPS — GFS tends to over-predict in the tropics).",
        "es": "**SPI-3** (Índice de Precipitación Estandarizado, 3 meses) — qué tan inusual "
              "ha sido la lluvia de los últimos 3 meses comparada con 1981–presente en este "
              "lugar y época del año. **0 = típico**, **−1 = sequía moderada**, "
              "**−1.5 = sequía severa**. Fuente: CHIRPS v3. "
              "El **pronóstico a 15 días** proviene de NOAA GFS 0.25° (sin corrección de "
              "sesgo respecto a CHIRPS — GFS tiende a sobreestimar en los trópicos).",
        "fr": "**SPI-3** (indice de précipitations standardisé, 3 mois) — à quel point la "
              "pluie des 3 derniers mois est inhabituelle par rapport à 1981–aujourd'hui à "
              "cet endroit et à cette période de l'année. **0 = typique**, **−1 = sécheresse "
              "modérée**, **−1,5 = sécheresse sévère**. Source : CHIRPS v3. "
              "La **prévision à 15 jours** provient de NOAA GFS 0,25° (brute, sans correction "
              "de biais par rapport à CHIRPS — GFS tend à surestimer sous les tropiques).",
    },
    "ind_smap_help": {
        "en": "**Root-zone soil moisture (0–100 cm)** — water available to maize roots. "
              "Even when surface looks moist, what kills yield at silking is depletion "
              "of the deeper store, which this captures. Source: NASA SMAP L4.",
        "es": "**Humedad del suelo en la zona radicular (0–100 cm)** — agua disponible para "
              "las raíces del maíz. Aunque la superficie parezca húmeda, lo que reduce el "
              "rendimiento en la floración es el agotamiento de la reserva profunda, que "
              "este indicador captura. Fuente: NASA SMAP L4.",
        "fr": "**Humidité du sol en zone racinaire (0–100 cm)** — eau disponible pour les "
              "racines du maïs. Même si la surface paraît humide, c'est l'épuisement de la "
              "réserve profonde qui fait chuter le rendement à la floraison, et c'est ce "
              "que mesure cet indicateur. Source : NASA SMAP L4.",
    },
    "ind_wapor_help": {
        "en": "**Actual evapotranspiration (ETa)** — water actually leaving the soil "
              "and crop canopy. Low ETa during the growing season confirms crop stress. "
              "Lags rainfall/soil moisture by ~10 days. Source: FAO WAPOR v3.",
        "es": "**Evapotranspiración real (ETa)** — agua que realmente sale del suelo y del "
              "dosel del cultivo. Una ETa baja durante la temporada de crecimiento confirma "
              "estrés en el cultivo. Se retrasa ~10 días respecto a la lluvia/humedad del "
              "suelo. Fuente: FAO WAPOR v3.",
        "fr": "**Évapotranspiration réelle (ETa)** — eau qui quitte effectivement le sol et "
              "le couvert végétal. Une ETa faible pendant la saison de croissance confirme "
              "le stress des cultures. Décalage d'environ 10 jours par rapport à la "
              "pluie/l'humidité du sol. Source : FAO WAPOR v3.",
    },
    "ind_imerg_help": {
        "en": "**Daily rainfall** at finer temporal/spatial resolution than CHIRPS. "
              "Use for verifying individual rain events. Source: NASA IMERG-Late V07.",
        "es": "**Lluvia diaria** con mayor resolución temporal/espacial que CHIRPS. "
              "Útil para verificar eventos de lluvia individuales. Fuente: NASA IMERG-Late V07.",
        "fr": "**Pluie journalière** à résolution temporelle/spatiale plus fine que CHIRPS. "
              "Utile pour vérifier des épisodes pluvieux individuels. Source : NASA IMERG-Late V07.",
    },
    "baseline_fmt": {
        "en": "{start}–present",
        "es": "{start}–presente",
        "fr": "{start}–aujourd'hui",
    },
    "yaxis_spi_3": {
        "en": "SPI-3 (standardized rainfall, last 3 months)",
        "es": "SPI-3 (lluvia estandarizada, últimos 3 meses)",
        "fr": "SPI-3 (pluie standardisée, 3 derniers mois)",
    },
    "yaxis_spi_1": {
        "en": "SPI-1 (standardized rainfall, last month)",
        "es": "SPI-1 (lluvia estandarizada, último mes)",
        "fr": "SPI-1 (pluie standardisée, dernier mois)",
    },
    "yaxis_spi_6": {
        "en": "SPI-6 (standardized rainfall, last 6 months)",
        "es": "SPI-6 (lluvia estandarizada, últimos 6 meses)",
        "fr": "SPI-6 (pluie standardisée, 6 derniers mois)",
    },
    "yaxis_precip_pentad_mm": {
        "en": "Rainfall (mm per 5-day pentad)",
        "es": "Lluvia (mm por péntada de 5 días)",
        "fr": "Pluie (mm par pentade de 5 jours)",
    },
    "yaxis_rzsm_m3m3": {
        "en": "Root-zone soil moisture (m³/m³)",
        "es": "Humedad del suelo en zona radicular (m³/m³)",
        "fr": "Humidité du sol en zone racinaire (m³/m³)",
    },
    "yaxis_eta_mm": {
        "en": "Evapotranspiration (mm per dekad)",
        "es": "Evapotranspiración (mm por década)",
        "fr": "Évapotranspiration (mm par décade)",
    },
    "yaxis_imerg_precip_mm": {
        "en": "Rainfall (mm per day)",
        "es": "Lluvia (mm por día)",
        "fr": "Pluie (mm par jour)",
    },
    "forecast_toggle": {
        "en": "Show 15-day forecast (where available)",
        "es": "Mostrar pronóstico a 15 días (donde esté disponible)",
        "fr": "Afficher la prévision à 15 jours (si disponible)",
    },
    "forecast_toggle_help": {
        "en": "Append the CHIRPS3-GEFS 15-day rainfall forecast as a dashed segment.",
        "es": "Agrega el pronóstico de lluvia a 15 días CHIRPS3-GEFS como un segmento discontinuo.",
        "fr": "Ajoute la prévision de pluie à 15 jours CHIRPS3-GEFS sous forme de segment en pointillé.",
    },
    "check_new_data_btn": {
        "en": "🔄 Check for new data",
        "es": "🔄 Buscar datos nuevos",
        "fr": "🔄 Vérifier les nouvelles données",
    },
    "check_new_data_help": {
        "en": "Queries Earth Engine for the latest data, pulls UCSB CHIRPS-Prelim "
              "to fill the recent gap, and refreshes the 15-day GFS rainfall "
              "forecast. Limited to once per 12 hours across all users.",
        "es": "Consulta Earth Engine por los datos más recientes, descarga UCSB CHIRPS-Prelim "
              "para llenar el vacío reciente y actualiza el pronóstico de lluvia GFS a 15 días. "
              "Limitado a una vez cada 12 horas para todos los usuarios.",
        "fr": "Interroge Earth Engine pour les données les plus récentes, récupère UCSB "
              "CHIRPS-Prelim pour combler le retard récent et actualise la prévision de pluie "
              "GFS à 15 jours. Limité à une fois par 12 heures pour tous les utilisateurs.",
    },
    "check_new_data_disabled_help": {
        "en": "Already refreshed {last}. Next refresh available {next}.",
        "es": "Ya se actualizó {last}. Próxima actualización disponible {next}.",
        "fr": "Déjà actualisé {last}. Prochaine actualisation possible {next}.",
    },
    "refresh_used_caption": {
        "en": "⏱️ Daily refresh used · next available {next}",
        "es": "⏱️ Actualización diaria usada · próxima disponible {next}",
        "fr": "⏱️ Actualisation quotidienne utilisée · prochaine {next}",
    },
    "checking_status": {
        "en": "Checking source assets…",
        "es": "Revisando las fuentes de datos…",
        "fr": "Vérification des sources de données…",
    },
    "found_new_data": {
        "en": "Found new data — fetched and merged.",
        "es": "Se encontraron datos nuevos — descargados y combinados.",
        "fr": "Nouvelles données trouvées — récupérées et fusionnées.",
    },
    "already_up_to_date": {
        "en": "Already up to date.",
        "es": "Ya está actualizado.",
        "fr": "Déjà à jour.",
    },
    "refresh_failed": {
        "en": "Failed: {err}",
        "es": "Error: {err}",
        "fr": "Échec : {err}",
    },
    "rel_in": {"en": "in {unit}", "es": "en {unit}", "fr": "dans {unit}"},
    "rel_ago": {"en": "{unit} ago", "es": "hace {unit}", "fr": "il y a {unit}"},
    # ---- freshness ----
    "data_refreshed_caption": {
        "en": "Data refreshed: **{refreshed}**  \nNext refresh: **{next}**",
        "es": "Datos actualizados: **{refreshed}**  \nPróxima actualización: **{next}**",
        "fr": "Données actualisées : **{refreshed}**  \nProchaine actualisation : **{next}**",
    },
    "freshness_not_computed": {
        "en": "_Freshness summary not yet computed. Run "
              "`python -m el_nino.etl.run_etl finalize` once backfills complete._",
        "es": "_Resumen de actualidad aún no calculado. Ejecute "
              "`python -m el_nino.etl.run_etl finalize` cuando terminen las cargas históricas._",
        "fr": "_Résumé de fraîcheur pas encore calculé. Lancez "
              "`python -m el_nino.etl.run_etl finalize` une fois les chargements terminés._",
    },
    "badge_no_obs": {
        "en": "{emoji} No observations yet",
        "es": "{emoji} Aún sin observaciones",
        "fr": "{emoji} Pas encore d'observations",
    },
    "badge_last_obs": {
        "en": "{emoji} Last observation: {date} ({lag}{cadence})",
        "es": "{emoji} Última observación: {date} ({lag}{cadence})",
        "fr": "{emoji} Dernière observation : {date} ({lag}{cadence})",
    },
    "lag_today": {"en": "today", "es": "hoy", "fr": "aujourd'hui"},
    "lag_one_day_ago": {"en": "1 day ago", "es": "hace 1 día", "fr": "il y a 1 jour"},
    "lag_days_ago": {"en": "{n} days ago", "es": "hace {n} días", "fr": "il y a {n} jours"},
    "cadence_note": {
        "en": ", refreshes every {days}d",
        "es": ", se actualiza cada {days} d",
        "fr": ", actualisé tous les {days} j",
    },
    "status_no_obs": {
        "en": "No observations yet",
        "es": "Aún sin observaciones",
        "fr": "Pas encore d'observations",
    },
    "status_based_today": {
        "en": "Based on today's observations",
        "es": "Según las observaciones de hoy",
        "fr": "D'après les observations d'aujourd'hui",
    },
    "status_based_yesterday": {
        "en": "Based on yesterday's observations",
        "es": "Según las observaciones de ayer",
        "fr": "D'après les observations d'hier",
    },
    "status_based_days": {
        "en": "Based on observations from {n} days ago",
        "es": "Según observaciones de hace {n} días",
        "fr": "D'après des observations d'il y a {n} jours",
    },
    # ---- tabs & overview ----
    "tab_overview": {"en": "Overview", "es": "Resumen", "fr": "Vue d'ensemble"},
    "tab_detail": {"en": "Indicator Detail", "es": "Detalle del indicador", "fr": "Détail de l'indicateur"},
    "tab_compare": {"en": "Year Compare", "es": "Comparar años", "fr": "Comparer les années"},
    "overview_header": {
        "en": "Overview — {dep}",
        "es": "Resumen — {dep}",
        "fr": "Vue d'ensemble — {dep}",
    },
    "overview_caption": {
        "en": "Each panel shows the current year against the historical climatology envelope for the past 12 months.",
        "es": "Cada panel muestra el año actual frente a la envolvente climatológica histórica de los últimos 12 meses.",
        "fr": "Chaque panneau montre l'année en cours par rapport à l'enveloppe climatologique historique des 12 derniers mois.",
    },
    "map_title": {
        "en": "**Current {indicator} status — all {depts}**",
        "es": "**Estado actual de {indicator} — todos los {depts}**",
        "fr": "**État actuel de {indicator} — tous les {depts}**",
    },
    "map_click_hint": {
        "en": "💡 Click any {dept} to focus the dashboard on it.",
        "es": "💡 Haga clic en cualquier {dept} para enfocar el tablero en él.",
        "fr": "💡 Cliquez sur un {dept} pour y centrer le tableau de bord.",
    },
    "select_all_btn": {"en": "🌐 Select All", "es": "🌐 Ver todos", "fr": "🌐 Tout sélectionner"},
    "select_all_help": {
        "en": "Switch to the country-mean view across all {depts}.",
        "es": "Cambiar a la vista del promedio nacional de todos los {depts}.",
        "fr": "Passer à la vue moyenne nationale sur tous les {depts}.",
    },
    "map_unavailable": {
        "en": "Map unavailable — run `python -m el_nino.etl.aoi.fetch_aoi` to fetch the AOI polygons.",
        "es": "Mapa no disponible — ejecute `python -m el_nino.etl.aoi.fetch_aoi` para descargar los polígonos del AOI.",
        "fr": "Carte indisponible — lancez `python -m el_nino.etl.aoi.fetch_aoi` pour récupérer les polygones de la zone.",
    },
    "legend": {"en": "**Legend**", "es": "**Leyenda**", "fr": "**Légende**"},
    "map_status": {"en": "Status", "es": "Estado", "fr": "État"},
    "map_anomaly": {"en": "Anomaly (σ)", "es": "Anomalía (σ)", "fr": "Anomalie (σ)"},
    # ---- ENSO ----
    "enso_header": {
        "en": "El Niño / La Niña tracker & Comparison",
        "es": "Seguimiento y comparación de El Niño / La Niña",
        "fr": "Suivi et comparaison El Niño / La Niña",
    },
    "enso_btn_elnino": {
        "en": "📊 Notable El Niño years",
        "es": "📊 Años notables de El Niño",
        "fr": "📊 Années El Niño marquantes",
    },
    "enso_btn_lanina": {
        "en": "❄️ Notable La Niña years",
        "es": "❄️ Años notables de La Niña",
        "fr": "❄️ Années La Niña marquantes",
    },
    "clear": {"en": "Clear", "es": "Limpiar", "fr": "Effacer"},
    "years_overlay_label": {
        "en": "Years to overlay on the current year",
        "es": "Años a superponer sobre el año actual",
        "fr": "Années à superposer à l'année en cours",
    },
    "enso_caption_latest": {
        "en": "Latest ONI: **{oni} °C** ({phase}, {date}).",
        "es": "Último ONI: **{oni} °C** ({phase}, {date}).",
        "fr": "Dernier ONI : **{oni} °C** ({phase}, {date}).",
    },
    "enso_caption_weekly": {
        "en": " Freshest weekly Niño 3.4: **{val} °C** ({phase}, week of {date}).",
        "es": " Niño 3.4 semanal más reciente: **{val} °C** ({phase}, semana del {date}).",
        "fr": " Dernier Niño 3.4 hebdomadaire : **{val} °C** ({phase}, semaine du {date}).",
    },
    "enso_caption_note": {
        "en": " ONI is NOAA's 3-month Niño 3.4 SST anomaly; ±0.5 °C marks El Niño / "
              "La Niña. The weekly point (★) leads ONI by ~1 month.",
        "es": " El ONI es la anomalía trimestral de temperatura superficial del mar Niño 3.4 de la "
              "NOAA; ±0.5 °C marca El Niño / La Niña. El punto semanal (★) se adelanta ~1 mes al ONI.",
        "fr": " L'ONI est l'anomalie trimestrielle de température de surface Niño 3.4 de la NOAA ; "
              "±0,5 °C marque El Niño / La Niña. Le point hebdomadaire (★) précède l'ONI d'environ 1 mois.",
    },
    "phase_el_nino": {"en": "El Niño", "es": "El Niño", "fr": "El Niño"},
    "phase_la_nina": {"en": "La Niña", "es": "La Niña", "fr": "La Niña"},
    "phase_neutral": {"en": "Neutral", "es": "Neutral", "fr": "Neutre"},
    # ---- panels / detail ----
    "no_data": {"en": "No data.", "es": "Sin datos.", "fr": "Pas de données."},
    "detail_no_data": {
        "en": "No data for this indicator/{dept} combination.",
        "es": "Sin datos para esta combinación de indicador/{dept}.",
        "fr": "Pas de données pour cette combinaison indicateur/{dept}.",
    },
    "detail_header": {
        "en": "{indicator} — {dep}",
        "es": "{indicator} — {dep}",
        "fr": "{indicator} — {dep}",
    },
    "current_status": {"en": "Current status", "es": "Estado actual", "fr": "État actuel"},
    "tech_details": {
        "en": "Show technical details",
        "es": "Mostrar detalles técnicos",
        "fr": "Afficher les détails techniques",
    },
    "tech_z": {
        "en": "Latest anomaly z-score: {z}",
        "es": "Último z-score de anomalía: {z}",
        "fr": "Dernier z-score d'anomalie : {z}",
    },
    "tech_primary_col": {
        "en": "Primary column: `{col}`",
        "es": "Columna principal: `{col}`",
        "fr": "Colonne principale : `{col}`",
    },
    "tech_baseline": {
        "en": "Baseline period for {indicator}: {baseline} (per-DOY percentiles)",
        "es": "Período base para {indicator}: {baseline} (percentiles por día del año)",
        "fr": "Période de référence pour {indicator} : {baseline} (percentiles par jour de l'année)",
    },
    "clim_n_samples": {
        "en": ", median {n} samples per percentile fence",
        "es": ", mediana de {n} muestras por umbral de percentil",
        "fr": ", médiane de {n} échantillons par seuil de percentile",
    },
    "clim_caption_smoothed": {
        "en": "_Baseline: {baseline}. Percentile fences smoothed over ±{window}-day "
              "window{n_samples} — pools nearby days-of-year together so short records "
              "(esp. WAPOR's ~8 years) produce stable envelopes._",
        "es": "_Período base: {baseline}. Umbrales de percentil suavizados en una ventana de "
              "±{window} días{n_samples} — agrupa días del año cercanos para que registros "
              "cortos (esp. los ~8 años de WAPOR) produzcan envolventes estables._",
        "fr": "_Référence : {baseline}. Seuils de percentile lissés sur une fenêtre de "
              "±{window} jours{n_samples} — regroupe les jours de l'année voisins pour que "
              "les séries courtes (surtout les ~8 ans de WAPOR) donnent des enveloppes stables._",
    },
    "clim_caption_plain": {
        "en": "_Baseline: {baseline} (per-DOY only, no smoothing)._",
        "es": "_Período base: {baseline} (solo por día del año, sin suavizado)._",
        "fr": "_Référence : {baseline} (par jour de l'année uniquement, sans lissage)._",
    },
    # ---- year compare ----
    "compare_header": {
        "en": "Compare years — {indicator} in {dep}",
        "es": "Comparar años — {indicator} en {dep}",
        "fr": "Comparer les années — {indicator} à {dep}",
    },
    "compare_caption": {
        "en": "El Niño analogs (1982-83, 1997-98, 2015-16, 2023-24 — the strong / "
              "very-strong events) and La Niña analogs (1988-89, 1998-2001, 2007-08, "
              "2010-12, 2020-23) per NOAA ONI. "
              "Years outside an indicator's record (SMAP from 2015, WAPOR from 2018) "
              "are silently dropped.",
        "es": "Años análogos de El Niño (1982-83, 1997-98, 2015-16, 2023-24 — los eventos "
              "fuertes / muy fuertes) y de La Niña (1988-89, 1998-2001, 2007-08, 2010-12, "
              "2020-23) según el ONI de la NOAA. "
              "Los años fuera del registro de un indicador (SMAP desde 2015, WAPOR desde 2018) "
              "se omiten silenciosamente.",
        "fr": "Années analogues El Niño (1982-83, 1997-98, 2015-16, 2023-24 — les épisodes "
              "forts / très forts) et La Niña (1988-89, 1998-2001, 2007-08, 2010-12, 2020-23) "
              "selon l'ONI de la NOAA. "
              "Les années hors de la période d'un indicateur (SMAP depuis 2015, WAPOR depuis "
              "2018) sont ignorées silencieusement.",
    },
    # ---- charts ----
    "chart_outer": {
        "en": "Typical range (5th–95th pct)",
        "es": "Rango típico (percentiles 5–95)",
        "fr": "Plage typique (5e–95e pct)",
    },
    "chart_inner": {
        "en": "Most common range (25th–75th pct)",
        "es": "Rango más común (percentiles 25–75)",
        "fr": "Plage la plus courante (25e–75e pct)",
    },
    "chart_median": {
        "en": "Median (typical)",
        "es": "Mediana (típico)",
        "fr": "Médiane (typique)",
    },
    "chart_current_year": {"en": "Current year", "es": "Año actual", "fr": "Année en cours"},
    "chart_forecast": {
        "en": "Forecast (next 15 days)",
        "es": "Pronóstico (próximos 15 días)",
        "fr": "Prévision (15 prochains jours)",
    },
    "chart_today": {
        "en": "Today · {date}",
        "es": "Hoy · {date}",
        "fr": "Aujourd'hui · {date}",
    },
    "chart_awaiting": {
        "en": "Awaiting new data",
        "es": "En espera de datos nuevos",
        "fr": "En attente de nouvelles données",
    },
    "chart_enso_yaxis": {
        "en": "SST anomaly (°C) — ONI / Niño 3.4",
        "es": "Anomalía de TSM (°C) — ONI / Niño 3.4",
        "fr": "Anomalie de TSM (°C) — ONI / Niño 3.4",
    },
    "chart_elnino_thr": {
        "en": "El Niño ≥ +0.5 °C",
        "es": "El Niño ≥ +0.5 °C",
        "fr": "El Niño ≥ +0,5 °C",
    },
    "chart_lanina_thr": {
        "en": "La Niña ≤ −0.5 °C",
        "es": "La Niña ≤ −0.5 °C",
        "fr": "La Niña ≤ −0,5 °C",
    },
    "chart_weekly_nino34": {
        "en": "Latest weekly Niño 3.4",
        "es": "Último Niño 3.4 semanal",
        "fr": "Dernier Niño 3.4 hebdomadaire",
    },
    "chart_weekly_hover": {
        "en": "Weekly Niño 3.4 · {date}: {val} °C",
        "es": "Niño 3.4 semanal · {date}: {val} °C",
        "fr": "Niño 3.4 hebdomadaire · {date} : {val} °C",
    },
    # ---- drought categories (USDM tiers) ----
    "cat_pending_label": {"en": "Computing…", "es": "Calculando…", "fr": "Calcul en cours…"},
    "cat_pending_desc": {
        "en": "Not enough data yet to classify. The historical baseline or recent observations are still being computed.",
        "es": "Aún no hay datos suficientes para clasificar. La línea base histórica o las observaciones recientes todavía se están calculando.",
        "fr": "Pas encore assez de données pour classer. La référence historique ou les observations récentes sont encore en cours de calcul.",
    },
    "cat_normal_label": {"en": "Normal", "es": "Normal", "fr": "Normal"},
    "cat_normal_desc": {
        "en": "Conditions are within the typical range for this time of year.",
        "es": "Las condiciones están dentro del rango típico para esta época del año.",
        "fr": "Les conditions sont dans la plage typique pour cette période de l'année.",
    },
    "cat_w1_label": {"en": "Wetter than usual", "es": "Más húmedo de lo habitual", "fr": "Plus humide que d'habitude"},
    "cat_w1_desc": {
        "en": "Wetter than typical for this time of year. Watch for delayed planting or fungal pressure.",
        "es": "Más húmedo de lo típico para esta época del año. Vigile retrasos en la siembra o presión de hongos.",
        "fr": "Plus humide que la normale pour cette période. Surveillez les retards de semis ou la pression fongique.",
    },
    "cat_w2_label": {"en": "Very wet", "es": "Muy húmedo", "fr": "Très humide"},
    "cat_w2_desc": {
        "en": "Substantially wetter than typical. Flood risk in low-lying fields; later-season planting may slip.",
        "es": "Sustancialmente más húmedo de lo típico. Riesgo de inundación en parcelas bajas; la siembra tardía puede retrasarse.",
        "fr": "Nettement plus humide que la normale. Risque d'inondation dans les parcelles basses ; les semis tardifs peuvent glisser.",
    },
    "cat_w3_label": {"en": "Extremely wet", "es": "Extremadamente húmedo", "fr": "Extrêmement humide"},
    "cat_w3_desc": {
        "en": "Extremely wet conditions for this time of year. Likely waterlogging, lost yield in affected zones.",
        "es": "Condiciones extremadamente húmedas para esta época del año. Probable anegamiento y pérdida de rendimiento en las zonas afectadas.",
        "fr": "Conditions extrêmement humides pour cette période. Engorgement probable et pertes de rendement dans les zones touchées.",
    },
    "cat_d0_label": {"en": "Abnormally Dry", "es": "Anormalmente seco", "fr": "Anormalement sec"},
    "cat_d0_desc": {
        "en": "Going into drought or recovering from drought. Watch closely.",
        "es": "Entrando en sequía o recuperándose de ella. Vigile de cerca.",
        "fr": "Entrée en sécheresse ou sortie de sécheresse. À surveiller de près.",
    },
    "cat_d1_label": {"en": "Moderate Drought", "es": "Sequía moderada", "fr": "Sécheresse modérée"},
    "cat_d1_desc": {
        "en": "Some damage to crops; streams and soil moisture below normal.",
        "es": "Algún daño a los cultivos; caudales y humedad del suelo por debajo de lo normal.",
        "fr": "Quelques dégâts aux cultures ; cours d'eau et humidité du sol sous la normale.",
    },
    "cat_d2_label": {"en": "Severe Drought", "es": "Sequía severa", "fr": "Sécheresse sévère"},
    "cat_d2_desc": {
        "en": "Crop losses likely; water shortages common.",
        "es": "Pérdidas de cultivos probables; escasez de agua frecuente.",
        "fr": "Pertes de récoltes probables ; pénuries d'eau fréquentes.",
    },
    "cat_d3_label": {"en": "Extreme Drought", "es": "Sequía extrema", "fr": "Sécheresse extrême"},
    "cat_d3_desc": {
        "en": "Major crop losses; widespread water shortages.",
        "es": "Pérdidas importantes de cultivos; escasez de agua generalizada.",
        "fr": "Pertes de récoltes majeures ; pénuries d'eau généralisées.",
    },
    "cat_d4_label": {"en": "Exceptional Drought", "es": "Sequía excepcional", "fr": "Sécheresse exceptionnelle"},
    "cat_d4_desc": {
        "en": "Exceptional and widespread crop losses; emergency water shortages.",
        "es": "Pérdidas de cultivos excepcionales y generalizadas; escasez de agua de emergencia.",
        "fr": "Pertes de récoltes exceptionnelles et généralisées ; pénuries d'eau critiques.",
    },
    "plain_none": {
        "en": "Not enough data yet to compare to the typical range.",
        "es": "Aún no hay datos suficientes para comparar con el rango típico.",
        "fr": "Pas encore assez de données pour comparer à la plage typique.",
    },
    "plain_wet": {
        "en": "This value is wetter than {pct}% of years on record for this time of year.",
        "es": "Este valor es más húmedo que el {pct}% de los años registrados para esta época del año.",
        "fr": "Cette valeur est plus humide que {pct} % des années enregistrées pour cette période de l'année.",
    },
    "plain_dry": {
        "en": "This value is in the driest {pct}% of years on record for this time of year.",
        "es": "Este valor está entre el {pct}% de los años más secos registrados para esta época del año.",
        "fr": "Cette valeur se situe parmi les {pct} % d'années les plus sèches enregistrées pour cette période.",
    },
    # ---- alerts ----
    "reading_rain_label": {
        "en": "Rainfall (last 3 months)",
        "es": "Lluvia (últimos 3 meses)",
        "fr": "Pluie (3 derniers mois)",
    },
    "reading_soil_label": {
        "en": "Soil moisture (root-zone)",
        "es": "Humedad del suelo (zona radicular)",
        "fr": "Humidité du sol (zone racinaire)",
    },
    "reading_wet": {"en": "Wetter than usual", "es": "Más húmedo de lo habitual", "fr": "Plus humide que d'habitude"},
    "reading_normal": {"en": "Near normal", "es": "Cerca de lo normal", "fr": "Proche de la normale"},
    "reading_approaching": {"en": "Drier than usual", "es": "Más seco de lo habitual", "fr": "Plus sec que d'habitude"},
    "reading_triggered": {
        "en": "Very dry — at or past alert level",
        "es": "Muy seco — en el nivel de alerta o más allá",
        "fr": "Très sec — au niveau d'alerte ou au-delà",
    },
    "reading_slightly_dry": {
        "en": "Slightly drier than usual",
        "es": "Ligeramente más seco de lo habitual",
        "fr": "Légèrement plus sec que d'habitude",
    },
    "reading_no_data": {"en": "No data yet", "es": "Aún sin datos", "fr": "Pas encore de données"},
    "reading_activates_below": {
        "en": "Activates if below {thr}",
        "es": "Se activa si baja de {thr}",
        "fr": "S'active en dessous de {thr}",
    },
    "alert_not_calibrated": {
        "en": "Drought alert thresholds are not yet calibrated for this country. "
              "Run `COUNTRY=<key> python -m el_nino.experiments.trigger_calibration` "
              "and bake the recommended config into `etl/triggers.py`.",
        "es": "Los umbrales de alerta de sequía aún no están calibrados para este país. "
              "Ejecute `COUNTRY=<key> python -m el_nino.experiments.trigger_calibration` "
              "e incorpore la configuración recomendada en `etl/triggers.py`.",
        "fr": "Les seuils d'alerte sécheresse ne sont pas encore calibrés pour ce pays. "
              "Lancez `COUNTRY=<key> python -m el_nino.experiments.trigger_calibration` "
              "et intégrez la configuration recommandée dans `etl/triggers.py`.",
    },
    "alert_header": {"en": "### Drought alert", "es": "### Alerta de sequía", "fr": "### Alerte sécheresse"},
    "alert_pill_alert": {
        "en": "ALERT — drought conditions met",
        "es": "ALERTA — se cumplen las condiciones de sequía",
        "fr": "ALERTE — conditions de sécheresse atteintes",
    },
    "alert_pill_alert_sub": {
        "en": "Triggered in {n} {dep_word} so far this year",
        "es": "Activada en {n} {dep_word} en lo que va del año",
        "fr": "Déclenchée dans {n} {dep_word} depuis le début de l'année",
    },
    "alert_pill_watching": {"en": "Watching closely", "es": "En vigilancia", "fr": "Sous surveillance"},
    "alert_pill_watching_sub": {
        "en": "Critical growth weeks are happening now ({start}–{end})",
        "es": "Las semanas críticas de crecimiento están en curso ({start}–{end})",
        "fr": "Les semaines critiques de croissance sont en cours ({start}–{end})",
    },
    "alert_pill_clear": {
        "en": "All clear for this year's growing season",
        "es": "Sin alerta para la temporada de cultivo de este año",
        "fr": "Rien à signaler pour la saison de culture de cette année",
    },
    "alert_pill_clear_sub": {
        "en": "The {year} critical window passed without the alert triggering.",
        "es": "La ventana crítica de {year} pasó sin que se activara la alerta.",
        "fr": "La fenêtre critique de {year} est passée sans déclenchement de l'alerte.",
    },
    "alert_pill_pre": {
        "en": "Pre-season — quiet for now",
        "es": "Pretemporada — sin novedad por ahora",
        "fr": "Avant-saison — calme pour l'instant",
    },
    "alert_pill_pre_sub": {
        "en": "Critical growth weeks start in {days} days ({start}).",
        "es": "Las semanas críticas de crecimiento comienzan en {days} días ({start}).",
        "fr": "Les semaines critiques de croissance commencent dans {days} jours ({start}).",
    },
    "alert_right_now": {
        "en": "**Right now (country-wide):**",
        "es": "**Ahora mismo (a nivel nacional):**",
        "fr": "**En ce moment (à l'échelle du pays) :**",
    },
    "alert_explain": {
        "en": "**What sets off this alert.** When rainfall has been **very dry for "
              "the last 3 months** *and* **soil moisture is below normal**, all at "
              "the same time during the critical growth window "
              "(**{start} to {end}**). This is when rainfed crops in {country} are "
              "most vulnerable to drought — water stress during this window translates "
              "directly into yield loss in the {priority} ({names}).",
        "es": "**Qué activa esta alerta.** Cuando la lluvia ha sido **muy escasa durante "
              "los últimos 3 meses** *y* **la humedad del suelo está por debajo de lo normal**, "
              "ambas al mismo tiempo durante la ventana crítica de crecimiento "
              "(**{start} al {end}**). Es cuando los cultivos de secano en {country} son "
              "más vulnerables a la sequía — el estrés hídrico en esta ventana se traduce "
              "directamente en pérdida de rendimiento en el {priority} ({names}).",
        "fr": "**Ce qui déclenche cette alerte.** Lorsque la pluie a été **très faible pendant "
              "les 3 derniers mois** *et* que **l'humidité du sol est sous la normale**, "
              "en même temps, pendant la fenêtre critique de croissance "
              "(**du {start} au {end}**). C'est à ce moment que les cultures pluviales de "
              "{country} sont les plus vulnérables à la sécheresse — le stress hydrique pendant "
              "cette fenêtre se traduit directement par des pertes de rendement dans les "
              "{priority} ({names}).",
    },
    "alert_show_triggered": {
        "en": "Show triggered {depts}",
        "es": "Mostrar {depts} con alerta",
        "fr": "Afficher les {depts} en alerte",
    },
    "alert_triggered_row": {
        "en": "- **{dep}** — rainfall index `{spi}`, soil moisture `{rzsm}σ`, on {date}",
        "es": "- **{dep}** — índice de lluvia `{spi}`, humedad del suelo `{rzsm}σ`, el {date}",
        "fr": "- **{dep}** — indice de pluie `{spi}`, humidité du sol `{rzsm}σ`, le {date}",
    },
    "alert_confidence_heading": {
        "en": "How confident is this alert? (based on {n} years of data)",
        "es": "¿Qué tan confiable es esta alerta? (según {n} años de datos)",
        "fr": "Quelle confiance accorder à cette alerte ? (sur {n} années de données)",
    },
    "alert_history_heading": {
        "en": "Past years this alert triggered",
        "es": "Años anteriores en que se activó esta alerta",
        "fr": "Années passées où cette alerte s'est déclenchée",
    },
    "alert_eg": {
        "en": "(e.g., {years})",
        "es": "(p. ej., {years})",
        "fr": "(p. ex. {years})",
    },
    "alert_confidence_body": {
        "en": """
| Metric | Estimate | 95% range |
|---|---:|---:|
| When triggered, how often there was a real drought event | {precision} | {precision_lo} – {precision_hi} |
| Fraction of drought years the alert catches | {recall} | {recall_lo} – {recall_hi} |
| Fraction of *severe* drought years caught {anchor} | {severe} | {severe_lo} – {severe_hi} |
| False alarms per decade | {fp} | {fp_lo} – {fp_hi} |

Thresholds were chosen by checking which would have flagged the documented
El Niño drought years for {country} {anchor} without firing in normal years.
The fire test runs **per {dept}** — if any one of the {priority} ({names})
crosses both thresholds, the alert is raised. With only {n_years} years of
soil-moisture data, the margin of error is still wide. Re-run
`COUNTRY={country_key} python -m el_nino.experiments.trigger_calibration`
annually as more data accumulates.
""",
        "es": """
| Métrica | Estimación | Rango 95% |
|---|---:|---:|
| Cuando se activó, con qué frecuencia hubo una sequía real | {precision} | {precision_lo} – {precision_hi} |
| Fracción de años de sequía que la alerta detecta | {recall} | {recall_lo} – {recall_hi} |
| Fracción de años de sequía *severa* detectados {anchor} | {severe} | {severe_lo} – {severe_hi} |
| Falsas alarmas por década | {fp} | {fp_lo} – {fp_hi} |

Los umbrales se eligieron verificando cuáles habrían señalado los años de
sequía por El Niño documentados para {country} {anchor} sin activarse en años
normales. La prueba se ejecuta **por {dept}** — si cualquiera de los del
{priority} ({names}) cruza ambos umbrales, se emite la alerta. Con solo
{n_years} años de datos de humedad del suelo, el margen de error sigue siendo
amplio. Vuelva a ejecutar
`COUNTRY={country_key} python -m el_nino.experiments.trigger_calibration`
cada año a medida que se acumulen más datos.
""",
        "fr": """
| Indicateur | Estimation | Intervalle 95 % |
|---|---:|---:|
| Lors d'un déclenchement, fréquence d'une vraie sécheresse | {precision} | {precision_lo} – {precision_hi} |
| Part des années de sécheresse détectées par l'alerte | {recall} | {recall_lo} – {recall_hi} |
| Part des années de sécheresse *sévère* détectées {anchor} | {severe} | {severe_lo} – {severe_hi} |
| Fausses alertes par décennie | {fp} | {fp_lo} – {fp_hi} |

Les seuils ont été choisis en vérifiant lesquels auraient signalé les années
de sécheresse El Niño documentées pour {country} {anchor} sans se déclencher
les années normales. Le test s'exécute **par {dept}** — si l'un des
{priority} ({names}) franchit les deux seuils, l'alerte est émise. Avec
seulement {n_years} années de données d'humidité du sol, la marge d'erreur
reste large. Relancez
`COUNTRY={country_key} python -m el_nino.experiments.trigger_calibration`
chaque année à mesure que les données s'accumulent.
""",
    },
    "alert_past_years": {
        "en": "**📜 Past years this alert triggered: {n} ({years})**",
        "es": "**📜 Años anteriores en que se activó esta alerta: {n} ({years})**",
        "fr": "**📜 Années passées où cette alerte s'est déclenchée : {n} ({years})**",
    },
    "alert_past_row": {
        "en": "- **{year}** — {n} {dep_word}: {deps}",
        "es": "- **{year}** — {n} {dep_word}: {deps}",
        "fr": "- **{year}** — {n} {dep_word} : {deps}",
    },
    # ---- about ----
    "about_title": {"en": "About this data", "es": "Acerca de estos datos", "fr": "À propos de ces données"},
    "about_body": {
        "en": """
    **Indicators** (refresh cadence in parentheses):
    - **CHIRPS v3** rainfall + SPI-1/3/6 ({chirps_days} days)
    - **NOAA GFS0P25** 15-day rainfall forecast (daily refresh, uncalibrated — GFS over-predicts in the tropics)
    - **SMAP L4** root-zone soil moisture ({smap_days} days)
    - **FAO WAPOR v3** L1 AETI (dekadal, ~300 m) ({wapor_days} days)
    - **IMERG-Late V07** daily rainfall ({imerg_days} day)

    **Climatology baseline:** {clim_start}–{clim_end}.

    **Drought classification:** U.S. Drought Monitor SPI bins
    (D0 ≤ −1.0, D1 ≤ −1.3, D2 ≤ −1.6, D3 ≤ −2.0, D4 ≤ −2.5).

    **Alert thresholds** are country-specific and calibrated against historical
    El Niño drought events for {country} — see the
    "How confident is this alert?" expander under the Drought alert section.
    Re-run `COUNTRY={country_key} python -m el_nino.experiments.trigger_calibration`
    after each annual data refresh to update the calibration.
    """,
        "es": """
    **Indicadores** (frecuencia de actualización entre paréntesis):
    - **CHIRPS v3** lluvia + SPI-1/3/6 ({chirps_days} días)
    - **NOAA GFS0P25** pronóstico de lluvia a 15 días (actualización diaria, sin calibrar — GFS sobreestima en los trópicos)
    - **SMAP L4** humedad del suelo en zona radicular ({smap_days} días)
    - **FAO WAPOR v3** L1 AETI (decadal, ~300 m) ({wapor_days} días)
    - **IMERG-Late V07** lluvia diaria ({imerg_days} día)

    **Línea base climatológica:** {clim_start}–{clim_end}.

    **Clasificación de sequía:** categorías SPI del U.S. Drought Monitor
    (D0 ≤ −1.0, D1 ≤ −1.3, D2 ≤ −1.6, D3 ≤ −2.0, D4 ≤ −2.5).

    **Los umbrales de alerta** son específicos por país y están calibrados con
    eventos históricos de sequía por El Niño en {country} — vea el panel
    "¿Qué tan confiable es esta alerta?" en la sección Alerta de sequía.
    Vuelva a ejecutar `COUNTRY={country_key} python -m el_nino.experiments.trigger_calibration`
    después de cada actualización anual de datos para renovar la calibración.
    """,
        "fr": """
    **Indicateurs** (fréquence d'actualisation entre parenthèses) :
    - **CHIRPS v3** pluie + SPI-1/3/6 ({chirps_days} jours)
    - **NOAA GFS0P25** prévision de pluie à 15 jours (actualisation quotidienne, non calibrée — GFS surestime sous les tropiques)
    - **SMAP L4** humidité du sol en zone racinaire ({smap_days} jours)
    - **FAO WAPOR v3** L1 AETI (décadaire, ~300 m) ({wapor_days} jours)
    - **IMERG-Late V07** pluie journalière ({imerg_days} jour)

    **Référence climatologique :** {clim_start}–{clim_end}.

    **Classification de la sécheresse :** classes SPI du U.S. Drought Monitor
    (D0 ≤ −1,0, D1 ≤ −1,3, D2 ≤ −1,6, D3 ≤ −2,0, D4 ≤ −2,5).

    **Les seuils d'alerte** sont propres à chaque pays et calibrés sur les
    épisodes historiques de sécheresse El Niño en {country} — voir le panneau
    « Quelle confiance accorder à cette alerte ? » dans la section Alerte sécheresse.
    Relancez `COUNTRY={country_key} python -m el_nino.experiments.trigger_calibration`
    après chaque actualisation annuelle des données pour renouveler la calibration.
    """,
    },
    # ---- footer ----
    "footer_text": {
        "en": 'Created by <a href="https://geography.columbian.gwu.edu/michael-mann" target="_blank" rel="noopener">Michael Mann, PhD</a>. '
              "Data sources: rainfall &mdash; "
              '<a href="https://www.chc.ucsb.edu/data/chirps" target="_blank" rel="noopener">CHIRPS</a> (UCSB Climate Hazards Center) '
              'and <a href="https://gpm.nasa.gov/data/imerg" target="_blank" rel="noopener">IMERG</a> (NASA); '
              "soil moisture &mdash; "
              '<a href="https://smap.jpl.nasa.gov/" target="_blank" rel="noopener">SMAP L4</a> (NASA); '
              "evapotranspiration &mdash; "
              '<a href="https://wapor.apps.fao.org/" target="_blank" rel="noopener">WAPOR</a> (FAO); '
              "El Ni&ntilde;o index &mdash; "
              '<a href="https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php" target="_blank" rel="noopener">ONI</a> (NOAA); '
              "administrative boundaries &mdash; FAO GAUL. "
              "This site is independent and not affiliated with or endorsed by any data provider. "
              "Indicators and forecasts are produced by this dashboard and are provided without "
              "warranty of accuracy or fitness for any purpose.",
        "es": 'Creado por <a href="https://geography.columbian.gwu.edu/michael-mann" target="_blank" rel="noopener">Michael Mann, PhD</a>. '
              "Fuentes de datos: lluvia &mdash; "
              '<a href="https://www.chc.ucsb.edu/data/chirps" target="_blank" rel="noopener">CHIRPS</a> (UCSB Climate Hazards Center) '
              'e <a href="https://gpm.nasa.gov/data/imerg" target="_blank" rel="noopener">IMERG</a> (NASA); '
              "humedad del suelo &mdash; "
              '<a href="https://smap.jpl.nasa.gov/" target="_blank" rel="noopener">SMAP L4</a> (NASA); '
              "evapotranspiración &mdash; "
              '<a href="https://wapor.apps.fao.org/" target="_blank" rel="noopener">WAPOR</a> (FAO); '
              "índice de El Ni&ntilde;o &mdash; "
              '<a href="https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php" target="_blank" rel="noopener">ONI</a> (NOAA); '
              "límites administrativos &mdash; FAO GAUL. "
              "Este sitio es independiente y no está afiliado ni respaldado por ningún proveedor de datos. "
              "Los indicadores y pronósticos son producidos por este tablero y se ofrecen sin "
              "garantía de exactitud ni de idoneidad para ningún fin.",
        "fr": 'Créé par <a href="https://geography.columbian.gwu.edu/michael-mann" target="_blank" rel="noopener">Michael Mann, PhD</a>. '
              "Sources des données : pluie &mdash; "
              '<a href="https://www.chc.ucsb.edu/data/chirps" target="_blank" rel="noopener">CHIRPS</a> (UCSB Climate Hazards Center) '
              'et <a href="https://gpm.nasa.gov/data/imerg" target="_blank" rel="noopener">IMERG</a> (NASA) ; '
              "humidité du sol &mdash; "
              '<a href="https://smap.jpl.nasa.gov/" target="_blank" rel="noopener">SMAP L4</a> (NASA) ; '
              "évapotranspiration &mdash; "
              '<a href="https://wapor.apps.fao.org/" target="_blank" rel="noopener">WAPOR</a> (FAO) ; '
              "indice El Ni&ntilde;o &mdash; "
              '<a href="https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php" target="_blank" rel="noopener">ONI</a> (NOAA) ; '
              "limites administratives &mdash; FAO GAUL. "
              "Ce site est indépendant et n'est ni affilié à un fournisseur de données ni approuvé par lui. "
              "Les indicateurs et prévisions sont produits par ce tableau de bord et fournis sans "
              "garantie d'exactitude ni d'adéquation à un usage quelconque.",
    },
}
