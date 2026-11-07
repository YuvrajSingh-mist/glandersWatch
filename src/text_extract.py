"""Country / year mention extraction used to build the literature occurrence panel."""
from __future__ import annotations

import re

# Canonical ISO3 -> aliases.  Built from World Bank names plus common variants
# that appear in veterinary / historical glanders literature.
ALIASES: dict[str, list[str]] = {
    "IND": ["India", "Indian"],
    "PAK": ["Pakistan", "Pakistani"],
    "BGD": ["Bangladesh"],
    "NPL": ["Nepal"],
    "LKA": ["Sri Lanka"],
    "AFG": ["Afghanistan"],
    "IRN": ["Iran", "Persia", "Iranian"],
    "IRQ": ["Iraq", "Iraqi"],
    "TUR": ["Turkey", "Turkiye", "Turkish", "Ottoman"],
    "SYR": ["Syria", "Syrian"],
    "SAU": ["Saudi Arabia"],
    "ARE": ["United Arab Emirates", "UAE", "U.A.E."],
    "QAT": ["Qatar"],
    "KWT": ["Kuwait"],
    "OMN": ["Oman"],
    "YEM": ["Yemen"],
    "JOR": ["Jordan"],
    "LBN": ["Lebanon"],
    "ISR": ["Israel"],
    "PSE": ["Palestine", "Palestinian"],
    "EGY": ["Egypt", "Egyptian"],
    "LBY": ["Libya"],
    "TUN": ["Tunisia"],
    "DZA": ["Algeria"],
    "MAR": ["Morocco"],
    "SDN": ["Sudan"],
    "SSD": ["South Sudan"],
    "ETH": ["Ethiopia", "Ethiopian"],
    "ERI": ["Eritrea"],
    "SOM": ["Somalia"],
    "KEN": ["Kenya"],
    "TZA": ["Tanzania"],
    "UGA": ["Uganda"],
    "RWA": ["Rwanda"],
    "BDI": ["Burundi"],
    "NGA": ["Nigeria", "Nigerian"],
    "NER": ["Niger"],
    "TCD": ["Chad"],
    "CMR": ["Cameroon"],
    "GHA": ["Ghana"],
    "SEN": ["Senegal"],
    "MLI": ["Mali"],
    "BFA": ["Burkina Faso"],
    "CIV": ["Cote d'Ivoire", "Côte d'Ivoire", "Ivory Coast"],
    "BEN": ["Benin"],
    "TGO": ["Togo"],
    "GIN": ["Guinea"],
    "SLE": ["Sierra Leone"],
    "LBR": ["Liberia"],
    "GMB": ["Gambia"],
    "MRT": ["Mauritania"],
    "CAF": ["Central African Republic"],
    "COD": ["Democratic Republic of the Congo", "DR Congo", "DRC", "Zaire"],
    "COG": ["Republic of the Congo", "Congo"],
    "GAB": ["Gabon"],
    "AGO": ["Angola"],
    "ZMB": ["Zambia"],
    "ZWE": ["Zimbabwe", "Rhodesia"],
    "MWI": ["Malawi"],
    "MOZ": ["Mozambique"],
    "ZAF": ["South Africa", "South African"],
    "NAM": ["Namibia"],
    "BWA": ["Botswana"],
    "LSO": ["Lesotho"],
    "SWZ": ["Eswatini", "Swaziland"],
    "MDG": ["Madagascar"],
    "MUS": ["Mauritius"],
    "CHN": ["China", "Chinese", "PRC"],
    "MNG": ["Mongolia"],
    "JPN": ["Japan", "Japanese"],
    "KOR": ["South Korea", "Republic of Korea", "Korean"],
    "PRK": ["North Korea"],
    "TWN": ["Taiwan"],
    "HKG": ["Hong Kong"],
    "VNM": ["Vietnam", "Viet Nam"],
    "THA": ["Thailand", "Thai"],
    "MYS": ["Malaysia"],
    "IDN": ["Indonesia"],
    "PHL": ["Philippines"],
    "KHM": ["Cambodia"],
    "LAO": ["Laos"],
    "MMR": ["Myanmar", "Burma"],
    "SGP": ["Singapore"],
    "KAZ": ["Kazakhstan"],
    "UZB": ["Uzbekistan"],
    "TKM": ["Turkmenistan"],
    "KGZ": ["Kyrgyzstan"],
    "TJK": ["Tajikistan"],
    "AZE": ["(?<!East )(?<!West )Azerbaijan"],
    "ARM": ["Armenia"],
    "GEO": ["Georgia"],
    "RUS": ["Russia", "Russian Federation", "Russian", "Soviet Union", "USSR"],
    "UKR": ["Ukraine"],
    "BLR": ["Belarus"],
    "MDA": ["Moldova"],
    "POL": ["Poland", "Polish"],
    "DEU": ["Germany", "German"],
    "FRA": ["France", "French"],
    "GBR": ["United Kingdom", "UK", "U.K.", "Britain", "British", "England", "Scotland", "Wales"],
    "IRL": ["Ireland"],
    "ESP": ["Spain", "Spanish"],
    "PRT": ["Portugal"],
    "ITA": ["Italy", "Italian"],
    "NLD": ["Netherlands", "Dutch"],
    "BEL": ["Belgium"],
    "LUX": ["Luxembourg"],
    "CHE": ["Switzerland"],
    "AUT": ["Austria"],
    "CZE": ["Czech Republic", "Czechia"],
    "SVK": ["Slovakia"],
    "HUN": ["Hungary"],
    "ROU": ["Romania"],
    "BGR": ["Bulgaria"],
    "GRC": ["Greece"],
    "HRV": ["Croatia"],
    "SRB": ["Serbia"],
    "SVN": ["Slovenia"],
    "BIH": ["Bosnia"],
    "MKD": ["North Macedonia", "Macedonia"],
    "ALB": ["Albania"],
    "SWE": ["Sweden"],
    "NOR": ["Norway"],
    "DNK": ["Denmark"],
    "FIN": ["Finland"],
    "ISL": ["Iceland"],
    "EST": ["Estonia"],
    "LVA": ["Latvia"],
    "LTU": ["Lithuania"],
    "USA": ["United States", "USA", "U.S.A.", "US", "U.S.", "America", "American"],
    "CAN": ["Canada", "Canadian"],
    "MEX": ["Mexico", "Mexican"],
    "GTM": ["Guatemala"],
    "HND": ["Honduras"],
    "SLV": ["El Salvador"],
    "NIC": ["Nicaragua"],
    "CRI": ["Costa Rica"],
    "PAN": ["Panama"],
    "CUB": ["Cuba"],
    "HTI": ["Haiti"],
    "DOM": ["Dominican Republic"],
    "JAM": ["Jamaica"],
    "PRI": ["Puerto Rico"],
    "TTO": ["Trinidad"],
    "COL": ["Colombia"],
    "VEN": ["Venezuela"],
    "ECU": ["Ecuador"],
    "PER": ["Peru"],
    "BOL": ["Bolivia"],
    "BRA": ["Brazil", "Brasil", "Brazilian"],
    "PRY": ["Paraguay"],
    "URY": ["Uruguay"],
    "ARG": ["Argentina", "Argentine"],
    "CHL": ["Chile"],
    "AUS": ["Australia", "Australian"],
    "NZL": ["New Zealand"],
    "PNG": ["Papua New Guinea"],
    "FJI": ["Fiji"],
}

# Ambiguous aliases that produce false positives in this literature.
# "Georgia" is both a country and a US state; "Congo"/"Guinea" attach to other names.
_DROP = {"GEO": ["Georgia"], "COG": ["Congo"], "GIN": ["Guinea"], "NER": ["Niger"]}
for _iso, _bad in _DROP.items():
    ALIASES[_iso] = [a for a in ALIASES[_iso] if a not in _bad]

# Build one regex, longest alias first so "South Africa" wins over "Africa".
_PATTERNS: list[tuple[str, re.Pattern]] = []
for iso, names in ALIASES.items():
    for name in sorted(names, key=len, reverse=True):
        _PATTERNS.append((iso, re.compile(rf"(?<![A-Za-z]){name if name.startswith('(?<') else re.escape(name)}(?![A-Za-z])")))
_PATTERNS.sort(key=lambda t: -len(t[1].pattern))

YEAR_RE = re.compile(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)")

# Language suggesting the paper actually reports field occurrence, not bench work.
OCCURRENCE_TERMS = re.compile(
    r"\b(outbreak|outbreaks|case report|case series|cases|surveillance|seroprevalence|"
    r"seropositive|occurred|occurrence|reported|detected|isolation|isolated|epidemic|"
    r"epizootic|confirmed|prevalence|incidence|notified)\b",
    re.I,
)
REVIEW_TERMS = re.compile(r"\b(review|meta-analysis|systematic review|perspective|opinion)\b", re.I)


def extract_countries(text: str) -> set[str]:
    found: set[str] = set()
    for iso, pat in _PATTERNS:
        if iso in found:
            continue
        if pat.search(text):
            found.add(iso)
    return found


def extract_years(text: str) -> set[int]:
    return {int(y) for y in YEAR_RE.findall(text)}
