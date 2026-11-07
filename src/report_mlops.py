"""Chapter 5: MLOps and model serving."""

BODY_MLOPS = r"""
% =====================================================================
\chapter{MLOps and Model Serving}
\label{ch:mlops}
% =====================================================================

\section{From a Notebook Model to a Service}

A trained model is not a component until it can be called, versioned, monitored and replaced. The
gap between the two is what this chapter addresses. Three things have to be true before the risk
engine can be called a service.

The model has to be a portable artefact, so that the exact object scored in evaluation is the
object served in production, with nothing re-fitted in between.

Every prediction has to name the version that produced it, so that a decision can be explained
months later and a regression can be traced to a release.

The service has to degrade predictably, so that a bad model release or a missing feature does not
produce confident nonsense.

\section{Software Layout}

The project is a sequence of numbered scripts, each producing artefacts consumed by the next. All
intermediate outputs are cached, so any stage can be re-run without repeating the stages before it.
This layout is also what makes the pipeline inspectable: a reader can run one stage and check it
before trusting the next.

\begin{table}[htbp]
\centering
\caption{Processing stages and their outputs.}
\label{tab:stages}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{4.3cm}>{\raggedright\arraybackslash}p{4.0cm}>{\raggedright\arraybackslash}p{6.2cm}@{}}
\toprule
\textbf{Script} & \textbf{Stage} & \textbf{Output} \\
\midrule
\texttt{00\_novelty\_audit} & Prior art audit & Query counts and retrieved titles \\
\texttt{01\_fetch\_data} & Ingestion & Europe PMC, World Bank and NASA POWER payloads \\
\texttt{01c\_extract\_faostat} & Ingestion & Seven FAOSTAT stock series \\
\texttt{02\_build\_panel} & Assembly & Panel, extracted events and audit block \\
\texttt{03\_train\_evaluate} & Modelling & Metrics, predictions and model comparison \\
\texttt{05\_dataset\_analysis} & Analysis & Association, redundancy and selection statistics \\
\texttt{04\_report}, \texttt{06\_analysis\_figures} & Reporting & Figures and summary tables \\
\texttt{09\_make\_full\_report} & Reporting & This document \\
\bottomrule
\end{tabular}
\end{table}

\section{Training Pipeline}

Figure~\ref{fig:trainflow} shows the training sequence. The split is applied before any model
sees data, so the test years cannot influence fitting, tuning, calibration or threshold selection.

@TRAININGFIG@

Figure~\ref{fig:evalflow} shows the corresponding evaluation sequence. One trained model is
scored under three schemes, each answering a different question, and the metrics are summarised
with bootstrap intervals rather than as point estimates.

@EVALFIG@

Two properties of this sequence are worth stating because they are commonly violated. Feature
scaling and imputation are fitted inside each cross-validation fold, not on the full matrix, so no
information leaks from a validation fold into training. The probability calibrator is fitted on a
held-out slice of the training period, never on the test period, so the reported calibration error
is not circular.

\section{Experiment Tracking and the Model Registry}

Every training run writes a record containing the git commit, the data version, the feature list
and hash, the hyperparameters, and the full metric set for all three validation schemes. Runs are
compared on leave-country-out precision-recall AUC, the metric that governs promotion, rather than
on the temporal holdout that is more flattering.

A model is promoted from candidate to champion only if it satisfies four conditions:

\begin{enumerate}
  \item Its leave-country-out PR-AUC exceeds the incumbent's by more than the bootstrap interval width,
        so the improvement is not noise.
  \item Its expected calibration error is below the deployment ceiling, currently 0.05.
  \item Its feature schema matches what the serving environment can supply, checked by name and
        order rather than by position.
  \item It has been scored on a shadow period without producing a prediction outside the
        plausible range.
\end{enumerate}

The registry keeps the previous champion, so promotion is reversible. This is the mechanism
behind the fail-soft guarantee in Chapter~\ref{ch:arch}: a bundle that fails its checksum or its
schema check is replaced by the previous champion instead of being served.

\section{The Model Bundle}

The unit of deployment is a directory, not a pickled object, because a pickle alone cannot say
what its inputs mean.

\begin{verbatim}
gw-xgb-2026.11.1/
  model.joblib        # fitted pipeline, predict_proba
  manifest.json       # feature order, dtypes, calibration, metrics
  thresholds.json     # level boundaries and hysteresis margin
  SHA256SUMS
\end{verbatim}

The manifest is the part that makes the bundle reusable. It records the ordered feature list with
dtypes, so the serving layer can reject a request that supplies the wrong columns before any
inference happens. It records the calibration method and the achieved expected calibration error,
so a consumer knows whether to read the output as a probability or only as a rank. It records the
metrics from evaluation, so the number in the report and the number in the registry are the same
number.

Because the bundle is a directory with a manifest, it can be loaded by the API, by a batch job, or
by a notebook, with identical behaviour. That is the practical meaning of reusability here.

\section{Serving Design}

The service exposes a small REST interface. The endpoints are deliberately coarse: a caller asks
for a prediction for an area and period, and receives the full record, rather than assembling a
prediction from several calls.

\begin{table}[htbp]
\centering
\caption{HTTP interface of the risk engine.}
\label{tab:api}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.6cm}>{\raggedright\arraybackslash}p{1.5cm}>{\raggedright\arraybackslash}p{9.2cm}@{}}
\toprule
\textbf{Endpoint} & \textbf{Method} & \textbf{Purpose and contract} \\
\midrule
\texttt{/v1/predict} & POST & Score one area and period. Body supplies \texttt{area\_id}, \texttt{period} and either a feature vector or a flag to read stored features. Returns one \texttt{PredictionRecord}. \\
\texttt{/v1/predict/batch} & POST & Score up to 500 area-period pairs. Returns a list, with per-item errors rather than failing the request. \\
\texttt{/v1/risk-map} & GET & GeoJSON of the latest predictions for a period, filtered by risk level. Serves the dashboard directly. \\
\texttt{/v1/models} & GET & Registry listing: model id, promotion date, metrics, feature-schema hash. \\
\texttt{/v1/models/\{id\}} & GET & The manifest of one version, so a consumer can inspect what it is being served. \\
\texttt{/v1/health} & GET & Liveness plus readiness, where readiness checks that a champion bundle is loaded and its feature schema resolves. \\
\bottomrule
\end{tabular}
\end{table}

Every response carries the \texttt{model\_id} that produced it and a \texttt{data\_freshness} block.
The freshness block is not decoration: the alert service reads it before sending anything, so a
prediction computed on stale upstream data cannot produce a message.

\input{fig_serving.tex}

\section{Request Lifecycle}

The order of operations in Figure~\ref{fig:serving} is a reliability choice, not an optimisation.
Validation runs first so a malformed request costs a schema check rather than a model load. The
cache is consulted before inference because risk maps are read far more often than they are
recomputed, and the same area-period is requested repeatedly during a dashboard session.

Inference itself is deterministic for a fixed bundle, so a cache key of model id, area and period
is safe: the same inputs always produce the same output. The cache is invalidated when a new
champion is promoted, which is why the model id is part of the key rather than a version counter.

The response is written back to the predictions table as well as cached, so the read path for the
map does not depend on the cache being warm.

\section{Latency Budget}

The endpoint is specified against a budget rather than measured, since the service is not
deployed. The budget is set so that a full risk map for one period is interactive.

\begin{table}[htbp]
\centering
\caption{Target latency for a single prediction request.}
\label{tab:latency}
\small
\begin{tabular}{@{}lrl@{}}
\toprule
\textbf{Stage} & \textbf{Target} & \textbf{Note} \\
\midrule
Schema and range validation & 2 ms & Rejects malformed input before any I/O \\
Cache lookup & 3 ms & Redis, keyed on model, area, period \\
Feature retrieval & 25 ms & Indexed PostGIS and relational joins \\
Model inference & 8 ms & A single row through a tree ensemble \\
Calibration and record assembly & 2 ms & Isotonic lookup plus rounding \\
\midrule
Total, cache miss & 40 ms & \\
Total, cache hit & 4 ms & \\
\bottomrule
\end{tabular}
\end{table}

The explanation endpoint has a different budget, two seconds, because it includes a generation
step. That is why the alert service does not call it inline: a message must not wait on an LLM.

\section{Monitoring}

Three classes of signal are monitored, and they catch different failures.

\textbf{Service health.} Request rate, error rate and latency percentiles per endpoint, exposed on
a Prometheus endpoint and charted in Grafana. This catches the service being down or slow, which
is the least interesting failure.

\textbf{Data drift.} For each feature, the distribution in the current period is compared with the
training distribution using a population stability index and a Kolmogorov-Smirnov statistic. A
feature that drifts beyond its alerting band is reported, because a tree model asked to
extrapolate outside its training range produces a confident answer with no basis.

\textbf{Prediction drift and calibration decay.} The mean predicted probability per period is
tracked against the observed event rate as labels arrive. A model that keeps saying 0.2 while the
observed rate falls to 0.05 has lost calibration even if its ranking is intact, and the threshold
configuration must be revisited before the alerts it drives become wrong.

The retraining trigger follows from the third signal: recalibrate when the observed-to-predicted
ratio leaves a band for two consecutive periods, and retrain when a new year of labels is
available and the champion's leave-country-out score has degraded beyond the bootstrap interval.

\section{Continuous Integration}

The pipeline runs linting, unit tests and a smoke test on every push. The unit tests cover the
parts that can be checked without data: schema validation, the level-threshold function including
hysteresis behaviour at the boundary, the idempotency key derivation, and the citation parser.

A further test checks the model bundle itself. It loads the committed bundle, scores a fixed
fixture, and asserts that the output matches a recorded value to four decimals. This catches the
most common silent failure in a project of this kind, where a dependency upgrade changes
numerical behaviour and every downstream number moves without anyone noticing.

\section{Reproducibility}

The full computation runs in approximately @RUNTIMEMIN@ minutes on a laptop processor without a
graphics accelerator, using @HARDWARE@. Per-family fitting time at the country-year level ranges
from @MINTIME@ seconds for the decision tree to @MAXTIME@ seconds for LightGBM.

A single module-level seed governs model fitting, cross-validation splitting, bootstrap resampling
and SHAP sampling. Software versions are @ENVSPEC@. Raw payloads are cached under
\texttt{data/raw} and the derived panel is written to \texttt{data/processed}, so every reported
number can be regenerated without re-downloading upstream sources.

One determinism caveat applies. Tree ensembles are seeded but not bitwise reproducible across
different thread counts, so parallel execution may change the final decimal of an ensemble score.
The bundle smoke test described above is run single-threaded for exactly this reason.
"""
