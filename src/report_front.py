"""Front matter and chapters 1-2 of the full technical report.

Plain raw strings with @TOKEN@ placeholders, substituted by src/09_make_full_report.py.
No f-strings, so LaTeX braces need no escaping.
"""

FRONT_MATTER = r"""
% ============================== TITLE PAGE ==============================
\begin{titlepage}
\centering
\vspace*{0.5cm}

{\Large\bfseries INDIAN INSTITUTE OF INFORMATION TECHNOLOGY,\\[0.15em]
BHUBANESWAR\par}

\vspace{1.3cm}

{\LARGE\bfseries GlandersWatch\par}
\vspace{0.45cm}
{\Large\bfseries A Chained Multi-Level Machine Learning Framework for\\[0.15em]
Population-Level Glanders Risk Prediction\par}

\vspace{1.1cm}
{\large\itshape Project Report\par}
\vspace{0.3cm}
{\normalsize submitted in partial fulfilment of the requirements for the award of the degree\par}
\vspace{0.3cm}
{\large\bfseries Bachelor of Technology\par}
\vspace{0.15cm}
{\normalsize in\par}
\vspace{0.15cm}
{\large\bfseries Computer Science and Engineering\par}

\vspace{1.1cm}
{\normalsize by\par}
\vspace{0.3cm}
{\large\bfseries Yuvraj Singh \quad (Roll No.\ \textit{@ROLLNO@})\par}

\vspace{1.1cm}
{\normalsize Under the supervision of\par}
\vspace{0.25cm}
{\large\bfseries @SUPERVISOR@\par}

\vfill
{\normalsize Department of Computer Science and Engineering\\
Indian Institute of Information Technology, Bhubaneswar\\
Odisha, India\par}
\vspace{0.25cm}
{\normalsize @MONTHYEAR@\par}
\end{titlepage}

% ============================== CERTIFICATE ==============================
\newpage
\thispagestyle{plain}
\begin{center}
{\Large\bfseries INDIAN INSTITUTE OF INFORMATION TECHNOLOGY,\\ BHUBANESWAR\par}
\vspace{0.35cm}
{\Large\bfseries CERTIFICATE\par}
\end{center}

\vspace{0.7cm}
\noindent
This is to certify that the report entitled \textbf{``GlandersWatch: A Chained Multi-Level
Machine Learning Framework for Population-Level Glanders Risk Prediction''}, submitted by
\textbf{Yuvraj Singh} (Roll No.\ \textit{@ROLLNO@}) to the Indian Institute of Information
Technology, Bhubaneswar, in partial fulfilment of the requirements for the award of the degree
of Bachelor of Technology in Computer Science and Engineering, is a bona fide record of the
work carried out by him under my supervision and guidance.

\vspace{0.4em}
\noindent
The work has not been submitted elsewhere, in part or in full, for the award of any other
degree or diploma. The help and support received during the course of this work has been duly
acknowledged.

\vspace{2.4cm}
\begin{flushright}
\rule{5cm}{0.4pt}\\
@SUPERVISOR@\\
Supervisor\\
Department of CSE, IIIT Bhubaneswar
\end{flushright}

\vfill
\noindent
Date: \rule{3cm}{0.4pt}\hfill Place: Bhubaneswar

% ============================== DECLARATION ==============================
\newpage
\thispagestyle{plain}
\begin{center}
{\Large\bfseries DECLARATION\par}
\end{center}

\vspace{0.7cm}
\noindent
I hereby declare that the work contained in this report is my own and that I have not
reproduced any material from any other source, except where this has been acknowledged or cited
in the text.

\vspace{0.4em}
\noindent
All data used in this study are publicly available and every source is identified in
Chapter~\ref{ch:method} and listed in the References. All code written for this project is
original, and every reported number can be reproduced from that code.

\vspace{0.4em}
\noindent
I further declare that this report has not been submitted, in whole or in part, to any other
institution for any degree or diploma.

\vspace{2.4cm}
\begin{flushright}
\rule{5cm}{0.4pt}\\
Yuvraj Singh\\
Roll No.\ \textit{@ROLLNO@}\\
Department of CSE, IIIT Bhubaneswar
\end{flushright}

\vfill
\noindent
Date: \rule{3cm}{0.4pt}\hfill Place: Bhubaneswar

% ============================== ACKNOWLEDGMENTS ==============================
\newpage
\thispagestyle{plain}
\begin{center}
{\Large\bfseries ACKNOWLEDGMENTS\par}
\end{center}

\vspace{0.7cm}
\noindent
I would like to express my sincere gratitude to my supervisor, @SUPERVISOR@, for the guidance
and support extended throughout this project. The suggestions on framing the evaluation, and on
reporting negative results honestly, improved the work considerably.

\vspace{0.4em}
\noindent
I am grateful to the Department of Computer Science and Engineering at IIIT Bhubaneswar for the
computing facilities used for the experiments, and to the faculty who reviewed earlier versions
of this work and identified weaknesses in the evaluation design.

\vspace{0.4em}
\noindent
This study relies entirely on open data. I acknowledge the World Organisation for Animal Health,
the Department of Animal Husbandry and Dairying of the Government of India, the Food and
Agriculture Organization, the World Bank, the NASA POWER project and Europe PMC, whose publicly
accessible datasets made the work possible.

\vspace{2.2cm}
\begin{flushright}
Yuvraj Singh
\end{flushright}

% ============================== ABSTRACT ==============================
\newpage
\thispagestyle{plain}
\begin{center}
{\Large\bfseries ABSTRACT\par}
\end{center}

\vspace{0.6cm}
\noindent
Glanders is a bacterial zoonosis of equids caused by \textit{Burkholderia mallei}. It is
notifiable, frequently fatal, and remains endemic in parts of Africa, Asia and South America.
Indian surveillance between 2019 and 2023 identified 728 seropositive equids across 138
districts, with strong geographic concentration. The published machine learning literature on
this disease is confined to laboratory identification of the organism by spectroscopic methods.
No population-level geographic risk model has been reported.

\vspace{0.35em}
\noindent
This project develops such a model. Four public datasets that had not previously been applied to
glanders are combined into a country-year panel: a text-mined occurrence corpus from Europe PMC,
FAOSTAT livestock stocks, World Bank development indicators and NASA POWER reanalysis
climatology. The panel contains 3,078 country-year observations across 162 equine-holding
countries for the years 2005 to 2023, with 172 positive labels and 44 engineered features.

\vspace{0.35em}
\noindent
Six model families are trained under three validation schemes, and a three-stage chained
pipeline is evaluated in which animal population is forecast before occurrence is predicted. On
a forward temporal holdout the strongest model reaches a precision-recall AUC of 0.554 against a
base rate of 0.056, an approximately ten-fold lift, with an expected calibration error of 0.016.
Performance falls to 0.304 under leave-country-out validation, which is the honest estimate for
an unseen country. Chaining produces no measurable gain in discrimination. An ablation shows that
climate covariates transfer poorly across countries, and the model performs least well in
low-income regions. The dominant limitation is that the label reflects documented activity rather
than true incidence, so the model largely learns which countries report disease. Reporting effort
is identified as the principal confounder for future work.

\vspace{0.5em}
\noindent
\textbf{Keywords:} glanders, \textit{Burkholderia mallei}, zoonosis, risk prediction, class
imbalance, gradient boosting, probability calibration, SHAP, text mining, animal health
surveillance.
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
a direct loss of livelihood, which makes early warning valuable even where mass treatment is not
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
livestock diseases but not for glanders. The problem addressed here is therefore the construction
and honest evaluation of a population-level risk model for glanders using only publicly
accessible data.

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

The objectives of the project are:

\begin{enumerate}
  \item To assemble a country-year panel for glanders from public sources not previously applied
        to this disease, covering animal history, animal population and environment.
  \item To engineer and select features using statistical evidence rather than assumption, and to
        document which evidence was used and why.
  \item To train and compare six model families under three validation schemes, with the harder
        scheme governing model selection.
  \item To design and evaluate a chained pipeline in which animal population is forecast as an
        intermediate step.
  \item To produce calibrated probabilities and an alert operating curve, so that the output can
        support a warning decision rather than only a ranking.
  \item To report limitations and negative results explicitly, including any component that failed
        to improve performance.
\end{enumerate}

\section{Scope and Limitations}

The study is scoped to country-year resolution. District-level modelling, which the original
project proposal envisaged for India, is not attempted here because the required district-level
covariates could not be assembled from public sources within the project period.

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
the gap addressed here. Chapter~\ref{ch:method} describes the data, the panel construction, the
feature engineering and the modelling approach. Chapter~\ref{ch:impl} covers the implementation,
including the software architecture and both computational pipelines.
Chapter~\ref{ch:results} presents and discusses the results. Chapter~\ref{ch:concl} concludes and
sets out future work.

% =====================================================================
\chapter{Literature Review and Gap Analysis}
\label{ch:lit}
% =====================================================================

\section{Glanders Epidemiology and Burden}

Glanders is reviewed in the veterinary literature as a neglected zoonosis with high case
fatality and a genuine occupational risk to handlers \cite{khan2013,kanani2026}. A recent
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
animal-level factors are associated with seropositivity. None constructs a predictive model, and
none uses population or reanalysis covariates as predictors.

\section{Geographic and Spatiotemporal Risk Analysis}

Descriptive spatial analysis of glanders has been reported. Fonseca-Rodr\'iguez et al. applied
spatiotemporal cluster detection to Brazilian glanders data \cite{fonseca2019}. More broadly,
species distribution and ecological niche models have been compared as tools for livestock and
disease epidemics \cite{hollings2017}.

This body of work is descriptive. Cluster detection identifies where cases have already
concentrated. It does not forecast which cells will be positive in a future period, and that
distinction matters for an early warning application, where the value lies in anticipating
rather than confirming.

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

The literature reviewed above divides into three disjoint groups. Epidemiological studies
describe where glanders occurs. Machine learning studies of \textit{B. mallei} classify laboratory
spectra. Veterinary risk models exist but are built for influenza. No study joins an occurrence
corpus, a livestock census, development indicators and reanalysis climatology into a single panel
for glanders, and none evaluates a calibrated predictive model on that panel.

That gap defines the contribution of this project.
"""
