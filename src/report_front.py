"""Front matter and chapters 1-2 of the full technical report.

FRONT_MATTER reproduces the institutional template used by the department's
project reports verbatim: title page with the institute emblem at top right,
Certificate, Declaration, Acknowledgments, Abstract and Contents. Only the
project-specific fields (title, author, roll number, supervisor) differ.

Plain raw strings with @TOKEN@ placeholders, substituted by src/09_make_full_report.py.
No f-strings, so LaTeX braces need no escaping.
"""

FRONT_MATTER = r"""
% ============================== TITLE PAGE ==============================
% Bold/regular pattern measured from the department template: the title is large but
% REGULAR weight; the four structural headings are bold; author names are bold with the
% roll numbers set regular in a second column. Names right-aligned, roll numbers
% left-aligned, as a tabular{rl}.
\begin{titlepage}
\thispagestyle{empty}
\begin{center}

{\huge GlandersWatch: A Modular Platform for\\[7pt]
Glanders Risk Prediction, Retrieval-Augmented\\[7pt]
Explanation and Owner Alerting\par}

\vspace{1.15cm}

{\Large\bfseries Project Report Submitted\par}
\vspace{0.30em}
{\normalsize in partial fulfillment of the requirements for the award of the\par}

\vspace{1.05cm}
{\Large\bfseries Bachelor of Technology\par}
\vspace{0.28em}
{\normalsize in\par}
\vspace{0.22em}
{\Large\bfseries Computer Science Engineering\par}

\vspace{0.95cm}
{\normalsize by\par}
\vspace{0.40em}
{\fontsize{10.9}{13.2}\selectfont
\begin{tabular}{@{}r@{\hspace{1.1em}}l@{}}
\bfseries Pedapatruni Shanmuk Vardhan & B123089 \\[1pt]
\bfseries Shaktimayee Mohanty & B123118 \\[1pt]
\bfseries Yuvraj Singh & B123153 \\
\end{tabular}\par}

\vspace{1.0cm}
{\normalsize Under the supervision of\par}
\vspace{0.32em}
{\fontsize{10.9}{13.2}\selectfont\bfseries Dr. Sangita Dhara\par}

\vspace{1.0cm}
\includegraphics[width=3.0cm]{iiit_logo.png}\par

\vfill

{\normalsize Department of Computer Science and Engineering\par}
\vspace{0.32em}
{\fontsize{10.9}{13.2}\selectfont\bfseries International Institute of Information Technology, Bhubaneswar\par}
\vspace{0.32em}
{\normalsize @MONTHYEAR@\par}

\vspace*{0.6cm}

\end{center}
\end{titlepage}

% ============================== CERTIFICATE ==============================
\newpage
\thispagestyle{empty}
\noindent\underline{\textbf{Certificate}}

\vspace{0.9cm}
\noindent
{\sloppy
This is to certify that the report entitled ``GlandersWatch: A Modular Platform for Glanders Risk
Prediction, Retrieval-Augmented Explanation and Owner Alerting'' submitted by \mbox{Pedapatruni Shanmuk Vardhan (@ROLLPSV@)}, \mbox{Shaktimayee Mohanty (@ROLLSM@)} and \mbox{Yuvraj Singh (@ROLLME@)} to
International Institute of Information Technology, Bhubaneswar is a record of bonafide project work
under my supervision, and the report is submitted for the evaluation of the BTech
Degree Final-Semester Project.\par}

\vspace{1.5cm}
\noindent
@SUPERVISOR@\\[0.2em]
\underline{(Supervisor)}

% ============================== DECLARATION ==============================
\newpage
\thispagestyle{empty}
\noindent\underline{\textbf{Declaration}}

\vspace{0.9cm}
\noindent
We certify that

\begin{enumerate}
  \item The work contained in the report has been done by ourselves under the general supervision
        of our supervisor.
  \item The work has not been submitted to any other Institute for any degree or diploma.
  \item We have followed the guidelines provided by the Institute in writing the report.
  \item We have conformed to the norms and guidelines given in the Ethical Code of Conduct of the
        Institute.
  \item Whenever we have used materials (data, theoretical analysis, and text) from other sources,
        we have given due credit to them by citing them in the text of the report and giving their
        details in the references.
  \item Whenever we have quoted written materials from other sources, we have put them under
        quotation marks and given due credit to the sources by citing them and giving required
        details in the references.
\end{enumerate}

\vspace{2.5cm}
\noindent
\noindent
\begin{tabular}{@{}p{5.75cm}p{4.35cm}p{4.35cm}@{}}
\textbf{Pedapatruni Shanmuk Vardhan} & \textbf{Shaktimayee Mohanty} & \textbf{Yuvraj Singh} \\[0.12em]
B123089 & B123118 & B123153 \\
\end{tabular}

% ============================== ACKNOWLEDGMENTS ==============================
\newpage
\thispagestyle{empty}
\noindent\underline{\textbf{Acknowledgments}}

\vspace{0.9cm}
\noindent
We would like to express our sincere gratitude to our respected supervisor, @SUPERVISOR@, for the
invaluable guidance, support and encouragement given throughout this project. Her insights and
expertise were instrumental in shaping this work and helped us overcome numerous challenges. We are
also thankful to the faculty and staff of the Department of Computer Science and Engineering,
International Institute of Information Technology, Bhubaneswar, for providing the resources and a
conducive learning environment. Finally, we would like to thank our families and friends for their
unwavering support and understanding during the course of this project.

\vspace{2.5cm}
\noindent
\noindent
\begin{tabular}{@{}p{5.75cm}p{4.35cm}p{4.35cm}@{}}
\textbf{Pedapatruni Shanmuk Vardhan} & \textbf{Shaktimayee Mohanty} & \textbf{Yuvraj Singh} \\[0.12em]
B123089 & B123118 & B123153 \\
\end{tabular}

% ============================== ABSTRACT ==============================
\newpage
\pagestyle{plain}
\noindent\underline{\textbf{Abstract}}
\addcontentsline{toc}{chapter}{Abstract}

\vspace{0.7cm}
\noindent
Glanders is a bacterial zoonosis of equids caused by \textit{Burkholderia mallei}. It is
notifiable, frequently fatal, and remains endemic in parts of Africa, Asia and South America.
Indian surveillance between 2019 and 2023 identified 728 seropositive equids across 138 districts,
with strong geographic concentration. The published machine learning literature on this disease is
confined to laboratory identification of the organism by spectroscopic methods, and no
population-level geographic risk model has been reported.

\vspace{0.5em}
\noindent
This report presents GlandersWatch, a platform built from three independently deployable components:
a calibrated machine learning risk engine, a retrieval-augmented layer that explains each
prediction with citations to official guidance, and an alert service that delivers the result to
equine owners. The decomposition is the contribution as much as the model is. Each component
communicates through a versioned schema rather than shared internals, none hardcodes the disease,
and each degrades without failing the others.

\vspace{0.5em}
\noindent
The risk engine combines four public datasets not previously applied to glanders into a country-year
panel: a text-mined occurrence corpus from Europe PMC, FAOSTAT livestock stocks, World Bank
development indicators and NASA POWER reanalysis climatology. The panel contains 3,078 country-year
observations across 162 equine-holding countries from 2005 to 2023, with 172 positive labels and 44
engineered features. Six model families are trained under three validation schemes, and a
three-stage chained pipeline is evaluated in which animal population is forecast before occurrence
is predicted.

\vspace{0.5em}
\noindent
On a forward temporal holdout the strongest model reaches a precision-recall AUC of 0.554 against a
base rate of 0.056, roughly a ten-fold lift, with an expected calibration error of 0.016. Performance
falls to 0.304 under leave-country-out validation, which is the estimate to quote for an unseen
country. Chaining produces no measurable gain in discrimination. An ablation shows climate
covariates transfer poorly across countries, and the model performs least well in low-income
regions. The dominant limitation is that the label reflects documented activity rather than true
incidence, so the model largely learns where disease is reported. Reporting effort is the principal
confounder and the main target for future work. The explanation and alert components are specified
to the level of their interfaces, rule semantics and evaluation protocol, and are not reported as
measured results because they are not deployed.

\vspace{0.7em}
\noindent
\textbf{Keywords:} Glanders, \textit{Burkholderia mallei}, Risk Prediction, Gradient Boosting,
Probability Calibration, SHAP, Retrieval-Augmented Generation, Citation Grounding, Alert Fatigue,
Modular System Design, MLOps, Animal Health Surveillance.
"""

BODY_INTRO = r"""
% =====================================================================
\chapter{Introduction}
\label{ch:intro}
% =====================================================================

\section{Background}

Glanders is a contagious and potentially fatal disease of horses, donkeys and mules caused by
the Gram-negative bacterium \textit{Burkholderia mallei}. The organism has no environmental
reservoir. Infection persists through transmission among equids, and asymptomatic carriers can
remain infectious for extended periods. Human infection is rare but carries a high case fatality
rate, and occurs through occupational contact with infected animals. The disease is notifiable
to the World Organisation for Animal Health and is classified as a potential bioterrorism agent.

The economic significance of glanders is concentrated in low and middle income countries, where
equids remain essential to transport, construction, agriculture and brick manufacture. India
recorded 5.44 lakh equids in the 2019 Livestock Census, a large proportion held by households
that depend on the animals for daily income. For such households the loss of a working animal is
a direct loss of livelihood, which makes early warning useful even where mass treatment is not
feasible.

Surveillance data indicate that the disease is neither rare nor geographically contained. A
national programme screening 158,798 equid serum samples from 391 districts between 2019 and
2023 identified 728 seropositive animals in 138 districts, with roughly sixty per cent of
positives reported from Uttar Pradesh. Historical surveillance covering 2006 to 2018 reported
1,145 positive equids among 128,404 sera tested. These figures describe a persistent, spatially
structured problem rather than isolated outbreaks.

\section{Problem Definition}

The operational question facing a district veterinary officer is not whether glanders exists in
the country, but whether it is likely to appear in a given area in the coming year. Answering it
requires combining several kinds of evidence: the history of the disease in and around the area,
the size of the susceptible population, and the environmental conditions that permit
transmission.

Surveillance systems report what has already happened. Forecasting systems exist for several
livestock diseases but not for glanders. The problem addressed here is therefore to build a
population-level risk model for glanders from publicly accessible data and to measure how well it
works.

The problem has four parts.

\begin{enumerate}
  \item \textbf{Data assembly.} No single public source records glanders occurrence completely.
        Occurrence must be reconstructed from the literature and joined to population and
        environmental covariates at a common geographic and temporal resolution.
  \item \textbf{Label construction.} The outcome is rare, which makes naive accuracy useless and
        requires an explicit treatment of what a negative observation means.
  \item \textbf{Model selection under distribution shift.} A model fitted on some countries must
        be evaluated on countries it has never seen, because that is the deployment condition.
  \item \textbf{Threshold economics.} A probability is not an alert. The operating point must be
        chosen so that the volume of warnings is defensible relative to the events caught.
\end{enumerate}

\section{Objectives}

The project has one research objective and three engineering objectives. The research objective is
the prediction problem; the engineering objectives are the three components that turn the
prediction into something a person can use.

\begin{enumerate}
  \item \textbf{Research.} To assemble a country-year panel for glanders from public sources not
        previously applied to this disease, train and compare six model families under three
        validation schemes, and report the achievable skill honestly, including negative results.
  \item \textbf{Component 1, prediction as a service.} To package the trained model as a versioned,
        portable artefact and expose it through a REST interface, so that the risk engine can be
        called by any consumer without that consumer knowing how the model works.
  \item \textbf{Component 2, cited explanation.} To build a retrieval-augmented layer that explains
        a prediction using official guidance, cites every claim, and refuses rather than guesses
        when the corpus does not support an answer.
  \item \textbf{Component 3, owner alerts.} To build a notification service that converts a
        calibrated probability into a small number of messages, using threshold, suppression and
        deduplication rules so that a rare disease does not train its users to ignore warnings.
\end{enumerate}

A cross-cutting requirement applies to all four: each component must be independently testable,
independently replaceable, and free of any hardcoded reference to glanders, so that the platform
can be repointed at another disease without altering the components themselves.

\section{Scope and Limitations}

The prediction study is scoped to country-year resolution. District-level modelling, which the
original project proposal envisaged for India, is not attempted here because the required
district-level covariates could not be assembled from public sources within the project period.
The explanation and alert layers are specified at area level and are resolution-agnostic, so they
apply unchanged once a district-level model exists.

The model is a population-level risk tool. It does not diagnose an individual animal and is not
a substitute for laboratory confirmation or clinical examination.

Three limitations are stated at the outset because they shape every result that follows. First,
the label is derived from published reports, so a negative observation may indicate absence of
disease or absence of reporting. Second, occurrence is reconstructed by an automated extractor
that has not been validated against a hand-annotated reference set. Third, with 172 positive
observations the statistical uncertainty on every headline metric is substantial, and this is
quantified rather than hidden.

\section{Organisation of the Report}

Chapter~\ref{ch:lit} reviews the epidemiological and machine learning literature and identifies
the gap addressed here. Chapter~\ref{ch:arch} sets out the system architecture and the three
components the platform is built from. Chapter~\ref{ch:method} describes the data, the panel
construction, the feature engineering and the modelling approach for the risk engine.
Chapter~\ref{ch:mlops} covers model serving and the operational layer that turns the trained model
into a callable component. Chapter~\ref{ch:rag} specifies the retrieval-augmented explanation layer
and Chapter~\ref{ch:alerts} the alert service. Chapter~\ref{ch:results} presents and discusses the
evaluation results. Chapter~\ref{ch:concl} concludes and sets out future work.

% =====================================================================
\chapter{Literature Review and Gap Analysis}
\label{ch:lit}
% =====================================================================

\section{Glanders Epidemiology and Burden}

Glanders is reviewed in the veterinary literature as a neglected zoonosis with high case
fatality and a real occupational risk to handlers \cite{khan2013,kanani2026}. A recent
systematic review and meta-analysis consolidates seroprevalence estimates across published
studies and identifies management practice and animal movement as the dominant epidemiological
drivers \cite{purnama2026}. Regional reviews document continued circulation in Brazil
\cite{mota2022}, and the disease remains endemic or repeatedly reported across parts of Africa,
Asia and the Middle East.

The consistent finding across this literature is that glanders persists where equid populations
are large, where animals move frequently, and where surveillance is weak. The first two
conditions are measurable from public data. The third affects whether the disease is visible at
all, and is therefore a confounder rather than a covariate.

\section{Surveillance in India}

Indian surveillance provides the strongest evidence base for the disease. Malik et al. described
the emergence and re-emergence of glanders in India through outbreaks reported between 2006 and
2011 \cite{malik2012}. Singha et al. reported serological surveillance and clinical investigation
of indigenous equines for the period 2015 to 2018 \cite{singha2020}. More recently, the national
programme covering 2019 to 2023 screened samples from 391 districts and produced a prevalence
estimate together with a risk analysis \cite{singha2026}.

These studies establish where glanders occurs, which districts carry the burden, and which
animal-level factors the risk analysis identified. None constructs a predictive model, and none
uses population or reanalysis covariates as predictors.

\section{Existing Forecasting Systems in India}

India is not without operational livestock forecasting. The closest system to this work is
NADRES v2, the National Animal Disease Referral Expert System operated by ICAR-NIVEDI
\cite{nadres}. It combines outbreak records from a network of AICRP centres with meteorological
and remote-sensing covariates, and issues district-level forewarnings roughly two months ahead
using a model family that overlaps with the one used here, including random forests and boosted
trees.

This project differs from it in four respects, and the differences are complementary rather than
competitive. It is glanders-specific, where a national system must spread effort across many
diseases. It is built entirely on public data, so it can be reproduced and audited by anyone. It
attaches a cited explanation to each prediction, which matters when the output is read by an owner
rather than a trained analyst. And it delivers to the owner directly, with rules designed to
suppress routine noise. A national system has institutional access that this project does not, and
this project has a level of local explainability that a multi-disease platform does not attempt.

The comparison is useful for a second reason. It shows that the architecture chosen here is the
conventional one for this problem class, and that the open question is not whether to forecast but
how to make a forecast understandable and actionable at the point of use.

\section{Geographic and Spatiotemporal Risk Analysis}

Descriptive spatial analysis of glanders has been reported. Fonseca-Rodr\'iguez et al. applied
spatiotemporal cluster detection to Brazilian glanders data \cite{fonseca2019}. More broadly,
species distribution and ecological niche models have been compared as tools for livestock and
disease epidemics \cite{hollings2017}.

This body of work is descriptive. Cluster detection identifies where cases have already
concentrated. It does not forecast which cells will be positive in a future period, which is the
question an early warning application has to answer.

\section{Machine Learning for Animal Disease Risk}

Predictive modelling of animal disease risk is established for avian influenza. Kane et al.
compared ARIMA and random forest models for the prediction of H5N1 outbreaks \cite{kane2014}.
Walsh et al. used machine learning to target active surveillance for avian influenza viruses
\cite{walsh2019}. Yoo et al. developed dynamic farm-level risk prediction for highly pathogenic
avian influenza in the Republic of Korea \cite{yoo2022}, and Alshatti et al. produced a risk
prediction model for outbreaks in Kuwait \cite{alshatti2026}.

This literature supplies the methodological template used here: assemble occurrence, population
and environmental covariates at a common spatial unit, fit tree-based ensembles, and evaluate on
held-out periods. The template has been applied to influenza, and not to glanders.

\section{Machine Learning and Glanders}

The only machine learning work specific to \textit{Burkholderia mallei} that could be located is
spectroscopic identification of the organism. Moawad et al. developed a Raman spectroscopic assay
in which learned models classify spectra to identify \textit{B. mallei} and related species
\cite{moawad2019}. St\"ockel et al. reported Raman spectroscopic detection and identification of
\textit{B. mallei} and \textit{B. pseudomallei} \cite{stoeckel2015}.

Both are laboratory diagnostic problems. Neither addresses the geographic or temporal
distribution of the disease, and neither produces a risk estimate for a population.

\section{Text Mining for Disease Event Extraction}

Using published literature as a structured source of occurrence data has precedent in epidemic
intelligence. Collier surveyed web-based epidemic intelligence and the role of text mining within
it \cite{collier2012}, and Lejeune et al. described multilingual event extraction for epidemic
detection \cite{lejeune2015}.

The present work applies sentence-level event extraction not as a supplementary signal but as the
primary source of the label, for the pragmatic reason that official outbreak records are
incomplete for many countries. The consequence, that the label inherits both the strengths and
the reporting biases of the literature, is analysed rather than assumed away.

\section{Prior Art Audit}

To test the novelty claim rather than assert it, a reproducible set of queries was run against
Europe PMC. Each row of Table~\ref{tab:novelty} is a query count, and the full query strings and
retrieved titles are retained alongside the project code.

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

The decisive cells are the query pairing glanders with NASA POWER, which returns zero records,
and the pairing with gradient boosting, which returns four, none of which is a glanders risk
model. The nearest prior work is descriptive cluster detection in Brazil and a risk-factor
analysis of the Indian serosurvey.

\section{Research Gap}

The literature reviewed above divides into three disjoint groups. Epidemiological studies describe
where glanders occurs. Machine learning studies of \textit{B. mallei} classify laboratory spectra.
Veterinary risk models exist but are built for influenza. No study joins an occurrence corpus, a
livestock census, development indicators and reanalysis climatology into a single panel for
glanders, and none evaluates a calibrated predictive model on that panel.

A second gap appears once the question moves from analysis to use. A probability on a dashboard
does not reach the person who owns the animals, and a risk score without a stated basis is not
something a field officer will act on. The literature that describes glanders occurrence and the
literature that builds spectroscopic classifiers both stop short of the delivery problem: how a
forecast becomes a cited explanation, and how an explanation becomes a message that an owner
receives and trusts. No work connects a glanders risk model to official control guidance and to a
notification path with rules that account for alert fatigue.

The contribution of this project therefore has two parts. The first is empirical: a calibrated
population-level risk model for glanders, built on data sources not previously applied to the
disease and evaluated under a forward temporal split and a country-holdout split. The second is
architectural: a decomposition of the delivery problem into three components with fixed contracts,
so that the prediction, its explanation and its alert can be built, tested and replaced
independently, and so that the same structure carries over to another disease.
"""
