"""Condensed body for the <=30 page technical project report.

Every number is still a @TOKEN@ resolved from reports/*.json by the builder, so
the condensed report cannot drift from the pipeline output. Prose is rewritten
shorter; no claim, citation or measurement is dropped unless noted.
"""

# =====================================================================
INTRO = r"""
% =====================================================================
\chapter{Introduction}
\label{ch:intro}
% =====================================================================

\section{Background}

Glanders is a contagious and often fatal disease of horses, donkeys and mules caused by
\textit{Burkholderia mallei}. The organism has no environmental reservoir, and asymptomatic
carriers remain infectious for long periods. Human infection is rare but carries a high case
fatality rate and follows occupational contact. The disease is notifiable to the World
Organisation for Animal Health and is classified as a potential bioterrorism agent.

The economic weight of the disease sits in low and middle income countries, where equids remain
essential to transport, construction, agriculture and brick manufacture. India recorded 5.44 lakh
equids in the 2019 Livestock Census, many held by households that depend on them for daily income.
The loss of a working animal is a direct loss of livelihood, which makes early warning useful even
where mass treatment is not feasible.

Surveillance data show the disease is neither rare nor geographically contained. A national
programme screening 158,798 equid sera from 391 districts between 2019 and 2023 found 728
seropositive animals in 138 districts, with roughly sixty per cent of positives in Uttar Pradesh.
Earlier surveillance covering 2006 to 2018 reported 1,145 positive equids among 128,404 sera
tested. These are persistent, spatially structured figures, not isolated outbreaks.

\section{Problem Definition}

A district veterinary officer faces a narrow question: is glanders likely to appear in this area
in the coming year? Answering it means combining the history of the disease nearby, the size of
the susceptible population, and the conditions that permit transmission.

Surveillance reports what has already happened. Forecasting systems exist for several livestock
diseases but not for glanders. The problem addressed here is to build a population-level risk
model for glanders from public data and to measure how well it works. It has four parts:

\begin{enumerate}
  \item \textbf{Data assembly.} No public source records glanders occurrence completely. Occurrence
        must be reconstructed from the literature and joined to population and environmental
        covariates at a common resolution.
  \item \textbf{Label construction.} The outcome is rare, so accuracy is useless and a negative
        observation needs an explicit meaning.
  \item \textbf{Model selection under distribution shift.} A model fitted on some countries must be
        evaluated on countries it has never seen, because that is the deployment condition.
  \item \textbf{Threshold economics.} A probability is not an alert. The operating point must be
        defensible against the number of warnings it produces.
\end{enumerate}

\section{Objectives}

There is one research objective and three engineering objectives.

\begin{enumerate}
  \item \textbf{Research.} Assemble a country-year panel for glanders from public sources not
        previously applied to the disease, compare six model families under three validation
        schemes, and report the achievable skill, including negative results.
  \item \textbf{Prediction as a service.} Package the trained model as a versioned, portable
        artefact behind a REST interface, so any consumer can call it without knowing how it works.
  \item \textbf{Cited explanation.} Build a retrieval-augmented layer that explains a prediction
        from official guidance, cites every claim, and refuses rather than guesses.
  \item \textbf{Owner alerts.} Convert a calibrated probability into a small number of messages,
        using threshold, suppression and deduplication rules so that a rare disease does not train
        its users to ignore warnings.
\end{enumerate}

All four share one requirement: each component must be independently testable, independently
replaceable, and free of any hardcoded reference to glanders, so the platform can be repointed at
another disease without altering the components.

\section{Scope and Limitations}

The study is scoped to country-year resolution. District-level modelling for India was envisaged
in the project proposal but is not attempted, because the required covariates could not be
assembled from public sources within the project period. The explanation and alert layers are
resolution-agnostic and apply unchanged once a district-level model exists. The model is a
population-level tool: it does not diagnose an individual animal and does not replace laboratory
confirmation.

Three limitations shape every result that follows. The label comes from published reports, so a
negative may mean no disease or no reporting. Occurrence is reconstructed by an automated extractor
that has not been validated against a hand-annotated set. And with 172 positive observations the
uncertainty on every headline metric is substantial, which is quantified rather than hidden.
"""


# =====================================================================
LIT = r"""
% =====================================================================
\chapter{Literature Review and Gap Analysis}
\label{ch:lit}
% =====================================================================

\section{Epidemiology and Surveillance}

Glanders is treated as a neglected zoonosis with high case fatality and a real occupational risk to
handlers \cite{khan2013,kanani2026}. A recent systematic review and meta-analysis consolidates
seroprevalence estimates and identifies management practice and animal movement as the dominant
drivers \cite{purnama2026}; regional reviews document continued circulation in Brazil
\cite{mota2022}. The disease persists where equid populations are large, animals move often and
surveillance is weak. The first two are measurable from public data, while the third decides whether
the disease is visible at all and is therefore a confounder rather than a covariate.

Indian surveillance is the strongest evidence base. Malik et al. described outbreaks reported
between 2006 and 2011 \cite{malik2012}, Singha et al. reported serological surveillance for 2015 to
2018 \cite{singha2020}, and the national programme covering 2019 to 2023 produced a prevalence
estimate with a risk analysis \cite{singha2026}. These establish where glanders occurs and which
animal-level factors the risk analysis identified. None builds a predictive model, and none uses
population or reanalysis covariates as predictors.

\section{Existing Forecasting Systems in India}

The closest operational system is NADRES v2, the National Animal Disease Referral Expert System run
by ICAR-NIVEDI \cite{nadres}. It combines outbreak records from AICRP centres with meteorological and
remote-sensing covariates and issues district-level forewarnings about two months ahead, using a
model family that overlaps with the one used here.

This project differs in four complementary ways. It is glanders-specific, where a national system
must spread effort across many diseases. It uses only public data, so anyone can reproduce and audit
it. It attaches a cited explanation to each prediction, which matters when the reader is an owner
rather than a trained analyst. And it delivers to the owner directly, with rules that suppress
routine noise. NADRES has institutional access this project lacks; this project has a level of local
explainability that a multi-disease platform does not attempt. The comparison also confirms that the
architecture chosen here is conventional for this problem class, and that the open question is not
whether to forecast but how to make a forecast understandable where it is used.

\section{Spatial Risk and Machine Learning}

Spatial work on glanders is descriptive. Fonseca-Rodr\'iguez et al. applied spatiotemporal cluster
detection to Brazilian data \cite{fonseca2019}, and species distribution models have been compared as
tools for livestock disease \cite{hollings2017}. Cluster detection identifies where cases have already
concentrated; it does not forecast which cells will be positive next period, which is the question an
early warning system must answer.

Predictive modelling is established for avian influenza. Kane et al. compared ARIMA and random forest
models for H5N1 outbreaks \cite{kane2014}, Walsh et al. used machine learning to target active
surveillance \cite{walsh2019}, and Yoo et al. and Alshatti et al. built farm-level risk models in Korea
and Kuwait \cite{yoo2022,alshatti2026}. That literature supplies the methodological template used
here: assemble occurrence, population and environmental covariates at a common unit, fit tree-based
ensembles, and evaluate on held-out periods. The template has been applied to influenza, not to
glanders.

The only machine learning work specific to \textit{B. mallei} is spectroscopic identification. Moawad
et al. built a Raman assay in which learned models classify spectra \cite{moawad2019}, and St\"ockel et
al. reported spectroscopic detection of \textit{B. mallei} and \textit{B. pseudomallei}
\cite{stoeckel2015}. Both are laboratory diagnostic problems; neither addresses geographic or temporal
distribution, and neither produces a population risk estimate. Using published literature as
structured occurrence data has precedent in epidemic intelligence \cite{collier2012,lejeune2015}, but
here event extraction is the primary source of the label rather than a supplementary signal, because
official outbreak records are incomplete for many countries. The label therefore inherits the
reporting biases of the literature, which is analysed rather than assumed away.

\section{Prior Art Audit}

To test the novelty claim rather than assert it, a reproducible set of queries was run against Europe
PMC. Each row of Table~\ref{tab:novelty} is a query count; the query strings and retrieved titles are
retained with the project code.

\begin{table}[htbp]
\centering
\caption{Europe PMC hit counts for combinations of glanders with each data source and method used
in this study.}
\label{tab:novelty}
\small
\begin{tabular}{@{}lc@{}}
\toprule
\textbf{Query} & \textbf{Hits} \\
\midrule
@NOVELTYROWS@
\bottomrule
\end{tabular}
\end{table}

The decisive cells pair glanders with NASA POWER, which returns zero records, and with gradient
boosting, which returns four, none of them a glanders risk model. The nearest prior work is
descriptive cluster detection in Brazil and a risk-factor analysis of the Indian serosurvey.

\section{Research Gap}

The literature divides into three disjoint groups. Epidemiological studies describe where glanders
occurs; machine learning studies of \textit{B. mallei} classify laboratory spectra; veterinary risk
models exist but are built for influenza. No study joins an occurrence corpus, a livestock census,
development indicators and reanalysis climatology into a single panel for glanders, and none
evaluates a calibrated predictive model on that panel.

A second gap appears once the question moves from analysis to use. A probability on a dashboard does
not reach the person who owns the animals, and a risk score without a stated basis is not something a
field officer will act on. Both bodies of literature stop short of the delivery problem: how a
forecast becomes a cited explanation, and how that becomes a message an owner receives and trusts.

The contribution has two parts: a calibrated population-level risk model for glanders, built on data
sources not previously applied to the disease and evaluated under forward temporal and country-holdout
splits; and a decomposition of the delivery problem into three components with fixed contracts, so
prediction, explanation and alert can be built, tested and replaced independently.
"""


# =====================================================================
ARCH = r"""
% =====================================================================
\chapter{System Architecture}
\label{ch:arch}
% =====================================================================

\section{What the Platform Has to Do}

The platform answers one question and produces three outputs: whether glanders is likely to be
documented in an area next period, expressed as a number on a map, an explanation in words, and a
message to an owner. Each is read by a different person, at a different time, through a different
device, and each can fail without the others failing.

That asymmetry is why the system is three components rather than one application. One service serving
all three would tie alert delivery to the latency of an LLM call and make the risk model impossible to
test on its own.

\input{fig_architecture.tex}

\section{Design Principles}

Five rules govern the decomposition. Every later design decision follows from them, and they are
the part of the project that transfers to other diseases.

\textbf{One responsibility per component.} The risk engine turns features into a calibrated
probability, the RAG layer turns a prediction into a cited explanation, and the alert service turns
a prediction into a delivered message. None computes what another could compute instead.

\textbf{Contracts before implementations.} Components exchange versioned schemas, never shared
tables or in-process calls, so each side can be built and tested against a fixture. This is what let
the RAG layer be developed while the alert service was still being written.

\textbf{The core is disease-agnostic.} A disease is a configuration record: which label extractor,
knowledge-base collection, templates and thresholds to use. A second disease is a configuration
change plus a retrain, not a code fork.

\textbf{Fail soft, never fail silent.} A degraded component returns a degraded answer. If the RAG
layer is unavailable the alert still goes out, with the level and standing action text but no
explanation. If retrieval finds nothing above the relevance floor, the layer returns a refusal plus
the model's own SHAP factors. Neither case produces a wrong statement, and neither produces silence.

\textbf{Every output is traceable.} Each prediction carries its model version, each explanation the
document identifiers it was grounded in, each alert the prediction that triggered it and the rule
outcomes that allowed it, so a decision can be reconstructed after the fact.

\section{The Three Components}

\begin{table}[htbp]
\centering
\caption{Component responsibilities, interfaces and failure behaviour.}
\label{tab:components}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.3cm}>{\raggedright\arraybackslash}p{3.5cm}>{\raggedright\arraybackslash}p{3.4cm}>{\raggedright\arraybackslash}p{4.2cm}@{}}
\toprule
\textbf{Component} & \textbf{Responsibility} & \textbf{Interface} & \textbf{On failure} \\
\midrule
ML risk engine & Features to calibrated probability, with attribution & \texttt{POST /v1/predict}, \texttt{GET /v1/risk-map} & \texttt{503} with the champion version id; the last good prediction stays in the table, marked stale. \\
RAG layer & Prediction plus question to a cited explanation & \texttt{POST /v1/explain}, \texttt{POST /v1/chat} & Alert text is sent without the explanation; chat returns a refusal rather than an ungrounded answer. \\
Alert service & Prediction to a delivered, deduplicated message & \texttt{POST /v1/alerts/evaluate}; consumes \texttt{predictions\_ready} & Alerts queue in Redis and drain on recovery; map and explanations are unaffected. \\
\bottomrule
\end{tabular}
\end{table}

\section{Component Contracts}

A contract is a JSON schema plus the guarantees that accompany it. A narrow contract is what makes
a component replaceable, so all three are deliberately small.

The risk engine emits a \texttt{PredictionRecord} with the area, period, calibrated probability,
discrete risk level, model identifier, a data-freshness block and the top SHAP factors. Three
guarantees accompany it: the probability is calibrated on held-out data and may be read as a
frequency; the risk level is derived from that probability by the threshold configuration, so the
two cannot contradict each other; and the top factors come from the model itself, so they remain
available when the RAG layer does not.

The RAG layer takes an \texttt{ExplainRequest}, wrapping a prediction with a question and a
language, and returns an \texttt{ExplainResponse} with an answer, resolved citations, a
\texttt{grounded} flag and a refusal reason. A refusal carries no answer text, so a caller cannot
render one as an explanation.

The alert service emits an \texttt{AlertEvent} with the alert identifier, area, period, current and
previous level, the prediction it derives from, each rule outcome and a recipient count. The
identifier is derived deterministically from its key (Chapter~\ref{ch:alerts}).

The components share a database but not tables: each table has one owning writer and the others
read it, and no component updates another's rows. Spatial columns use PostGIS and document
embeddings use pgvector, so spatial and vector queries run beside the relational joins rather than
in a second store that would need synchronising.

\section{Modularity and Reuse}

The decomposition justifies its overhead only if the parts are reusable. A second disease supplies a
new gazetteer, guidance collection and thresholds, while the modelling code, which never refers to
glanders by name, does not change. A second LLM provider is a configuration value, because the RAG
layer calls a single-method interface. A second channel is an adapter plus a template, and the rules
engine never learns which channel carries the message. The trained pipeline is a scikit-learn
compatible object \cite{pedregosa2011} exported with a manifest, so any Python process can load it
without the API. A replacement model needs no downstream change, since the record carries
\texttt{model\_id} and the registry keeps previous versions.

\section{Deployment and Status}

One Docker Compose file describes the API, worker, PostgreSQL with PostGIS and pgvector, Redis and the
frontend, so local demonstration and server deployment share a structure. A Celery beat job runs the
feature job, then the prediction job, then publishes \texttt{predictions\_ready}, from which
explanations and alerts are computed; a failed explanation never blocks a prediction, and a failed
prediction never sends an alert about stale data.

The report distinguishes throughout between what has been built and what has been specified. The risk
engine is built and evaluated, and every number in Chapter~\ref{ch:results} is reproducible from the
committed scripts. Model serving, the RAG layer and the alert service are specified with fixed
contracts and stated protocols but are not deployed, so no measured performance is reported for them.
"""


# =====================================================================
METHOD = r"""
% =====================================================================
\chapter{Methodology}
\label{ch:method}
% =====================================================================

\section{Data Sources}

Four public sources are used: a literature index, a livestock census, a development indicator set and
a reanalysis climate archive \cite{europepmc,faostat,wdi,power}. None had previously been applied to
glanders risk modelling.

Europe PMC supplies the animal history: @LITRECORDS@ records yielding @LITEVENTS@ occurrence
events. FAOSTAT supplies animal population, 68,449 records covering seven stock series from 1961 to
2023. The World Bank supplies socio-economic context, ten development indicators and country
centroids for 217 countries from 2000 to 2024. NASA POWER supplies environment, six measures of
temperature, precipitation, humidity and wind at @CLIMCOUNT@ centroids from 2005 to 2024.

Extracted events rise in volume after 2015, which reflects growth in open access veterinary
publishing as much as any change in incidence. This is one reason the label is treated as
documented activity throughout.

\section{Panel Construction}

All four sources are keyed on ISO 3166 alpha-3 code and calendar year, so they join once names are
reconciled. FAOSTAT is streamed from its 32\,MB compressed archive and filtered to the seven stock
series rather than loaded whole. Names are matched through \texttt{pycountry} with overrides for forms
such as ``T\"urkiye'' and ``C\^ote d'Ivoire'', and World Bank regional and global aggregates are
excluded by requiring a three-character ISO code, so rows such as ``World'' never enter the panel as
though they were countries.

The grid holds @PANELROWS@ country-year rows across @PANELCOUNTRIES@ countries for 2000 to 2024.
Three restrictions produce the modelling matrix: only equine-holding countries, defined as a maximum
equid stock of at least one thousand; only 2005 to 2023; and only rows with an observable next-year
label. The result has @ROWS@ rows, @FEATURES@ features and @POSITIVES@ positives.

Events are de-duplicated on country, year and source record identifier, so one paper reporting
several cases cannot contribute multiple counts. Missing values are median-imputed inside the training
pipeline, with a missing-indicator feature per affected column, so the test period cannot influence
imputed values. Missingness is low: @MISSFAO@ for FAOSTAT, @MISSWB@ for the World Bank, @MISSNASA@ for
climate, and @MISSALL@ overall, with no column above @MISSMAX@.

\section{Label Definition}

The target is binary: whether a glanders occurrence was documented in country $i$ during year $t+1$.
Occurrence is extracted from Europe PMC by matching, within one sentence, a country name from a
curated gazetteer and a term from an occurrence lexicon (\emph{outbreak}, \emph{case},
\emph{detected}, \emph{seropositive}, \emph{surveillance}). An event is recorded for the year in the
sentence, or the publication year where none is stated. Because the label depends on publication it
is termed \emph{documented activity}: a negative may mean no disease or no report, so the model
predicts surveillance-observable activity rather than biological presence.

\section{Feature Engineering}

Four groups are built from information available at year $t$ or earlier. Seven disease-history
features cover prior-year occurrence, a five-year total, years since the last event, and world and
regional activity shares. Fourteen population features cover log equid and livestock stocks, equid
share, density, growth and species counts. Ten climate features cover temperature, precipitation,
humidity and wind, each with an anomaly against the country's own expanding mean, separating unusual
conditions from latitude. Eleven socio-geographic features cover income, agriculture, GDP, rural
share, connectivity and population, and largely proxy surveillance capacity.

Three derived features need definition. Equid share is horses, asses and mules divided by total farm
animals. Livestock units apply weights of 0.8 for cattle and camels and 0.1 for small ruminants, so
one number expresses grazing pressure across species. Years since the last event uses 99 to denote no
event in the window.

Selection ran in two stages. Columns with mutual information below 0.002 and absolute Spearman
correlation below 0.02 were removed, then one member of each pair correlated at or above 0.90, plus a
column that was exactly the sum of three others, which a tree can construct itself. No projection was
applied: with @FEATURES@ features and @ROWS@ rows the binding constraint is signal rather than
dimensionality, and Section~\ref{sec:ablation} shows reduced sets transfer better.

\section{Models}

Six families are compared. Logistic regression is the additive baseline with balanced class weights.
A single shallow decision tree is included because a non-specialist can read it. Random forest and
extra trees are bagged ensembles \cite{breiman2001}, differing in split randomisation; XGBoost and
LightGBM are boosted ensembles \cite{chen2016,ke2017}. Tuning used grouped cross-validation on
country. Neural networks were excluded: with @POSITIVES@ positives and @FEATURES@ features a network
has more parameters than examples and would memorise the training period.

\section{Evaluation Design}

Three schemes answer different questions. A temporal holdout trains on 2005 to 2017 and tests on 2018
to 2023, with the test period never observed during fitting, which answers whether the model can be
used in following years. Leave-country-out uses five folds grouped by country, so every prediction is
for an unseen country; it answers whether the model transfers and it governs selection, being the
harsher test and the closer approximation of deployment. Repeated stratified cross-validation, five
folds three times, is a stability check.

Precision-recall AUC is the primary metric: at @PREVALENCE@ prevalence ROC-AUC is dominated by the
true-negative mass and overstates performance \cite{saito2015,davis2006}, so it is reported only for
comparability. Brier score and expected calibration error are reported because an uncalibrated
probability cannot support a threshold-based alert \cite{niculescu2005,huang2020}. Precision, recall,
specificity, F1 and the Matthews correlation use a threshold tuned on training data only, with
bootstrap percentile intervals over one thousand resamples. Grouped rather than random splitting is
essential, since a random row split would let the model memorise country identity \cite{roberts2017}.

\section{Leakage Controls}

Six controls apply: features use year $t$ or earlier and only the target uses $t+1$; the split is
chronological; hyperparameters are tuned inside training folds; calibration is fitted on training
folds only; the alert threshold is fixed on training; and imputation values and missing indicators
are generated inside the pipeline.
"""


# =====================================================================
MLOPS = r"""
% =====================================================================
\chapter{MLOps and Model Serving}
\label{ch:mlops}
% =====================================================================

\section{From a Notebook to a Service}

A trained model is not a component until it can be called, versioned, monitored and replaced. Three
things must be true first. The model must be a portable artefact, so the object scored in evaluation
is the object served, with nothing re-fitted in between. Every prediction must name the version that
produced it. And the service must degrade predictably, so a bad release or a missing feature does not
produce confident nonsense. The project is a sequence of numbered scripts, each producing artefacts
consumed by the next, with every intermediate output cached so any stage can be re-run alone. That is
also what makes the pipeline inspectable: a reader can run one stage and check it before trusting the
next.

\section{The Model Bundle}

The unit of deployment is a directory, not a pickled object, because a pickle alone cannot say what
its inputs mean.

\begin{verbatim}
gw-xgb-2026.11.1/
  model.joblib        # fitted pipeline, predict_proba
  manifest.json       # feature order, dtypes, calibration, metrics
  thresholds.json     # level boundaries and hysteresis margin
  SHA256SUMS
\end{verbatim}

The manifest is what makes the bundle reusable. It records the ordered feature list with dtypes, so
serving rejects a request with the wrong columns before any inference happens. It records the
calibration method and achieved error, so a consumer knows whether to read the output as a probability
or only as a rank. It records the evaluation metrics, so the number in the report and the number in
the registry are the same. Because the bundle is a directory with a manifest, the API, a batch job and
a notebook load it with identical behaviour.

Every training run also writes a record with the git commit, data version, feature list and hash,
hyperparameters and the full metric set for all three schemes. Promotion is decided on
leave-country-out precision-recall AUC rather than on the more flattering temporal holdout. A
candidate becomes champion only if it beats the incumbent by more than the bootstrap interval width,
its expected calibration error is below the deployment ceiling of 0.05, its feature schema matches
what serving can supply when checked by name and order, and it has scored a shadow period without a
prediction outside the plausible range. The previous champion is retained, so promotion is reversible,
and a bundle failing its checksum or schema check is replaced by the previous champion rather than
served.

\section{Serving Design}

The interface is deliberately coarse: a caller asks for a prediction for an area and period and
receives the full record, rather than assembling one from several calls.

\begin{table}[htbp]
\centering
\caption{HTTP interface of the risk engine.}
\label{tab:api}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.4cm}>{\raggedright\arraybackslash}p{1.4cm}>{\raggedright\arraybackslash}p{9.2cm}@{}}
\toprule
\textbf{Endpoint} & \textbf{Method} & \textbf{Purpose and contract} \\
\midrule
\texttt{/v1/predict} & POST & Score one area and period from a supplied or stored feature vector. Returns one \texttt{PredictionRecord}. \\
\texttt{/v1/predict/batch} & POST & Score up to 500 area-period pairs, with per-item errors rather than failing the request. \\
\texttt{/v1/risk-map} & GET & GeoJSON of the latest predictions for a period, filtered by risk level. Serves the dashboard directly. \\
\texttt{/v1/models} & GET & Registry listing: model id, promotion date, metrics, feature-schema hash. \\
\texttt{/v1/models/\{id\}} & GET & The manifest of one version, for inspection by a consumer. \\
\texttt{/v1/health} & GET & Liveness and readiness, where readiness checks that a champion bundle is loaded and its schema resolves. \\
\bottomrule
\end{tabular}
\end{table}

Every response carries the \texttt{model\_id} that produced it and a \texttt{data\_freshness} block.
The alert service reads that block before sending anything, so a prediction computed on stale
upstream data cannot produce a message.


The order of operations is a reliability choice. Validation runs first, so a malformed request costs a
schema check rather than a model load. The cache is consulted before
inference because risk maps are read far more often than recomputed. Inference is deterministic for a
fixed bundle, so a cache key of model id, area and period is safe, and the model id is part of the key
rather than a version counter so promotion invalidates the cache. Responses are written back to the
predictions table as well as cached, so the map does not depend on a warm cache.

The endpoint is specified against a budget rather than measured, since the service is not deployed:
40\,ms on a cache miss and 4\,ms on a hit, of which feature retrieval takes 25\,ms and inference 8\,ms.
The explanation endpoint has a separate budget of two seconds because it includes generation, which is
why the alert service never calls it inline. A message must not wait on an LLM.

\section{Monitoring and Retraining}

Three classes of signal are monitored. Service health covers request rate, error rate and latency
percentiles per endpoint on a Prometheus endpoint charted in Grafana, which catches the service being
down, the least interesting failure. Data drift compares each feature's current distribution with the
training distribution using a population stability index and a Kolmogorov-Smirnov statistic, because a
tree asked to extrapolate outside its training range returns a confident answer with no basis.
Prediction drift and calibration decay track the mean predicted probability per period against the
observed event rate as labels arrive: a model that keeps saying 0.2 while the observed rate falls to
0.05 has lost calibration even with its ranking intact.

Retraining follows from the third signal. Recalibrate when the observed-to-predicted ratio leaves a
band for two consecutive periods, and retrain when a new year of labels is available and the champion's
leave-country-out score has degraded beyond the bootstrap interval.

The pipeline runs linting, unit tests and a smoke test on every push. Unit tests cover what can be
checked without data: schema validation, the level-threshold function including hysteresis at the
boundary, idempotency key derivation, and the citation parser. A further test loads the committed
bundle, scores a fixed fixture and asserts the output to four decimals, which catches the most common
silent failure here, where a dependency upgrade changes numerical behaviour and every downstream number
moves unnoticed.

The full computation runs in about @RUNTIMEMIN@ minutes on @HARDWARE@ without a graphics accelerator.
Per-family fitting time at the country-year level ranges from @MINTIME@ seconds for the decision tree
to @MAXTIME@ seconds for LightGBM. One module-level seed governs fitting, cross-validation, bootstrap
resampling and SHAP sampling, with software versions @ENVSPEC@, and the bundle smoke test runs
single-threaded because tree ensembles are not bitwise reproducible across thread counts.
"""


# =====================================================================
RAG = r"""
% =====================================================================
\chapter{The RAG Explanation Layer}
\label{ch:rag}
% =====================================================================

\section{The Problem This Layer Solves}

A calibrated probability of 0.24 is actionable for a veterinary officer and meaningless to an equine
owner. The owner needs to know what happened, what it means for their animals, and what to do next.
The officer needs to know which factors drove the number, because a forecast they cannot interrogate
is a forecast they will not act on.

Asking a large language model is the obvious answer and the obvious hazard. A model asked about
glanders answers from training data that may be outdated, may conflate glanders with melioidosis,
and may invent a treatment protocol. For a zoonosis under statutory control, an invented instruction
is worse than no instruction. Retrieval-augmented generation \cite{lewis2020} changes what the model
may use: it is not asked what it knows, but given a small set of passages from official guidance
plus the prediction's own numbers, and required to answer only from those. Each claim traces to a
passage, and the passage is shown to the reader.

The goal is therefore narrow and testable: an answer a veterinary officer would accept as consistent
with the National Action Plan, and a refusal rather than a guess when the corpus does not support
one.

Fine-tuning would produce fluent text with no citations and no way to tell guidance from the base
model's priors, and it would freeze the knowledge at training time, so a revised plan would require
retraining. Retrieval keeps knowledge in a corpus that a re-ingestion can update, makes every answer
auditable by construction, and allows a refusal path that fine-tuning does not. The cost is latency
and possible retrieval failure, both handled explicitly below.

\section{Knowledge Base}

The corpus is restricted to sources with authority, because the layer's value is that it cites them.
Each document carries an authority tier, used as a tie-breaker during retrieval.

\begin{table}[htbp]
\centering
\caption{Knowledge base, by authority tier.}
\label{tab:corpus}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{5.0cm}>{\raggedright\arraybackslash}p{1.6cm}>{\raggedright\arraybackslash}p{7.0cm}@{}}
\toprule
\textbf{Source} & \textbf{Tier} & \textbf{Use} \\
\midrule
DAHD National Action Plan for Glanders, 2025 \cite{dahd2025} & 1 & Case definitions, surveillance obligations, movement control, quarantine, notification duties. \\
WOAH and WHO disease information sheets & 1 & Disease biology, transmission, zoonotic risk, official status. \\
ICAR and national laboratory guidance & 2 & Diagnostic sampling, laboratory referral. \\
Open-access research papers & 3 & Epidemiology, risk factors, regional situation. \\
\bottomrule
\end{tabular}
\end{table}

Tier 3 may inform an explanation but never overrides tier 1 on a control instruction. When passages
conflict the higher tier wins and the conflict is logged, because a silent contradiction between
sources is exactly the failure this layer exists to prevent.

\section{Ingestion, Embedding and Retrieval}

Ingestion runs offline as a job. A document is parsed, split at section boundaries, and each chunk
is stored with enough metadata to be cited and filtered.

Chunking is section-aware rather than fixed-width, because a fixed window cuts control instructions
in half and lets the model complete a truncated sentence. The splitter respects headings first, then
paragraphs, and falls back to a sliding window only for a section longer than the ceiling. Chunks
target 400 to 700 tokens with 15 per cent overlap inside a section, sections under 80 tokens merge
into the parent, and the retained metadata is document id, title, full section path, page, year and
authority tier. The section path is kept in full, for example
\texttt{NAP-2025 > 5.2 Movement control}, so a citation points to a subsection rather than to a
90-page document.

Chunks are embedded with a compact sentence-transformer \cite{reimers2019} producing 384-dimensional
vectors, cheap enough to embed on a laptop, with a multilingual variant for Hindi because an
English-only embedding degrades on Devanagari. Vectors live in pgvector beside the relational tables,
so re-ingestion and prediction share one transaction boundary. The index is HNSW with cosine distance
\cite{malkov2020}, acceptable because the reranker corrects recall at the head of the list and it keeps
query cost flat as the corpus grows.

\input{fig_rag.tex}

Retrieval is hybrid, because dense and lexical search \cite{robertson2009} fail differently here. A
dense query for ``what should I do if I suspect glanders'' retrieves passages about suspicion, which
helps. A dense query for ``movement control'' may miss a passage using ``restriction of equid
movement'', where a lexical match succeeds; conversely a lexical query for a rare acronym retrieves
noise a dense query ignores. Both lists are retrieved and fused by reciprocal rank fusion
\cite{cormack2009}, which combines rankings without requiring comparable scores:

\[
\mathrm{RRF}(d) = \sum_{i \in \{\text{dense},\text{lexical}\}} \frac{1}{k + \mathrm{rank}_i(d)},
\qquad k = 60
\]

The fused top fifty are reranked by a cross-encoder scoring each passage against the question
jointly. A cross-encoder is far slower per pair than an embedding dot product, which is why it runs
on fifty candidates rather than on the corpus, and the top five become the context.

\begin{table}[htbp]
\centering
\caption{Retrieval parameters.}
\label{tab:retrieval}
\small
\begin{tabular}{@{}lll@{}}
\toprule
\textbf{Stage} & \textbf{Setting} & \textbf{Reason} \\
\midrule
Dense recall & top 30, cosine & Semantic paraphrase coverage \\
Lexical recall & top 30, BM25 & Exact terms, acronyms, section titles \\
Fusion & reciprocal rank, $k=60$ & Scale-free combination of two rankings \\
Rerank & cross-encoder, top 50 to 5 & Precision at the head of the list \\
Relevance floor & rerank score below 0.30 discarded & Prevents padding the context with weak passages \\
\bottomrule
\end{tabular}
\end{table}

The relevance floor drives the refusal path: if fewer than two passages clear it, the layer returns a
refusal with the SHAP factors, because a context built from marginal passages produces a confident
answer built on nothing.

\section{Context, Generation and Guardrails}

The prompt has three parts in fixed order: a system instruction, the retrieved passages with
identifiers, and the structured prediction facts. Those facts make the answer specific to this
forecast rather than to glanders in general, and they are injected as structured data so the model
cannot restate an association as a cause. The system instruction states four constraints: answer only
from the passages, cite every claim, never diagnose an individual animal, and state that the output is
a population-level forecast.

Generation uses temperature 0.1 and a bounded output length. Low temperature is chosen for
consistency rather than caution: two officers asking the same question about the same area should
receive the same instruction. The provider sits behind a single-method interface, so the same
retrieval, grounding and citation code runs against a local Ollama model or a hosted API, and
switching model cannot silently disable the guardrails.

The layer is designed to refuse, and four checks can terminate a response.

\begin{table}[htbp]
\centering
\caption{Guardrails and their failure behaviour.}
\label{tab:guardrails}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.0cm}>{\raggedright\arraybackslash}p{5.2cm}>{\raggedright\arraybackslash}p{5.4cm}@{}}
\toprule
\textbf{Check} & \textbf{What it verifies} & \textbf{On failure} \\
\midrule
Retrieval floor & At least two passages above the relevance threshold & Refusal with the top SHAP factors, which need no retrieval \\
Citation resolution & Every cited identifier exists in the retrieved set & Answer rejected and regenerated once, then refusal \\
Diagnosis scope & No individual-animal diagnosis or treatment prescription & Response rewritten without the clinical claim, and the attempt logged \\
Out-of-scope & Question is about glanders control, not unrelated topics & Refusal stating what the layer covers \\
\bottomrule
\end{tabular}
\end{table}

The citation check is mechanical. The answer is parsed for identifiers and each is looked up in the
retrieved set; one that does not resolve means the model cited a document it was not given, which is a
hallucination whether or not the sentence is true. Asking a model to be accurate is not a control;
checking its output is.

\section{Evaluation}

Four quantities are measured, none of them whether the prose reads well. Retrieval quality is
recall@5 and mean reciprocal rank on a hand-built question set, which isolates retrieval from
generation, since no generation quality helps if the right passage is never retrieved. Faithfulness
is whether each claim is supported by the retrieved context, scored by a judge model and reviewed
by hand on a sample; this catches a model that cites a passage but says something it does not say.
Citation precision is the fraction of citations resolving to a passage that supports the sentence,
which is distinct from resolution, since resolution only checks existence. Refusal
behaviour is the refusal rate on out-of-scope questions and the false refusal rate in scope: a layer
that never refuses is unsafe and one that always refuses is useless, so both are reported.

Because the layer is specified rather than deployed, the validation that would precede deployment is
stated so the claim is falsifiable: recall@5 above 0.85, faithfulness above 0.90 on 100 manually
reviewed answers, citation precision above 0.95, zero individual-animal diagnoses on an adversarial
probe set, refusal on every out-of-scope question with a false refusal rate below 10 per cent, and
p95 latency under two seconds. These are targets, not results.
"""


# =====================================================================
ALERT = r"""
% =====================================================================
\chapter{The Alert Service}
\label{ch:alerts}
% =====================================================================

\section{Why the Alert Is the Hard Part}

The risk engine produces a probability and the RAG layer explains it, but neither reaches the person
who owns the animals, whose only interaction is a message on a phone competing with everything else
on it. The design problem is therefore not how to send a message but how to send few enough that the
ones which arrive are read. A system that warns about every area every month trains its users to
ignore it, then fails silently at the moment it was built for.

The service is event-driven: the prediction job publishes \texttt{predictions\_ready} and the evaluator
consumes it, so an alert cannot be sent for a period whose predictions were not recomputed. For each
subscribed area the evaluator reads the new prediction and the previous alert state, and those two
values are the entire input to the rules. It reads no features or model internals, so a model change
can affect alert behaviour only through the probability it produces.

\section{Rule 1: Threshold with Hysteresis}

The calibrated probability maps to three levels. The boundaries are configuration values derived
from the operating curve in Chapter~\ref{ch:results}, not defaults and not 0.5.

\begin{table}[htbp]
\centering
\caption{Level thresholds and their basis.}
\label{tab:thresholds}
\small
\begin{tabular}{@{}p{1.6cm}p{2.6cm}p{5.4cm}p{3.4cm}@{}}
\toprule
\textbf{Level} & \textbf{Band} & \textbf{Meaning for the recipient} & \textbf{Basis} \\
\midrule
LOW & below the medium boundary & No message. Routine monitoring. & Below the budget where precision collapses \\
MEDIUM & medium to high boundary & Prepare; check animals; note the veterinary contact & Operating point where recall exceeds 80 per cent \\
HIGH & above the high boundary & Act: restrict movement, isolate suspects, inform the authority & Top of the operating curve, precision above 0.5 \\
\bottomrule
\end{tabular}
\end{table}

Hysteresis addresses a specific defect. With a single boundary, an area whose probability oscillates
around the threshold produces an alert every period, because each crossing is a state change. Two
boundaries are therefore used: an area enters HIGH at the high threshold and leaves only when the
probability falls below that threshold minus a margin.

\[
\text{enter HIGH at } p \ge T_H, \qquad
\text{leave HIGH only at } p < T_H - \delta, \qquad \delta = 0.05
\]

The margin is configurable per disease. A larger margin gives a more stable state at the cost of
slower de-escalation, which suits a disease where a missed warning costs more than a late all-clear.

\section{Rule 2: Suppression}

Suppression decides whether a message is warranted at all, given that the level has changed. Six
conditions apply and any one can stop the message.

\begin{table}[htbp]
\centering
\caption{Suppression conditions.}
\label{tab:suppression}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.0cm}>{\raggedright\arraybackslash}p{5.2cm}>{\raggedright\arraybackslash}p{5.4cm}@{}}
\toprule
\textbf{Condition} & \textbf{Rule} & \textbf{Rationale} \\
\midrule
State change & Send only on a transition, not while the level is held & A monthly reminder at the same level carries no new information \\
Cooldown & No repeat of the same level within a configurable window & Prevents oscillation at a boundary from producing repeated messages \\
Escalation bypass & An upward transition ignores the cooldown & A worsening must never be delayed by a timer \\
Per-user daily cap & At most one message per recipient per day & Protects against several areas escalating at once \\
Quiet hours & Nothing sent between 21:00 and 07:00 local; queued instead & A warning that wakes a household at night is resented, and is not actionable then \\
Stale-data guard & No send if \texttt{data\_freshness.passes} is false & An alert about a prediction computed on stale inputs is worse than no alert \\
\bottomrule
\end{tabular}
\end{table}

A manual mute per area lets an officer silence a zone under active surveillance without disabling the
service. De-escalation is separate: when a level falls, an optional short all-clear is sent, since a
recipient told to act needs to be told when to stop. Sending it is a configuration choice, because an
all-clear costs a message but prevents a restriction being maintained indefinitely.

\section{Rule 3: Deduplication}

The service must be safe to re-run: jobs are retried, deployments restart workers, and a model may be
re-scored for the same period, and none may produce a second message. Deduplication is enforced at
three levels, each with its own key and database constraint.

\begin{table}[htbp]
\centering
\caption{Deduplication levels.}
\label{tab:dedup}
\small
\begin{tabular}{@{}p{1.4cm}p{4.6cm}p{7.4cm}@{}}
\toprule
\textbf{Level} & \textbf{Key} & \textbf{What it prevents} \\
\midrule
Alert & \texttt{(area\_id, period, level)} & A re-run of the job creating a second alert for the same period \\
Recipient & \texttt{(alert\_id, subscription\_id)} & One subscriber receiving the same alert through two fan-out passes \\
Send & \texttt{(alert\_id, subscription\_id, attempt)} & A retry after a timeout delivering a message that had in fact succeeded \\
\bottomrule
\end{tabular}
\end{table}

The first two are unique database constraints, so protection does not depend on application logic
being correct. The alert identifier is derived deterministically from its key rather than at random,
so two concurrent workers computing the same alert arrive at the same identifier and one loses the
insert. The send-level check reads the delivery log before each attempt, handling the case where a
provider accepts a message, the response times out, and the retry would deliver it twice.

\section{Fan-Out, Channels and Delivery}

Once an alert record exists, one delivery job per subscription is queued through Redis. A channel
adapter receives a rendered message and a recipient and returns a delivery status, with adapters for
SMS, WhatsApp and Telegram, the last used for demonstration because it needs no commercial
onboarding. Retries use exponential backoff with jitter: a permanent failure such as an invalid number
is not retried, a transient one such as a provider timeout is, and the distinction is logged, because
a silent permanent failure leaves a subscriber who believes they are covered and is not. Templates are
separate from the rules engine, so adding a language adds a template set rather than touching the
rules.

The same alert through a richer channel carries the explanation paragraph from the RAG layer with its
citations. The rule that decides whether to send is identical; only the adapter and template differ,
which is what lets one alert serve a feature phone and a smartphone without duplicating the decision
logic.

\section{Evaluation of the Alert Layer}

The service is evaluated as a warning system, not as a messaging system. Alert precision is the
fraction of HIGH area-periods followed by a documented event, and it determines whether recipients
trust the message. Event coverage at budget is the operating curve already reported in
Chapter~\ref{ch:results}, and the thresholds are read from it. Noise per recipient is messages per
subscriber per year, which predicts whether the service will still be read in its second year.
Delivery reliability is the fraction of queued deliveries reaching a terminal success state within
the retry window, reported per channel. The first two come from historical predictions and labels;
the last two need a deployed service and are stated as the protocol that would measure them.
"""


# =====================================================================
RESULTS = r"""
% =====================================================================
\chapter{Results and Discussion}
\label{ch:results}
% =====================================================================

\section{Dataset Characteristics}

The modelling matrix holds @ROWS@ country-year observations, of which @POSITIVES@ are positive: a
prevalence of @PREVALENCE@ and an imbalance of @IMBALANCE@ to one. @POSCOUNTRIES@ of @COUNTRIES@
countries record at least one positive, @REPEATPOS@ of them in two or more years, and the top five
hold @TOP5SHARE@ of all positives. The imbalance rules out accuracy as a metric and motivates
precision-recall analysis; the persistence justifies historical features; and the concentration is
the first indication that the label tracks reporting capacity, since those countries operate
reference laboratories.

\section{Model Comparison}

Table~\ref{tab:level1} reports discrimination under all three schemes.

\begin{table}[htbp]
\centering
\caption{Discrimination at the country-year level. Brackets give 95 per cent bootstrap intervals
on the temporal holdout.}
\label{tab:level1}
\small
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lcccccccc@{}}
\toprule
\textbf{Model} & \textbf{PR-AUC} & \textbf{95\% CI} & \textbf{ROC-AUC} &
\textbf{PR-AUC} & \textbf{PR-AUC} & \textbf{Brier} & \textbf{Prec.} & \textbf{Rec.} \\
 & \textbf{(time)} & \textbf{on PR-AUC} & \textbf{(time)} & \textbf{(country)} &
\textbf{(rep.\ CV)} & & & \\
\midrule
@LEVEL1ROWS@
\bottomrule
\end{tabular}}
\end{table}

Against a base rate of @PREVALENCE@, the strongest temporal result of @BESTPR@ is an approximately
@LIFT@-fold lift. Every tree-based model beats the logistic baseline, and the single decision tree is
weakest, which indicates that the relationships are interactive rather than additive. The more
important pattern is the decline under leave-country-out validation: for Random Forest the score falls
from @RFPR@ to @RFLOCOR@, and the decline exceeds the bootstrap interval width for every family. That
is the signature of learning country-specific structure, and the estimate to quote for deployment.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig03_roc_pr_curves.png}
\caption{ROC curves (panel A) and precision-recall curves (panel B) on the temporal holdout. At this
prevalence the ROC panels compress into a narrow band while the precision-recall panels separate the
families.}
\label{fig:curves}
\end{figure}

\section{Calibration}

Predictions are well calibrated, with an expected calibration error of @ECE@ and a Brier score of
@BRIER@: a stated risk of twenty-four per cent corresponds to an observed frequency near twenty-four
per cent. That is what makes a threshold-based alert defensible, since a message quoting a probability
must be numerically trustworthy.

\section{Ablation}
\label{sec:ablation}

Feature groups were removed and each configuration retrained (Table~\ref{tab:ablation}).

\begin{table}[htbp]
\centering
\caption{Ablation settings, using XGBoost with fixed hyperparameters.}
\label{tab:ablation}
\small
\begin{tabular}{@{}lccc@{}}
\toprule
\textbf{Feature set} & \textbf{Columns} & \textbf{PR-AUC (time)} & \textbf{PR-AUC (country)} \\
\midrule
@ABLATIONROWS@
\bottomrule
\end{tabular}
\end{table}

Two results matter more than the headline. The reduced set of @AS5K@ columns reaches @AS5LOCO@ under
leave-country-out validation, against @AS6LOCO@ for the full @AS6K@: added covariates improve
in-distribution fit and reduce transfer by letting the model fit country peculiarities. Climate alone
reaches @AS3LOCO@, marginally above the @PREVALENCE@ floor, so annual country climatology largely
encodes latitude and therefore country identity. Adding research-output proxies moves the
leave-country-out score by @AS7DELTA@, weak evidence against pure publication tracking but not
proof.

\section{Chained Pipeline}

Table~\ref{tab:chain} reports the effect of appending the stage-one population forecast.

\begin{table}[htbp]
\centering
\caption{Effect of chaining the population forecast into the occurrence model.}
\label{tab:chain}
\small
\begin{tabular}{@{}lccc@{}}
\toprule
\textbf{Variant} & \textbf{PR-AUC (time)} & \textbf{ROC-AUC (time)} & \textbf{PR-AUC (country)} \\
\midrule
@CHAINROWS@
\bottomrule
\end{tabular}
\end{table}

The population forecast performs well as a forecast, with a mean absolute error of @S1MAE@ on the log
scale and a Spearman correlation of @S1RHO@. The intensity stage is weaker but usable, at a mean
absolute error of @S3MAE@ and a rank correlation of @S3RHO@ among positive observations. The hurdle
product ranks expected annual burden with a Spearman correlation of @HZRHO@, and its highest decile
captures @HZEVENTS@ of @HZTOTAL@ observed events.

Appending the forecast changes temporal PR-AUC by @CHAINDELTA@, inside the noise band. The cause is
structural: population magnitude is already a direct feature, so forecasting it supplies a less
accurate copy of what the model holds. Chaining should help where that quantity cannot be observed
directly, which is not the case here.

\section{Alert Economics}

As a warning system, alerting the six per cent of country-years at highest predicted risk captures
about half of all observed events, and twenty-eight per cent captures eighty per cent
(Figure~\ref{fig:alerts}). Uniform alerting would need full coverage for the same recall, so the model
is roughly eight times more efficient than arbitrary selection at the fifty per cent point.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.78\textwidth]{fig07_alert_budget.png}
\caption{Alert economics. Panel A gives the fraction of events captured as the alert budget grows,
against random alerting. Panel B gives the alert volume required to reach a target recall.}
\label{fig:alerts}
\end{figure}

\section{Subgroup Analysis}

Table~\ref{tab:subgroup} reports leave-country-out performance by region. Skill is lowest in
Sub-Saharan Africa and in low-income countries, where early warning would help most. The cause is
label sparsity rather than a model defect: few events are recorded in those strata to learn from.

\begin{table}[htbp]
\centering
\caption{Leave-country-out performance by World Bank region.}
\label{tab:subgroup}
\small
\begin{tabular}{@{}lcccc@{}}
\toprule
\textbf{Region} & \textbf{Observations} & \textbf{Events} & \textbf{ROC-AUC} & \textbf{PR-AUC} \\
\midrule
@SUBGROUPROWS@
\bottomrule
\end{tabular}
\end{table}

\section{Discussion}

The model has predictive skill: a precision-recall AUC of @BESTPR@ against a base rate of
@PREVALENCE@ is not explainable by chance, survives a forward-looking split, and is calibrated to
within two points. It does not transfer intact, though: leave-country-out performance is roughly forty
per cent lower, and that is the planning figure, so a new country needs local validation first.

The principal signal is surveillance rather than biology, and three analyses agree: the highest
features are population and connectivity measures, the label concentrates in countries with reference
laboratories, and the best-scoring cells are India, the United States and Australia. Climate,
treated as a primary input in the proposal, transfers poorly here. Simpler models transfer better too,
which argues for parsimony when positives are few.
"""


# =====================================================================
CONCL = r"""
% =====================================================================
\chapter{Conclusion and Future Work}
\label{ch:concl}
% =====================================================================

\section{Conclusion}

This project set out to build a usable warning system for glanders: to establish whether
population-level risk could be predicted from public data, and to design how a prediction reaches the
person who owns the animals. Four sources not previously applied to the disease formed a country-year
panel across 162 equine-holding countries, six model families were trained under three validation
schemes, and a three-stage chained pipeline was tested. Around the model, delivery was decomposed into
three components with fixed contracts: a risk engine, a retrieval-augmented explanation layer and an
alert service.

Prediction is possible, and the performance is moderate. On a forward-looking temporal holdout the
strongest model reaches a precision-recall AUC of @BESTPR@ against a base rate of @PREVALENCE@, an
approximately @LIFT@-fold lift, with a calibration error of @ECE@, capturing half of all observed
events while alerting six per cent of country-years. The skill is fragile across geography, though:
leave-country-out performance is about forty per cent lower, and the decline concentrates where early
warning would help most.

What the model learns is less encouraging. Three analyses converge: the highest-ranked features are
population size and reporting capacity rather than biological drivers, the label concentrates in
countries operating reference laboratories, and the best-scoring cells have the strongest publishing
record. It predicts where glanders will be documented, not where the organism is present. The chained
design does not improve discrimination because the intermediate quantity is already a direct feature.

The decomposition also proved useful: three components with versioned contracts, none hardcoding the
disease, were each testable alone, so the risk engine could be evaluated before any explanation
existed and the alert rules checked against a policy before any message was sent.

\section{Future Work}

\textbf{Reported activity.} The most important extension is to model surveillance capacity as a
quantity, as an offset on publication volume or through a two-part model estimating detection and
occurrence jointly; otherwise gains in score reflect reporting rather than disease.

\textbf{The label extractor.} The 263 extracted events have not been checked against a hand-annotated
set; annotating a stratified sample would give the extractor's own precision and recall, bounding
label noise that propagates downstream.

\textbf{Resolution.} The proposal envisaged district-month resolution for India; public district
covariates would need assembling, but that resolution matches the scale at which control is applied.

\textbf{The unmeasured components.} The calibration here is one point estimate; production needs
drift monitoring and a retraining trigger. The RAG layer's retrieval, guardrail and protocol targets
are specified but unmeasured, and running it against the corpus would give recall@5, faithfulness,
citation precision and the false refusal rate. \textbf{The field.} Messages per subscriber per year
decides whether the service survives a second year; a district pilot would supply it. A WOAH WAHIS
record set \cite{wahis} would validate the literature-derived label where the two overlap, and a
cost-sensitive threshold would match the operating point to the programme's priorities.
"""
