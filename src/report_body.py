"""Chapters 3-6 of the full technical report (methodology, implementation, results, conclusion)."""

BODY_METHOD = r"""
% =====================================================================
\chapter{Methodology}
\label{ch:method}
% =====================================================================

\section{Data Sources}

Four publicly accessible sources are used: a literature index, a livestock census, a development
indicator set and a reanalysis climate archive \cite{europepmc,faostat,wdi,power}. None had
previously been applied to glanders risk modelling, and each contributes a distinct kind of
evidence.

\begin{table}[htbp]
\centering
\caption{Data sources and their role in the panel.}
\label{tab:sources}
\small
\begin{tabular}{@{}p{2.9cm}p{2.7cm}p{4.3cm}p{3.4cm}@{}}
\toprule
\textbf{Source} & \textbf{Role} & \textbf{Content} & \textbf{Coverage} \\
\midrule
Europe PMC & Animal history & Occurrence events extracted from abstracts & @LITRECORDS@ records, @LITEVENTS@ events \\
FAOSTAT & Animal population & Stocks of horses, asses, mules, camels, cattle, sheep and goats & 68,449 records, 1961--2023 \\
World Bank & Socio-economic context & Ten development indicators and country centroids & 217 countries, 2000--2024 \\
NASA POWER & Environment & Temperature, precipitation, humidity and wind & Six measures, @CLIMCOUNT@ centroids, 2005--2024 \\
\bottomrule
\end{tabular}
\end{table}

Figure~\ref{fig:coverage} shows the distribution of the extracted occurrence events by year and
by country. The volume of recorded activity rises after 2015, which reflects growth in open
access veterinary publishing as much as any change in disease incidence. This is one reason the
label is treated as documented activity throughout.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig01_dataset_coverage.png}
\caption{Occurrence events extracted from Europe PMC. Panel A gives the annual count. Panel B
gives the distribution across the most frequently reporting countries on a logarithmic scale.}
\label{fig:coverage}
\end{figure}

\section{Panel Construction}

All four sources are keyed on ISO 3166 alpha-3 country code and calendar year, so they join
without ambiguity once names are reconciled. FAOSTAT is streamed from the 32\,MB compressed bulk
archive, which expands to approximately 545\,MB, and filtered to the seven stock series of
interest rather than loaded into memory.

Country names are matched to ISO-3 through \texttt{pycountry} with explicit overrides for
non-standard forms such as ``T\"urkiye'', ``Viet Nam'' and ``C\^ote d'Ivoire''. World Bank
regional and global aggregates are excluded by requiring a three-character ISO code, which
prevents rows such as ``World'' or ``South Asia'' from entering the panel as if they were
countries.

Combining the four sources produces a grid of @PANELROWS@ country-year rows across
@PANELCOUNTRIES@ countries for 2000 to 2024, in 60 columns: 44 engineered candidate features, three
identifiers, five label fields and eight intermediate quantities from which the features are derived.

Preprocessing reduces that grid to @ROWS@ rows, and feature selection then keeps @SELN@ of the 44
candidates, which is the matrix every model in this report was trained and evaluated on. The row loss
comes from two restrictions: the equine-holding filter, which keeps 162 of the @PANELCOUNTRIES@
countries on a maximum equid stock of at least one thousand animals, and the 2005 to 2023 year window.
The third restriction, an observable next-year label, then removes no further rows.

The exported file is therefore @ROWS@ rows by @SELN@ feature columns, plus the target column.

\section{Preprocessing}

\subsection{Duplicate Removal}

Extracted events are de-duplicated on the composite key of country, year and source record
identifier. Without this step a single paper reporting several cases would contribute multiple
counts and inflate the occurrence signal.

\subsection{Missing Values}

Missing numeric values are imputed with the column median, and every column that required
imputation keeps a binary missing-indicator feature so that absence is represented rather than
silently filled. Imputation is fitted inside the training pipeline, so the test period cannot
influence imputed values. Missingness is low: @MISSFAO@ in the FAOSTAT block, @MISSWB@ in the
World Bank block, @MISSNASA@ in the climate block, and @MISSALL@ overall, with no column
exceeding @MISSMAX@.

\subsection{Treatment of Absence}

A country-year is assigned a negative label only after the country passes the equine-stock
filter. This prevents a country with no recorded equids from contributing an uninformative
negative observation, and ensures that a blank is never read as proof that disease was absent.

\section{Label Definition}

The prediction target is binary: whether a glanders occurrence was documented in country $i$
during year $t+1$. Occurrence is extracted from Europe PMC by matching, within a single sentence,
a country name from a curated gazetteer and a term from an occurrence lexicon containing
\emph{outbreak}, \emph{case}, \emph{detected}, \emph{seropositive} and \emph{surveillance}. When
both are present, an event is recorded for the year stated in the sentence, or the publication
year where no year is stated.

Because the label depends on publication it is termed \emph{documented activity} throughout. A
negative value may indicate either the absence of disease or the absence of a report, and the
model is therefore interpreted as a predictor of surveillance-observable activity.

\section{Feature Engineering}

Four groups of features are constructed, all using information available at time $t$ or earlier.

\begin{table}[htbp]
\centering
\caption{Feature groups, sizes and rationale.}
\label{tab:features}
\small
\begin{tabular}{@{}p{2.7cm}cp{9.6cm}@{}}
\toprule
\textbf{Group} & \textbf{Count} & \textbf{Content and rationale} \\
\midrule
Disease history & 7 & Occurrence in the two prior years, a five-year running total, years since the last event, and contemporaneous world and regional activity shares. The disease persists in an area once introduced. \\
Animal population & 14 & Log equid and total livestock stocks, equid share of farm animals, equid density, one- and three-year growth, and the seven species counts. A larger susceptible population offers more opportunity for detection. \\
Climate & 10 & Mean, maximum and minimum temperature, precipitation total and coefficient of variation, relative humidity and wind, each paired with an anomaly computed against the country's own expanding mean. The anomaly separates unusual conditions from latitude. \\
Socio-geography & 11 & Income band, agricultural land share, agricultural value added, livestock production index, GDP per capita, rural share, internet penetration, fertiliser intensity, life expectancy, population and density. These largely proxy surveillance capacity. \\
\bottomrule
\end{tabular}
\end{table}

Three derived features require definition. Equid share is the sum of horses, asses and mules
divided by total farm animals. Livestock units apply metabolic weights, with cattle and camels at
0.8 and small ruminants at 0.1, so that one number expresses grazing pressure across species.
Years since the last event uses the value 99 to denote no recorded event within the panel window.

\section{Statistical Association Measures}
\label{sec:assoc}

Feature screening uses four measures. Each is computed by a standard library routine rather than a
handwritten implementation, and the versions are recorded with the run environment
(Section~\ref{ch:mlops}). Let $y \in \{0,1\}$ be the next-year label, $x$ a numeric feature, and $n$
the number of rows where both are present.

\textbf{Spearman's rank correlation} (\texttt{scipy.stats.spearmanr}) measures monotone association
without assuming linearity, which matters here because equid stock spans four orders of magnitude.
It is the Pearson correlation of the mid-ranks, $\rho = \operatorname{cov}(R(x), R(y)) /
(\sigma_{R(x)}\sigma_{R(y)})$, which with no ties reduces to
$\rho = 1 - 6\sum_i d_i^2 / \big(n(n^2-1)\big)$.

\textbf{Mutual information} (\texttt{sklearn.feature\_selection.mutual\_info\_classif}, $k=5$
nearest neighbours) captures non-monotone dependence that a rank correlation misses, since a feature
can matter strongly at one end of its range and not at all at the other:
\[
I(X;Y) = \iint p(x,y)\,\log\frac{p(x,y)}{p(x)\,p(y)}\,\mathrm{d}x\,\mathrm{d}y ,
\]
estimated by the Kraskov--St\"ugbauer--Grassberger $k$-nearest-neighbour form
\[
\hat{I} = \psi(n) - \big\langle \psi(n_x+1) + \psi(n_y+1) \big\rangle + \psi(k),
\]
where $\psi$ is the digamma function and $n_x$, $n_y$ are per-point neighbour counts.

\textbf{Cram\'er's $V$} (\texttt{scipy.stats.chi2\_contingency}) measures association between a
categorical feature and the binary label, and puts every categorical result on the same 0 to 1 scale
so that income band and region are comparable:
\[
V = \sqrt{\frac{\chi^2}{n\,\min(r-1,\,c-1)}} ,
\]
where $\chi^2$ is the test statistic of the $r \times c$ contingency table.

\textbf{Variance inflation factor} (\texttt{numpy.linalg.lstsq}) quantifies how far one feature can
be reconstructed from the others, and therefore how unstable its coefficient would be in a linear
model:
\[
\mathrm{VIF}_j = \frac{1}{1 - R_j^2},
\]
where $R_j^2$ is the coefficient of determination from regressing $x_j$ on the remaining features.
This is the measure behind the collinearity result in Chapter~\ref{ch:results}.

\section{Feature Selection}

The association measures are diagnostics, not filters. They describe how each candidate relates to the
label on its own, and they are not used to choose the feature set, because a marginal measure and a
fitted model disagree about what matters (Chapter~\ref{ch:results}). Selection is driven by
attribution instead, in Section~\ref{sec:shapselect}.

One column is removed structurally: \texttt{equids} is exactly the sum of horses, asses and mules,
which a tree can rebuild from its parts. No projection or principal component analysis is applied;
with @SELN@ retained features and @ROWS@ rows the binding constraint proved to be signal rather than
dimensionality, which the ablation in Section~\ref{sec:ablation} supports.

\section{Feature Selection by SHAP}
\label{sec:shapselect}

\subsection*{What SHAP is}

SHAP attributes a prediction to its inputs using Shapley values, a construction from cooperative game
theory. The inputs are players, the prediction is the payout, and a feature's contribution is its
average marginal effect over every order in which the features could be introduced. For feature $j$,
with $F$ the full set and $f$ the model,
\[
\phi_j = \sum_{S \subseteq F \setminus \{j\}}
\frac{|S|!\,\big(|F|-|S|-1\big)!}{|F|!}
\Big[ f\big(S \cup \{j\}\big) - f(S) \Big],
\]
where $f(S)$ is the model output using only the features in $S$, the rest marginalised. The values
satisfy local accuracy ($\sum_j \phi_j$ equals the prediction minus the base rate), missingness (an
absent feature receives zero) and consistency (if a feature's marginal effect rises in every subset,
its value cannot fall). The implementation is \texttt{shap.TreeExplainer}, which computes exact
TreeSHAP values for the tree ensembles, so the attribution is not sampled. Global importance is the
mean absolute value over the $n$ explained rows, $\bar{\phi}_j = \frac{1}{n}\sum_i |\phi_{ij}|$.

\subsection*{Why attribution rather than association}

The measures in Section~\ref{sec:assoc} ask how a feature relates to the label on its own. Selection
needs a different question: how much a feature adds to a model that already has the others. The two
answers diverge here. Mutual information and Spearman correlation rank \texttt{longitude} first and
\texttt{temp\_mean\_anom} near the bottom, while attribution reverses them, because longitude stands in
for which continent a country occupies, and the model recovers that from region, population and
reporting variables. Selecting on association would keep proxy columns and drop conditional signal.

SHAP was the only attribution method used, for three reasons. It is additive and signed, so the same
values supply the global ranking selection needs and the per-prediction factor list the risk engine
returns, keeping one explanation mechanism in the platform rather than two. \texttt{TreeExplainer} is
exact for the tree families in use, and cheap enough to recompute on every training run. And it
carries the consistency guarantee above, which permutation importance and impurity gain do not:
impurity gain is biased toward high-cardinality columns, and permutation importance is unstable with
the correlated inputs this panel has many of.

\subsection*{Procedure and the retained set}

The ranking is computed on the training years only, 2005 to @SELTRAINEND@. Fitting on the full panel
would let the held-out years influence which features were chosen, making the temporal-holdout score
optimistic. The @SELCAND@ numeric candidates are ranked by mean absolute SHAP on that window and the
first @SELK@ are kept, together with the two categorical columns, which are retained because region and
income band are the reporting-capacity proxies the discussion turns on.

\begin{table}[htbp]
\centering
\caption{The @SELN@ features the reported models use, in rank order by mean absolute SHAP on the
training years, with the unit each variable is measured in. The set carries @SELSHARE@ of the total
attribution across all @SELCAND@ candidates.}
\label{tab:selected}
\small
\begin{tabular}{@{}rlp{4.6cm}r@{}}
\toprule
\textbf{Rank} & \textbf{Feature} & \textbf{Unit as measured} & \textbf{Mean $|\phi|$} \\
\midrule
@SELROWS@
\bottomrule
\end{tabular}
\end{table}

\section{Models}

Six model families are compared. The set spans the range from additive to fully interactive, and
includes a deliberately simple reference.

\begin{table}[htbp]
\centering
\caption{Model families and the hyperparameters selected by tuning.}
\label{tab:models}
\small
\begin{tabular}{@{}p{2.6cm}p{2.3cm}p{9.2cm}@{}}
\toprule
\textbf{Model} & \textbf{Family} & \textbf{Selected configuration} \\
\midrule
@MODELROWS@
\bottomrule
\end{tabular}
\end{table}

Logistic regression provides an additive baseline with balanced class weights. A single decision
tree is included because shallow trees are interpretable by a non-specialist, and because the
performance gap between one tree and an ensemble is itself informative. Random forest and extra
trees are bagged ensembles \cite{breiman2001}, differing in the degree of randomisation applied to
split selection.
XGBoost and LightGBM are boosted ensembles, differing in tree growth strategy \cite{chen2016,ke2017}.

Neural networks were excluded on evidential grounds: with @POSITIVES@ positives and @FEATURES@
features a network has more parameters than examples and would memorise the training period.

\section{Chained Pipeline}

The project proposal specified a multi-stage design. Three stages are implemented.

\begin{enumerate}
  \item \textbf{Population forecast.} Next-year log equid stock is predicted from the current
        year's covariates using ridge regression and histogram gradient boosting, evaluated by
        grouped cross-validation on country.
  \item \textbf{Occurrence.} The binary label is modelled with the forecast population appended as
        an additional feature, and compared against the same model without it.
  \item \textbf{Intensity.} Conditional on an event, log event count is modelled by a random forest
        regressor trained on positive observations only.
\end{enumerate}

The stages are combined into a hurdle model, in which expected event burden is the product of
event probability and conditional intensity.

\section{Evaluation Design}

Three validation schemes are reported, each answering a different question.

\begin{itemize}
  \item \textbf{Temporal holdout.} Training on 2005 to 2017 and testing on 2018 to 2023, with the
        test period never observed during fitting. This answers whether the model can be used in
        the following years.
  \item \textbf{Leave-country-out.} Five folds grouped by country, so every prediction is made for
        a country absent from training. This answers whether the model transfers to a new country,
        and it governs model selection because it is the harsher test and the closer
        approximation of deployment.
  \item \textbf{Repeated stratified cross-validation.} Five folds repeated three times, used as a
        stability check on the ranking metrics.
\end{itemize}

Precision-recall AUC is the primary metric. At @PREVALENCE@ prevalence, ROC-AUC is dominated by the
true-negative mass and overstates performance, a well-characterised property of imbalanced problems
\cite{saito2015,davis2006}, so it is reported only for comparability. Brier score and expected
calibration error are reported because an uncalibrated probability cannot support a threshold-based
alert \cite{niculescu2005,huang2020}. Precision, recall, specificity, F1 and the Matthews
correlation are computed at a threshold tuned on training data only, with bootstrap percentile
intervals over one thousand resamples.

Grouped rather than random splitting is essential, since a random row split would put the same
country in both partitions and let the model memorise country identity, inflating every score
\cite{roberts2017}.

\section{Leakage Controls}

Six controls are applied: features use year $t$ or earlier and only target columns use $t+1$; the
split is chronological; hyperparameters are tuned inside training folds with grouped
cross-validation; calibration is fitted on training folds only; the alert threshold is fixed on the
training period and applied unchanged to test; and imputation values and missing indicators are
generated inside the pipeline.
"""

BODY_IMPL = r"""
% =====================================================================
\chapter{Implementation}
\label{ch:impl}
% =====================================================================

\section{Software Architecture}

The project is implemented as a sequence of numbered scripts, each producing artefacts consumed
by the next. All intermediate outputs are cached, so any stage can be re-run without repeating
the stages before it.

\begin{table}[htbp]
\centering
\caption{Processing stages and their outputs.}
\label{tab:stages}
\small
\begin{tabular}{@{}p{4.3cm}p{4.0cm}p{6.2cm}@{}}
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

Figure~\ref{fig:trainflow} shows the training sequence. The chronological split is placed before
any model sees the data, so the test years cannot influence fitting, tuning or calibration.

@TRAININGFIG@

\section{Evaluation Pipeline}

Figure~\ref{fig:evalflow} shows the evaluation sequence. One trained model is scored under three
schemes, each producing a different answer, and the resulting metrics are summarised with
uncertainty intervals.

@EVALFIG@

\section{Alert Engine Design}

The wider platform for which this model was built includes an alert service that converts a
predicted probability into a notification for registered owners and field workers. The rules
engine is shown in Figure~\ref{fig:alertarch}. Three rules govern whether a notification is
emitted. A threshold maps the calibrated probability to a risk level. A suppression rule decides
whether a message is warranted at all, based on state changes, cooldowns and a data-freshness
guard. A deduplication rule prevents the same alert being issued twice for the same area, period
and level.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{proposal_alert_architecture.png}
\caption{Architecture of the alert rules engine, reproduced from the project proposal. The
calibrated probability enters the threshold, suppression and deduplication rules before an alert
record is created and fanned out to notification channels.}
\label{fig:alertarch}
\end{figure}

The thresholds used by this engine come from the operating curve in
Section~\ref{sec:alerts}, so the alerting behaviour of the platform is tied to measured
performance rather than to a default value.

\section{Reproducibility}

The full computation runs in approximately @RUNTIMEMIN@ minutes on a laptop processor without a
graphics accelerator, using @HARDWARE@. Per-family fitting time at the country-year level ranges
from @MINTIME@ seconds for the decision tree to @MAXTIME@ seconds for LightGBM.

A single module-level seed constant governs model fitting, cross-validation splitting, bootstrap
resampling and SHAP sampling. Software versions are @ENVSPEC@. Raw payloads are cached under
\texttt{data/raw} and the derived panel is written to \texttt{data/processed}, so every reported
number can be regenerated without re-downloading upstream sources.

One determinism caveat applies. Tree ensembles are seeded but not bitwise reproducible across
different thread counts, so parallel execution may change the final decimal of an ensemble score.
"""
