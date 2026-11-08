"""Related work + bibliography, with every reference verified against Europe PMC
or Crossref (DOIs resolved) before being written here.

Used by both report generators (src/07 and src/08).
"""
from __future__ import annotations

# Each entry: (citation key, formatted LaTeX bibliographic entry, verification source)
# Europe PMC / Crossref lookups were performed on 2026-11-06; see
# reports/related_works_verified.json for the raw payloads.
REFERENCES: dict[str, str] = {
    # ---------------- 1. glanders epidemiology ----------------
    "khan2013": (
        "Khan I, Wieler LH, Melzer F, et al. Glanders in animals: a review on epidemiology, clinical "
        "presentation, diagnosis and countermeasures. "
        "\\emph{Transboundary and Emerging Diseases}. 2013. "
        "doi:10.1111/j.1865-1682.2012.01342.x"
    ),
    "kanani2026": (
        "Kanani Y, Oryan A, Derakhshandeh A. Glanders: past, present and future of a "
        "neglected zoonosis as a threat in veterinary and human health. "
        "\\emph{Veterinary Medicine and Science}. 2026. doi:10.1002/vms3.70950"
    ),
    "purnama2026": (
        "Purnama MTE, Firdausy LW, Fikri F, et al. Seroprevalence and "
        "associated epidemiological drivers of glanders in horses: a systematic review and "
        "meta-analysis. \\emph{Research in Veterinary Science}. 2026;106416. "
        "doi:10.1016/j.rvsc.2026.106416"
    ),
    "mota2022": (
        "Mota RA, Pinheiro J\\'unior JW. Current status of glanders in Brazil: recent "
        "advances and challenges. \\emph{Brazilian Journal of Microbiology}. 2022. "
        "doi:10.1007/s42770-022-00814-1"
    ),
    # ---------------- 2. India ----------------
    "singha2026": (
        "Singha H, Shanmugasundaram K, Jhandai P, et al. "
        "Surveillance of equine glanders in India (2019--2023): prevalence estimate, risk "
        "analysis and future strategy. \\emph{Microbial Pathogenesis}. 2026;217:108597. "
        "doi:10.1016/j.micpath.2026.108597"
    ),
    "singha2020": (
        "Singha H, Shanmugasundaram K, Tripathi BN, et al. "
        "Serological surveillance and clinical investigation of glanders among indigenous "
        "equines in India from 2015 to 2018. \\emph{Transboundary and Emerging Diseases}. "
        "2020. doi:10.1111/tbed.13475"
    ),
    "malik2012": (
        "Malik P, Singha H, Khurana SK, et al. Emergence and "
        "re-emergence of glanders in India: a description of outbreaks from 2006 to 2011. "
        "\\emph{Veterinaria Italiana}. 2012. PMID:22718333"
    ),
    # ---------------- 3. spatial / temporal risk analysis ----------------
    "fonseca2019": (
        "Fonseca-Rodr\\'iguez O, Pinheiro J\\'unior JW, Mota RA. Spatiotemporal analysis of "
        "glanders in Brazil. \\emph{Journal of Equine Veterinary Science}. 2019. "
        "doi:10.1016/j.jevs.2019.03.216"
    ),
    "hollings2017": (
        "Hollings T, Robinson A, van Andel M, et al. Species distribution "
        "models: a comparison of statistical approaches for livestock and disease epidemics. "
        "\\emph{PLOS ONE}. 2017;12(8):e0183626. doi:10.1371/journal.pone.0183626"
    ),
    # ---------------- 4. ML for animal disease risk ----------------
    "alshatti2026": (
        "Alshatti M, Al-Hemoud A, Othman A, et al. A risk prediction model for "
        "highly pathogenic avian influenza outbreaks in Kuwait. "
        "\\emph{Frontiers in Veterinary Science}. 2026. doi:10.3389/fvets.2026.1843962"
    ),
    "kane2014": (
        "Kane MJ, Price N, Scotch M, Rabinowitz P. Comparison of ARIMA and Random Forest "
        "time series models for prediction of avian influenza H5N1 outbreaks. "
        "\\emph{BMC Bioinformatics}. 2014;15:276. doi:10.1186/1471-2105-15-276"
    ),
    "walsh2019": (
        "Walsh DP, Ma TF, Ip HS, Zhu J. Artificial intelligence and avian influenza: using "
        "machine learning to enhance active surveillance for avian influenza viruses. "
        "\\emph{Transboundary and Emerging Diseases}. 2019. doi:10.1111/tbed.13318"
    ),
    "yoo2022": (
        "Yoo DS, Song YH, Choi DW, et al. Machine learning-driven dynamic "
        "risk prediction for highly pathogenic avian influenza at poultry farms in the "
        "Republic of Korea. \\emph{Transboundary and Emerging Diseases}. 2021. "
        "doi:10.1111/tbed.14419"
    ),
    # ---------------- 5. ML for glanders (the gap) ----------------
    "moawad2019": (
        "Moawad AA, Silge A, Bocklitz T, Fischer K, R\\\"osch P, Roesler U, Elschner MC, "
        "Popp J, Neubauer H. A machine learning-based Raman spectroscopic assay for the "
        "identification of \\emph{Burkholderia mallei} and related species. "
        "\\emph{Molecules}. 2019;24(24):4516. doi:10.3390/molecules24244516"
    ),
    "stoeckel2015": (
        "St\\\"ockel S, Meisel S, Elschner M, Melzer F, R\\\"osch P, Popp J. Raman "
        "spectroscopic detection and identification of \\emph{Burkholderia mallei} and "
        "\\emph{Burkholderia pseudomallei}. \\emph{Analytical and Bioanalytical Chemistry}. "
        "2015;407(3):833--843. doi:10.1007/s00216-014-7906-5"
    ),
    # ---------------- 6. text mining for event extraction ----------------
    "collier2012": (
        "Collier N. Uncovering text mining: a survey of current work on web-based epidemic "
        "intelligence. \\emph{Global Public Health}. 2012. "
        "doi:10.1080/17441692.2012.699975"
    ),
    "lejeune2015": (
        "Lejeune G, Brixtel R, Doucet A, et al. Multilingual event extraction for epidemic "
        "detection. \\emph{Artificial Intelligence in Medicine}. 2015. "
        "doi:10.1016/j.artmed.2015.06.005"
    ),
    # ---------------- 7. methodological foundations ----------------
    "chen2016": (
        "Chen T, Guestrin C. XGBoost: a scalable tree boosting system. In: "
        "\\emph{Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge "
        "Discovery and Data Mining}. 2016:785--794. doi:10.1145/2939672.2939785"
    ),
    "ke2017": (
        "Ke G, Meng Q, Finley T, et al. LightGBM: a highly "
        "efficient gradient boosting decision tree. In: \\emph{Advances in Neural "
        "Information Processing Systems 30 (NIPS)}. 2017:3146--3154."
    ),
    "breiman2001": (
        "Breiman L. Random forests. \\emph{Machine Learning}. 2001. "
        "doi:10.1023/A:1010933404324"
    ),
    "lundberg2017": (
        "Lundberg SM, Lee SI. A unified approach to interpreting model predictions. In: "
        "\\emph{Advances in Neural Information Processing Systems 30 (NIPS)}. "
        "2017:4765--4774. arXiv:1705.07874"
    ),
    "saito2015": (
        "Saito T, Rehmsmeier M. The precision-recall plot is more informative than the ROC "
        "plot when evaluating binary classifiers on imbalanced datasets. "
        "\\emph{PLOS ONE}. 2015;10(3):e0118432. doi:10.1371/journal.pone.0118432"
    ),
    "davis2006": (
        "Davis J, Goadrich M. The relationship between precision-recall and ROC curves. In: "
        "\\emph{Proceedings of the 23rd International Conference on Machine Learning}. "
        "2006:233--240. doi:10.1145/1143844.1143874"
    ),
    "roberts2017": (
        "Roberts DR, Bahn V, Ciuti S, et al. "
        "Cross-validation strategies for data with temporal, spatial, hierarchical, or "
        "phylogenetic structure. \\emph{Ecography}. 2017. "
        "doi:10.1111/ecog.02881"
    ),
    "niculescu2005": (
        "Niculescu-Mizil A, Caruana R. Predicting good probabilities with supervised "
        "learning. In: \\emph{Proceedings of the 22nd International Conference on Machine "
        "Learning}. 2005:625--632. doi:10.1145/1102351.1102430"
    ),
    "huang2020": (
        "Huang Y, Li W, Macheret F, et al. A tutorial on calibration "
        "measurements and calibration models for clinical prediction models. "
        "\\emph{Journal of the American Medical Informatics Association}. "
        "2020;27(4):621--633. doi:10.1093/jamia/ocz228"
    ),
    # ---------------- 8. retrieval, embeddings and language models ----------------
    "lewis2020": (
        "Lewis P, Perez E, Piktus A, et al. Retrieval-augmented generation for "
        "knowledge-intensive NLP tasks. In: \\emph{Advances in Neural Information "
        "Processing Systems 33 (NeurIPS)}. 2020:9459--9474. arXiv:2005.11401"
    ),
    "reimers2019": (
        "Reimers N, Gurevych I. Sentence-BERT: sentence embeddings using Siamese "
        "BERT-networks. In: \\emph{Proceedings of the 2019 Conference on Empirical "
        "Methods in Natural Language Processing (EMNLP-IJCNLP)}. 2019:3982--3992. "
        "doi:10.18653/v1/D19-1410"
    ),
    "malkov2020": (
        "Malkov YA, Yashunin DA. Efficient and robust approximate nearest neighbor "
        "search using hierarchical navigable small world graphs. \\emph{IEEE "
        "Transactions on Pattern Analysis and Machine Intelligence}. "
        "2020;42(4):824--836. doi:10.1109/TPAMI.2018.2889473"
    ),
    "robertson2009": (
        "Robertson S, Zaragoza H. The probabilistic relevance framework: BM25 and "
        "beyond. \\emph{Foundations and Trends in Information Retrieval}. "
        "2009;3(4):333--389. doi:10.1561/1500000019"
    ),
    "cormack2009": (
        "Cormack GV, Clarke CLA, Buettcher S. Reciprocal rank fusion outperforms "
        "Condorcet and individual rank learning methods. In: \\emph{Proceedings of "
        "the 32nd International ACM SIGIR Conference}. 2009:758--759. "
        "doi:10.1145/1571941.1572114"
    ),
    "pedregosa2011": (
        "Pedregosa F, Varoquaux G, Gramfort A, et al. Scikit-learn: machine learning "
        "in Python. \\emph{Journal of Machine Learning Research}. 2011;12:2825--2830."
    ),
}

# Data sources and grey literature.
DATA_REFS: dict[str, str] = {
    "wahis": (
        "WOAH. World Animal Health Information System (WAHIS). \\url{https://wahis.woah.org}"
    ),
    "dahd2025": (
        "Department of Animal Husbandry and Dairying, Government of India. "
        "\\emph{National Action Plan for Control and Eradication of Glanders in India} "
        "(Revised 2025). New Delhi: DAHD; 2025."
    ),
    "faostat": (
        "FAO. FAOSTAT: crops and livestock products. \\url{https://www.fao.org/faostat}"
    ),
    "power": (
        "NASA Langley Research Center. POWER agroclimatology API. "
        "\\url{https://power.larc.nasa.gov}"
    ),
    "wdi": (
        "World Bank. World Development Indicators. \\url{https://databank.worldbank.org}"
    ),
    "europepmc": (
        "Europe PMC literature search API. \\url{https://europepmc.org}"
    ),
}


RELATED_TEX = r"""
\section{Related Work}
\label{sec:related}

\textbf{Glanders.} A neglected zoonosis of equids with high mortality and real human risk
\cite{khan2013,kanani2026}; a 2026 meta-analysis consolidates seroprevalence and names
management and movement as the main drivers \cite{purnama2026}. Brazil keeps an active
control literature \cite{mota2022}.

\textbf{India.} Outbreaks 2006--11 \cite{malik2012}, serosurveillance 2015--18
\cite{singha2020}, and a multi-state survey 2019--23 \cite{singha2026} establish
\emph{where} glanders is. None builds a predictive model.

\textbf{Geographic risk.} Spatiotemporal cluster detection for Brazilian glanders
\cite{fonseca2019} and niche models for livestock disease \cite{hollings2017} are both
descriptive: clusters are found after the fact, not forecast.

\textbf{ML for animal disease.} The closest template is avian influenza: ARIMA versus
random forest \cite{kane2014}, ML-targeted surveillance \cite{walsh2019}, dynamic farm-level
risk \cite{yoo2022}, and an outbreak model for Kuwait \cite{alshatti2026}. That template
exists for influenza, not glanders.

\textbf{The gap.} The only ML on \emph{B.\ mallei} is spectroscopic identification of the
organism \cite{moawad2019,stoeckel2015}, which is a laboratory test rather than a population
forecast.
Text mining has precedent in epidemic intelligence \cite{collier2012,lejeune2015}, but not
for glanders.

\textbf{Methods.} Random forests \cite{breiman2001}, XGBoost \cite{chen2016} and LightGBM
\cite{ke2017}, explained with SHAP \cite{lundberg2017}. Rare events call for
precision-recall \cite{saito2015,davis2006}; probabilities are calibrated
\cite{niculescu2005,huang2020}; validation respects temporal and spatial dependence
\cite{roberts2017}. Data: WAHIS \cite{wahis}, India's 2025 action plan \cite{dahd2025},
FAOSTAT \cite{faostat}, World Bank \cite{wdi}, NASA POWER \cite{power}, Europe PMC
\cite{europepmc}.

\textbf{Position.} Prior glanders work is descriptive or laboratory-based, prior veterinary
ML is built for influenza, and text-mined occurrence has never been used for glanders. This
study joins all four and reports what predicts and what does not.
"""




def bibliography_tex(long_form: bool = False) -> str:
    """Return a thebibliography block with all cited keys.

    long_form=True reproduces the original 2-column, footnotesize layout used by
    the long report; the brief uses the tighter 3-column version.
    """
    cols = 2 if long_form else 3
    size = "\\footnotesize" if long_form else "\\tiny"
    items = []
    for key in REFERENCES:
        items.append(f"\\bibitem{{{key}}} {REFERENCES[key]}")
    for key in DATA_REFS:
        items.append(f"\\bibitem{{{key}}} {DATA_REFS[key]}")
    body = "\n".join(items)
    return (
        "\\begin{multicols}{" + str(cols) + "}\n"
        "\\begin{thebibliography}{99}\n"
        + size + "\n"
        "\\setlength{\\itemsep}{0.15em}\n"
        "\\setlength{\\parskip}{0pt}\n"
        + body + "\n"
        "\\end{thebibliography}\n"
        "\\end{multicols}\n"
    )

# --------------------------------------------------------------------------- #
# Frozen original related-work text for the long report (src/07).
# Kept separately so the long document regenerates exactly as written, while
# the brief uses the shorter RELATED_TEX above.
# --------------------------------------------------------------------------- #
RELATED_TEX_LONG = r"""
\section{Related Work}
\label{sec:related}
% =====================================================================

\paragraph{Glanders epidemiology and burden.}
Glanders is reviewed as a neglected zoonosis of equids with high case fatality and a
persistent risk of human infection \cite{khan2013,kanani2026}. A 2026 systematic review
and meta-analysis consolidates seroprevalence estimates and identifies management and
movement as the dominant epidemiological drivers \cite{purnama2026}. Regionally, Brazil
maintains an active research and control literature \cite{mota2022}, and glanders is
endemic or repeatedly reported across parts of Africa, Asia and the Middle East.

\paragraph{Surveillance in India.}
Indian surveillance is the strongest available evidence base. Malik et al.\ described
outbreaks from 2006 to 2011 \cite{malik2012}; Singha et al.\ reported serological
surveillance of indigenous equines from 2015 to 2018 \cite{singha2020}; and the
2019--2023 national programme screened a large multi-state sample, identifying substantial
geographic concentration of seropositives \cite{singha2026}. These studies establish where
glanders occurs and which districts carry the burden. None of them produces a predictive,
calibrated risk model, and none uses population or reanalysis covariates.

\paragraph{Geographic and spatiotemporal risk analysis.}
Descriptive spatial work exists. Fonseca-Rodr\'iguez et al.\ applied spatiotemporal cluster
detection to Brazilian glanders \cite{fonseca2019}. More generally, species distribution
and ecological niche models have been compared as tools for livestock disease
epidemics \cite{hollings2017}. This literature is \emph{descriptive}: it identifies
clusters post hoc rather than forecasting future cells.

\paragraph{Machine learning for animal-disease risk prediction.}
Predictive modelling in veterinary epidemiology is established for avian influenza.
Kane et al.\ compared ARIMA and random forest for H5N1 outbreak prediction
\cite{kane2014}; Walsh et al.\ used machine learning to target active surveillance
\cite{walsh2019}; Yoo et al.\ built dynamic farm-level risk prediction in the Republic of
Korea \cite{yoo2022}; and Alshatti et al.\ produced a risk prediction model for HPAI in
Kuwait \cite{alshatti2026}. This is the closest methodological template for the present
work, and it exists for influenza rather than for glanders.

\paragraph{Machine learning and glanders: the gap.}
The only machine-learning work specific to \emph{Burkholderia mallei} that we located is
spectroscopic identification of the organism --- Raman assays classified by learned
models \cite{moawad2019,stoeckel2015}. That is a laboratory diagnostic problem, not a
population-level forecasting problem. A prior-art audit we ran over Europe PMC
returned zero records combining glanders with NASA POWER
climatology and four combining glanders with gradient boosting, none of which is a risk
model. The gap addressed here is therefore specific: a calibrated, chained,
population-level occurrence model for glanders.

\paragraph{Text mining for disease event extraction.}
Using literature as a structured occurrence signal has precedent in epidemic intelligence
\cite{collier2012}, including multilingual event extraction for outbreak
detection \cite{lejeune2015}. Our contribution is to apply sentence-level occurrence
extraction to build the \emph{label} itself when official event data are incomplete, and
to report the surveillance bias that this induces.

\paragraph{Methodological foundations.}
The model families are the standard tabular ensembles: random forests \cite{breiman2001},
XGBoost \cite{chen2016} and LightGBM \cite{ke2017}. Feature attribution uses
SHAP \cite{lundberg2017}. Because the outcome is rare, precision-recall analysis is the
appropriate primary metric \cite{saito2015}, and the relationship between PR and ROC
curves is well characterised \cite{davis2006}. Probability calibration follows
Niculescu-Mizil and Caruana \cite{niculescu2005}, with the measurement framework of Huang
et al.\ \cite{huang2020}. Validation follows Roberts et al., who show that ignoring
temporal and spatial dependence inflates performance estimates \cite{roberts2017} --- the
reason our primary scheme is a forward temporal holdout and our selection criterion is
leave-country-out.

\paragraph{Data sources.}
Official animal-health reporting is drawn from WOAH WAHIS \cite{wahis}; Indian policy and
case definitions from the 2025 National Action Plan \cite{dahd2025}; livestock
populations from FAOSTAT \cite{faostat}; socio-economic covariates from the World Bank
\cite{wdi}; climatology from NASA POWER \cite{power}; and the literature corpus from
Europe PMC \cite{europepmc}.

\paragraph{Positioning.}
The combination above is, to our knowledge, unstudied. Prior glanders work is either
epidemiological description or laboratory classification; prior veterinary ML risk work is
built for influenza; and prior text-mined occurrence work is not used for glanders at all.
This study joins an occurrence corpus, a livestock census, development indicators and
reanalysis climatology into a single country-year panel, and reports both what predicts and
what does not.
"""
