"""Chapters 5-6 (results, conclusion) of the full technical report."""

BODY_RESULTS = r"""
% =====================================================================
\chapter{Results and Discussion}
\label{ch:results}
% =====================================================================

\section{Dataset Characteristics}

The modelling matrix contains @ROWS@ country-year observations, of which @POSITIVES@ are
positive, a prevalence of @PREVALENCE@ and an imbalance ratio of @IMBALANCE@ to one.
Table~\ref{tab:labels} summarises the distribution.

\begin{table}[htbp]
\centering
\caption{Characteristics of the label.}
\label{tab:labels}
\small
\begin{tabular}{@{}lr@{}}
\toprule
\textbf{Property} & \textbf{Value} \\
\midrule
Observations & @ROWS@ \\
Positives and negatives & @POSITIVES@ and @NEGATIVES@ \\
Prevalence & @PREVALENCE@ \\
Imbalance ratio & @IMBALANCE@ : 1 \\
Countries with at least one positive & @POSCOUNTRIES@ of @COUNTRIES@ \\
Countries positive in two or more years & @REPEATPOS@ \\
Share of positives in the top five countries & @TOP5SHARE@ \\
\bottomrule
\end{tabular}
\end{table}

Three properties of this distribution matter. The imbalance rules out accuracy as a metric and
motivates precision-recall analysis. The temporal persistence of the label, with @REPEATPOS@ of
@POSCOUNTRIES@ positive countries recording positives in more than one year, justifies the use of
historical features. The geographic concentration of positives, with the top five countries
holding @TOP5SHARE@ of them, provides the first indication that the label tracks reporting
capacity, since those countries operate reference laboratories.

Figure~\ref{fig:labels} presents the same information graphically, together with the regional
distribution of prevalence.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig10_label_anatomy.png}
\caption{Label anatomy. Panel A gives annual positive counts with prevalence on the secondary
axis. Panel B gives the distribution of positive years per country. Panel C gives prevalence by
World Bank region.}
\label{fig:labels}
\end{figure}

\section{Statistical Association and Feature Selection}
\label{sec:selection}

Spearman correlation, mutual information and Cram\'er's $V$ were computed for every candidate
feature before any model was fitted. The strongest monotone association is
\texttt{years\_since\_last} at $\rho = @YSLRHO@$, negative because a longer interval since the
last recorded event implies lower risk. This is the most defensible epidemiological signal in the
panel. Among the categorical strata, region yields a Cram\'er's $V$ of @CRAMREGION@, a small
association, and income band yields @CRAMINCOME@, which is negligible.

Redundancy is substantial. Variance inflation reaches @VIFVAL@ for \texttt{@VIFFEAT@}, because
annual mean, minimum and maximum temperature are near-duplicates at country resolution.
Figure~\ref{fig:corr} shows the correlation structure of the highest-ranked features.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.76\textwidth]{fig11_correlation.png}
\caption{Spearman correlation matrix of the twenty-two highest-ranked features, hierarchically
ordered. Block structure indicates the collinear groups that motivated redundancy reduction.}
\label{fig:corr}
\end{figure}

The most consequential finding in this section concerns the choice of selection criterion.
Marginal association and conditional importance disagree almost completely. The rank correlation
between mutual information and SHAP attribution is @MIRHO@, and only @TOPOVERLAP@ of the ten
highest-ranked features are shared between the two orderings. \texttt{longitude} ranks first on
marginal correlation and approximately twentieth on conditional importance, because once
population and history are conditioned upon it carries little additional information. It
functions as a proxy for which part of the world a country occupies, and therefore for publishing
activity.

Figure~\ref{fig:views} shows the disagreement directly, and Table~\ref{tab:topfeat} gives the
ranked features with both sets of statistics. Ranking features by marginal association alone would
favour columns that track reporting practice rather than disease occurrence, so selection was
performed on conditional evidence instead.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig12_importance_views.png}
\caption{Marginal and conditional importance. Panel A plots mutual information against
conditional rank, and the absence of a downward trend is the disagreement quantified in the text.
Panel B gives the conditional ranking with the marginal association sign annotated.}
\label{fig:views}
\end{figure}

\begin{table}[htbp]
\centering
\caption{The eight highest-ranked features by mean absolute SHAP value, with marginal statistics
alongside for comparison.}
\label{tab:topfeat}
\small
\begin{tabular}{@{}rlrrrr@{}}
\toprule
\textbf{Rank} & \textbf{Feature} & \textbf{Mean $|$SHAP$|$} & \textbf{Spearman $\rho$} &
\textbf{Mutual info} & \textbf{VIF} \\
\midrule
@TOPFROWS@
\bottomrule
\end{tabular}
\end{table}

Figure~\ref{fig:shap} gives the global attribution for the full panel.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.72\textwidth]{fig06_shap.png}
\caption{Global feature attribution for XGBoost over the full panel, ordered by mean absolute SHAP
value. Population magnitude and reporting capacity dominate. Among biological drivers, recent
history and climate anomalies rank highest.}
\label{fig:shap}
\end{figure}

\section{Model Comparison}

Table~\ref{tab:level1} reports discrimination under all three schemes. The temporal holdout is the
realistic test and the leave-country-out result is the harder one.

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

Against a base rate of @PREVALENCE@, the strongest temporal result of @BESTPR@ represents an
approximately @LIFT@-fold lift. Every tree-based model exceeds the logistic baseline, and the
single decision tree is the weakest of the six, which indicates that the relationships are
interactive rather than additive.

The more important pattern is the systematic decline under leave-country-out validation. For
Random Forest the score falls from @RFPR@ to @RFLOCOR@, and the decline exceeds the width of the
bootstrap interval for every family. This is the expected signature of learning country-specific
structure, and it is the estimate that should be quoted for deployment.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig02_model_comparison.png}
\caption{Discrimination by model and validation scheme. The gap between repeated
cross-validation and leave-country-out validation is the cost of generalising to an unseen
country.}
\label{fig:comparison}
\end{figure}

Figure~\ref{fig:curves} shows the ROC and precision-recall curves for the temporal holdout. At
this prevalence the ROC curves compress into a narrow band while the precision-recall panel
separates the families.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig03_roc_pr_curves.png}
\caption{ROC curves (panel A) and precision-recall curves (panel B) on the temporal holdout.}
\label{fig:curves}
\end{figure}

\section{Calibration}

Predictions from the selected model are well calibrated, with an expected calibration error of
@ECE@ and a Brier score of @BRIER@. A stated risk of twenty-four per cent corresponds to an
observed event frequency of approximately twenty-four per cent. This property is what makes a
threshold-based alert defensible, since a message quoting a probability must be numerically
trustworthy.

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{fig04_calibration.png}
\caption{Reliability diagram for the selected model on the temporal holdout, together with the
distribution of predicted risk.}
\label{fig:calib}
\end{figure}

\section{Temporal Resolution}

Aggregating observations to country and five-year period raises prevalence to @L2PREV@ and
improves every metric, as shown in Figure~\ref{fig:resolution}. The mechanism is that coarser
windows match the reporting cadence of the label, and a positive anywhere within the window counts
once.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.85\textwidth]{fig09_resolution.png}
\caption{The same models evaluated at fine and coarse temporal resolution.}
\label{fig:resolution}
\end{figure}

\section{Ablation}
\label{sec:ablation}

Feature groups were removed and each configuration retrained, with results in
Table~\ref{tab:ablation} and Figure~\ref{fig:ablation}.

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

Two results are more informative than the headline score. First, the reduced history and
population set of @AS5K@ columns reaches @AS5LOCO@ under leave-country-out validation, against
@AS6LOCO@ for the full @AS6K@ column set. Added covariates improve in-distribution fit and reduce
transfer, because they allow the model to fit country-specific peculiarities. Second, climate
covariates alone reach only @AS3LOCO@, marginally above the @PREVALENCE@ floor, which indicates
that annual country-level climatology largely encodes latitude and therefore country identity.

A separate probe adds research-output proxies as two additional columns. It moves the
leave-country-out score by @AS7DELTA@, which is weak evidence that the model is not purely
tracking publication volume, but it is not proof.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.92\textwidth]{fig05_ablation.png}
\caption{Ablation settings under both validation schemes.}
\label{fig:ablation}
\end{figure}

\section{Chained Pipeline}

Table~\ref{tab:chain} reports the effect of appending the stage-one population forecast to the
occurrence model.

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

The population forecast performs well as a forecast, with a mean absolute error of @S1MAE@ on the
log scale and a Spearman correlation of @S1RHO@. The intensity stage is weaker but usable, with a
mean absolute error of @S3MAE@ and a rank correlation of @S3RHO@ among positive observations. The
hurdle product ranks expected annual event burden with a Spearman correlation of @HZRHO@, and its
highest decile captures @HZEVENTS@ of @HZTOTAL@ observed events.

Appending the stage-one forecast to the occurrence model changes temporal PR-AUC by
@CHAINDELTA@, which is inside the noise band. The explanation is structural rather than a failure
of tuning. Population magnitude is already a direct feature of the occurrence model, so
forecasting it and appending the forecast supplies a less accurate copy of information the model
already holds. Chaining is expected to assist where the intermediate quantity cannot be observed
directly, which is not the case here.

This is reported as a negative result. It is a genuine finding about chained architectures for
this problem class, and it is retained rather than removed.

\section{Alert Economics}
\label{sec:alerts}

The operating characteristics of the model as a warning system are shown in
Figure~\ref{fig:alerts}. Alerting the six per cent of country-years with the highest predicted
risk captures approximately half of all observed events, and alerting twenty-eight per cent
captures eighty per cent. Uniform alerting would require full coverage for the same recall, so the
model is roughly eight times more efficient than arbitrary selection at the fifty per cent
operating point.

\begin{figure}[htbp]
\centering
\includegraphics[width=0.92\textwidth]{fig07_alert_budget.png}
\caption{Alert economics. Panel A gives the fraction of events captured as the alert budget grows,
against random alerting. Panel B gives the alert volume required to reach a target recall.}
\label{fig:alerts}
\end{figure}

\section{Subgroup Analysis}

Table~\ref{tab:subgroup} reports leave-country-out performance by region. Skill is lowest in
Sub-Saharan Africa and in low-income countries, which are the settings in which early warning
would be most valuable. The cause is label sparsity rather than a defect in the model, since there
are few recorded events from which to learn in those strata.

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

\begin{figure}[htbp]
\centering
\includegraphics[width=0.9\textwidth]{fig08_subgroups.png}
\caption{Regional performance under leave-country-out validation.}
\label{fig:subgroups}
\end{figure}

\section{Discussion}

The results support four conclusions.

The model has genuine predictive skill. A precision-recall AUC of @BESTPR@ against a base rate of
@PREVALENCE@ is not explainable by chance, it survives a strictly forward-looking temporal split,
and the probabilities are calibrated to within two percentage points.

The skill does not transfer intact. Leave-country-out performance is roughly forty per cent lower
in relative terms, and this is the correct figure for planning. Any deployment to a new country
should be preceded by local validation.

The principal signal is surveillance rather than biology. The evidence is consistent across three
independent analyses: the highest-ranked features are population and connectivity measures, the
label concentrates in countries with reference laboratories, and the best-scoring cells are India,
the United States and Australia. Climate, which the original project proposal treated as a
primary input, transfers poorly at this resolution.

Simpler models transfer better. The reduced feature set outperforms the full set across countries,
and the linear baseline degrades least in absolute terms. This is a practical argument for
parsimony when positive examples are limited.
"""

BODY_CONCL = r"""
% =====================================================================
\chapter{Conclusion and Future Work}
\label{ch:concl}
% =====================================================================

\section{Conclusion}

This project set out to build a usable warning system for glanders, not only a model. That meant
two things: establishing whether population-level risk could be predicted from publicly available
data, and designing how such a prediction reaches a person. Four sources that had not previously
been applied to the disease were assembled into a country-year panel covering 162 equine-holding
countries, and six model families were trained and evaluated under three validation schemes,
together with a three-stage chained pipeline. Around that model, the delivery problem was
decomposed into three components with fixed contracts: the risk engine that produces a calibrated
probability, the retrieval-augmented layer that explains it against official guidance, and the
alert service that turns it into a small number of messages.

The central finding is that prediction is possible, and that the achievable performance is
moderate. On a strictly forward-looking temporal holdout the strongest model reaches a
precision-recall AUC of @BESTPR@ against a base rate of @PREVALENCE@, an approximately @LIFT@-fold
lift, with an expected calibration error of @ECE@. Used as a warning system, it captures half of
all observed events while alerting six per cent of country-years.

The second finding is that the skill is fragile across geography. Leave-country-out performance is
approximately forty per cent lower in relative terms, and the decline is concentrated in the
regions where early warning would be most useful.

The third finding concerns what the model is learning. Three independent analyses
converge on the same conclusion. The highest-ranked features are population size and reporting
capacity rather than biological drivers. The label concentrates in countries that operate
reference laboratories. And the highest-scoring cells are the countries with the strongest
veterinary publishing record. The model predicts where glanders will be documented, which is
useful for directing surveillance, and it is not a map of where the organism is present.

The fourth finding is negative. The chained design specified in the project proposal does not
improve discrimination, because the intermediate quantity is already available as a direct
feature. This is reported rather than omitted, since it is a reproducible result about chained
architectures for this problem class.

The fifth finding is architectural. Decomposing the system into three components with versioned
contracts, none of which hardcodes the disease, made each part testable on its own: the risk engine
could be evaluated before any explanation existed, and the alert rules could be specified and
checked against a policy before any message was sent. The cost is that the parts must be
maintained together, and the benefit is that replacing the model, the language model or the
notification channel is a local change. For a project whose useful life outlasts any single
model, that trade is the right one.

\section{Future Work}

Six directions follow from the limitations identified in this report. Four concern the model and
two concern the components around it.

\textbf{Modelling reporting effort explicitly.} The most important extension is to treat
surveillance capacity as a modelled quantity rather than an incidental covariate. This could be
done by using publication volume as a separate offset, or by fitting a two-part model in which
detection and occurrence are estimated jointly. Without this, gains in predictive score are
likely to reflect reporting practice rather than disease.

\textbf{Validating the label extractor.} The 263 extracted events have not been checked against a
hand-annotated reference set. Annotating a stratified sample of several hundred abstracts would
allow precision and recall of the extractor itself to be reported, and would bound the label noise
that currently propagates into every downstream estimate.

\textbf{District-level modelling for India.} The original proposal envisaged district-month
resolution for India, where the disease is concentrated in a small number of states. Public
district-level covariates for equine population and climate would need to be assembled, but the
resolution would match the scale at which control measures are applied.

\textbf{Operational calibration under drift.} A deployed model requires periodic recalibration as
reporting practice changes. The calibration framework used here is a single point estimate; a
production system would need drift monitoring and a defined retraining trigger.

\textbf{Deploying and evaluating the explanation layer.} The RAG layer is specified to the level of
its retrieval parameters, guardrails and evaluation protocol, but its targets are unmeasured. The
next step is to run it against the guidance corpus and report recall@5, faithfulness and citation
precision on the hand-built question set, including the false refusal rate, since a layer that
refuses too often is as unusable as one that never refuses.

\textbf{Measuring alert fatigue in the field.} The three alert rules are designed to keep message
volume low, but the quantity that decides whether the service survives its second year is messages
per subscriber per year, and that can only be measured with real subscribers. A small pilot with a
district veterinary office would give both that number and the delivery reliability per channel,
which the current specification states as a protocol rather than a result.

Two smaller extensions are also worth noting. Incorporating WOAH WAHIS official outbreak records as a
second label source would allow the literature-derived label to be validated where the two
overlap. And a cost-sensitive threshold, in which the relative cost of a missed outbreak and a
false alert is stated explicitly, would replace the F1-optimal threshold used here with one
matched to the programme's actual priorities.
"""
