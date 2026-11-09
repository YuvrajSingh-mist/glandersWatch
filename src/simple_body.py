BODY = r"""
% =====================================================================
\section{What We Tried To Do}
% =====================================================================

Glanders is a bacterial disease that kills horses, donkeys and mules, and it can pass to
people who handle infected animals. Most Indian equids belong to poor families who use
them for transport, farming and construction. A district officer who knew a year ahead
that glanders was likely could warn owners in time to act. So the question is:

\begin{quote}
\emph{Given what we know about a country this year, can we predict whether glanders
will be reported there next year?}
\end{quote}

One row in our data is one country in one year. The model returns a number between 0 and
1, which we read as a risk score. A score of 0.30 means roughly a 30\% chance that
glanders will be reported in that country next year.

The model does not diagnose an animal and cannot tell a farmer whether their horse is
sick. It works at the level of countries and years, so it suits planning work. It is not
a substitute for a veterinarian looking at a sick animal.

% =====================================================================
\section{Dataset Used}
% =====================================================================

We used four public data sources. None had been used for glanders before, which is the
main reason this counts as new work.

\begin{table}[htbp]
\centering
\caption{The four data sources. Glanders events in Europe PMC were extracted by
matching a country name and an event term within the same sentence, which yielded 263
events across 2000 to 2024.}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{5.6cm}>{\raggedright\arraybackslash}p{3.6cm}>{\raggedright\arraybackslash}p{4.8cm}@{}}
\toprule
\textbf{Source} & \textbf{What it gives us} & \textbf{Size} \\
\midrule
Europe PMC (publications) & Where and when glanders was reported & 6,674 papers $\rightarrow$ 263 events \\
FAOSTAT & How many horses, donkeys, mules, cattle, goats and sheep each country has & 68,449 records, 1961--2023 \\
World Bank & Money, farming, population, internet access & 10 indicators, 217 countries \\
NASA POWER & Temperature, rainfall, humidity, wind & 6 measures, 211 locations \\
\bottomrule
\end{tabular}
\end{table}

\paragraph{Why these four sources.} They cover what decides whether a disease can appear at
all: whether it has been there before, how many animals could catch it, and whether the
climate suits it. World Bank data adds a rough measure of how well a country detects and
reports disease. Pulling several kinds of data together is what makes this stronger than an
analysis of one source.

\paragraph{The assembled panel.} All four sources are keyed on ISO-3 country code and
calendar year, so they join without ambiguity. The full panel has PANEL_ROWS country-year
rows covering PANEL_COUNTRIES countries from 2000 to 2024. For modelling we keep only
equine-holding countries, meaning those with a maximum stock of at least 1{,}000 equids, the
years 2005 to 2023, and rows where next year's answer is observable. That leaves
\textbf{2,880 rows, 44 candidate columns and 169 positive labels}.

\paragraph{Preprocessing.} Five steps, in this order.

\begin{enumerate}
\setlength{\itemsep}{0.1em}
\item \textbf{Name reconciliation.} Country and area names were matched across sources
      through \texttt{pycountry} with explicit overrides, because the same country is
      written ``T\"urkiye'' in one file and ``Turkey'' in another. Without this the joins
      would silently drop rows.
\item \textbf{Aggregate removal.} World Bank regional and global totals were dropped by
      requiring a three-character ISO code, so rows such as ``World'' and ``South Asia''
      cannot enter the panel as if they were countries.
\item \textbf{De-duplication.} Literature events were de-duplicated on the key
      \texttt{(iso3, year, record\_id)}, so one paper cannot inflate a cell by being
      counted several times.
\item \textbf{Missing values.} Filled with the column median, and every column keeps a
      missing-indicator flag so the model can tell an imputed value from a real one. The
      fill is fitted inside the training pipeline, never on the full table. Missing data
      was rare: MISS_ALL overall and MISS_MAX in the worst column.
\item \textbf{Absence handling.} A country-year is coded 0 only after that country passes
      the equine-stock filter, so a blank is never read as proof that disease was absent.
      This is the step that keeps the label honest.
\end{enumerate}

\paragraph{Feature engineering.} Four groups of columns were built from the raw sources,
all using information available in the current year or earlier. History columns are lags, a
five-year running total and years since the last event. Population columns add derived
quantities: equid share of all farm animals, equine density, and growth over one and three
years. Climate columns pair each measure with an anomaly, its deviation from that country's
own expanding mean. Section~\ref{sec:features} lists all four groups.

\paragraph{Feature selection.} Every input was screened for association with the answer and
for duplication of another input, but the screens were read rather than obeyed. Only one column
was dropped outright: total equids, because it is exactly the sum of horses, asses and mules and a
tree can rebuild it. Four columns scored below both association thresholds and three near-duplicate
pairs were flagged, yet all were kept, for the reason covered in Section~\ref{sec:analysis}: the
univariate screen disagrees with what the fitted model actually uses, and one flagged column turns
out to be among the three most important. No principal component analysis was used either; the
limit here is signal rather than dimensionality.

% =====================================================================
\section{Dataset Analysis}
\label{sec:analysis}
% =====================================================================

We start with the label, then move to how each input relates to it and how much the inputs
duplicate each other.

\paragraph{The answer key.} For every country and year the answer is yes or no: was
glanders reported the following year? Only 169 of the 2,880 rows are yes, which is 5.9\%.

\begin{table}[htbp]
\centering
\caption{Numbers describing the answer key.}
\small
\begin{tabular}{@{}lr@{}}
\toprule
\textbf{Measure} & \textbf{Value} \\
\midrule
Total rows & 2,880 \\
``Yes'' rows (event next year) & 172 \\
``No'' rows & 2,906 \\
Percentage ``yes'' & 5.6\% \\
Ratio of no to yes & about 17 to 1 \\
Countries with at least one ``yes'' & 56 of 160 \\
Countries with ``yes'' in two or more years & 30 \\
Share of all ``yes'' in the top 5 countries & 35.5\% \\
\bottomrule
\end{tabular}
\end{table}

\paragraph{What the distribution tells us.} Three things follow from that table, and each
one changed a decision later. First, yes is rare enough that always answering no would be
right 94.4\% of the time, so accuracy is useless here and we need scores built for rare
events. Second, the disease comes back: 30 of the 56 positive countries were positive in
two or more years, so past activity is a fair input rather than a shortcut. Third, the yes
answers cluster, with five countries holding 35.5\% of them, and those five are mostly rich
countries that run publishing laboratories.

For that reason the target is termed \emph{documented activity} rather than
\emph{disease occurrence}. A negative label can reflect either the absence of disease or the
absence of a report.

Before training anything we measured how each input relates to the answer. Three measures
were used on the numeric columns.
\emph{Spearman's $\rho$} checks whether two quantities rise and fall together, on a scale
from $-1$ to $+1$. \emph{Mutual information} catches relationships that are not a straight
line, and equals zero when a column tells you nothing about the answer. \emph{Cram\'er's
$V$} does the same job for text categories such as region.

\paragraph{Statistical association.} The strongest monotone signal in the whole dataset is
\texttt{years\_since\_last} at $\rho = -0.35$. The sign is negative because more years
since the last outbreak means lower risk. This is the one broadly epidemiological result in
the panel, and it says what we would hope: recent activity predicts future activity. On the
same scale, \texttt{internet\_pct} scores only $+0.09$ and \texttt{temp\_mean\_anom} about
zero. For the two text categories, region gives Cram\'er's $V$ of CRAMV_REGION, which counts
as a small association, and income band gives CRAMV_INCOME, which is negligible. Neither is
strong enough to act as a stand-in for the label.

\paragraph{Correlation and redundancy.} Several columns measure nearly the same thing.
Variance inflation factor is the standard measure of that, where a value above 10 is
usually treated as a problem. It reaches VIF_VAL for \texttt{VIF_FEAT}, because annual mean,
minimum and maximum temperature are near-duplicates of each other at country resolution.
Three groups sit at $|\rho| \geq 0.90$: \texttt{occ\_lag1} with \texttt{occ\_count\_lag1},
\texttt{cattle} with \texttt{log\_livestock}, and \texttt{temp\_mean} with \texttt{temp\_min}.
We kept one member of each group. This matters for reading coefficients in a linear model,
and not much for trees, since a tree splits on thresholds and does not care whether two
columns carry overlapping information.

\paragraph{Where the two importance measures disagree.} This is the result that shaped the
whole feature set. We compared how much each column correlates with the answer on its own
with how much the trained model relies on it, using SHAP. The two rankings agreed
almost not at all, with a rank correlation of MI_RHO and only 5 of the 10 top features
shared. Longitude is the clearest case: it ranks first on simple correlation and around
twentieth in what the model uses. The explanation is that longitude does not cause
glanders. It identifies which part of the world a country is in, and some parts publish
more papers. Ranking features by marginal correlation would therefore favour columns that
track reporting practice rather than disease occurrence. Features were selected on the
conditional evidence instead, and correlation was used only to discard columns with no
signal.

\begin{table}[htbp]
\centering
\caption{Top 8 features by importance to the trained model, with marginal statistics
alongside. The gap between the two sets of numbers is the disagreement described above.}
\small
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}rlrrrr@{}}
\toprule
\textbf{Rank} & \textbf{Feature} & \textbf{Importance} & \textbf{Correlation} & \textbf{Mutual info} & \textbf{Redundancy} \\
 & & \textbf{(mean $|$SHAP$|$)} & \textbf{(Spearman $\rho$)} & \textbf{(MI)} & \textbf{(VIF)} \\
\midrule
TOP_FEATURES
\bottomrule
\end{tabular}}
\end{table}

\paragraph{What we removed, and why.} Four columns had mutual information below 0.002 and
$|\rho|$ below 0.02, which means no measurable relationship to the answer at all. We
dropped one column that was exactly the sum of three others, since it adds nothing a tree
cannot build itself. We dropped one member of each near-duplicate pair listed above. No
principal component analysis was used: with eight retained columns and 2,880 rows the limit is signal
rather than dimensionality, and the section on results confirms that fewer columns
generalise better across countries, so compressing further would have cost
interpretability for nothing. Scaling is applied only to the logistic baseline, because
tree models are indifferent to it.

% =====================================================================
\section{What We Gave The Model (Features)}
\label{sec:features}
% =====================================================================

A feature is an input column. Forty-four were engineered and fourteen are used, all of them built
from information available in the current year or earlier. The candidates fall into four groups.

\begin{itemize}
\setlength{\itemsep}{0.15em}
\item \textbf{Disease history (7 columns).} Outbreaks in the previous two years, the
      five-year running total, years since the last event, and world and regional activity
      shares for the same year. The disease persists once introduced, so this group carries
      the epidemiological prior.
\item \textbf{Animal population (14 columns).} Log equid and total livestock stocks, the
      equid share of all farm animals, equid density, growth over one and three years, and
      the seven species counts. More animals means more chances to find the disease.
\item \textbf{Climate (10 columns).} Mean, maximum and minimum temperature, precipitation
      total and its coefficient of variation, relative humidity, and wind, each paired with
      an \emph{anomaly}. An anomaly is the difference from that country's own expanding
      mean, which separates ``unusually wet for here'' from an absolute number that mostly
      encodes latitude.
\item \textbf{Country context (11 columns).} Income band, agricultural land share,
      agricultural value added, livestock production index, GDP per person, rural share,
      internet penetration, fertiliser intensity, life expectancy, population and density.
      These mostly measure how well a country detects disease.
\end{itemize}

Three derived columns are worth naming. \emph{Equid share} is horses plus donkeys plus
mules divided by all farm animals, which shows how much of the farming depends on equids.
\emph{Livestock units} counts cattle and camels at full weight and small ruminants at one
tenth, following standard metabolic weights, so one number expresses grazing pressure
across species. \emph{Years since last event} uses 99 to mean ``never recorded''.

% =====================================================================
\section{Models We Tried}
% =====================================================================

We trained six models, including a deliberately simple one to compare against. The table
gives each model's family, what it does, and the settings the tuning search picked.

\begin{table}[htbp]
\centering
\caption{The six models, their family, and the settings chosen by tuning.}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.9cm}>{\raggedright\arraybackslash}p{2.3cm}>{\raggedright\arraybackslash}p{8.9cm}@{}}
\toprule
\textbf{Model} & \textbf{Family} & \textbf{What it does, and the settings chosen} \\
\midrule
MODELS_TABLE
\bottomrule
\end{tabular}
\end{table}

Forest models train many trees \emph{in parallel} on random subsets and average them,
which reduces variance. Boosted models train trees \emph{in sequence}, each fitting the
error left by the last, which reduces bias. That difference explains why the two families
end up with similar scores.

We left neural networks out because the data cannot support them. With 169 positives and
44 inputs, a network has far more settings to learn than it has examples to learn from,
so it would memorise the training rows and fail on new ones. That is an argument from the
data rather than a judgement about the method.

The collinear columns noted in Section~\ref{sec:analysis} needed no special handling, since
trees split on thresholds.

\paragraph{How the final model was chosen.} On performance in countries it had never seen,
because that is how the model would be used. Extra Trees came out best at 0.363. Random
Forest scored higher on the easier time-based test, but the country test is the one that
speaks to deployment.

We did not stack the models into a meta-learner. The gap between families is smaller than
the uncertainty on any single score, so a meta-learner trained on 169 positives would add
variance without a gain we could defend. We spent that effort on calibration instead, since
that is what a threshold-based alert depends on.

% =====================================================================
\section{How We Trained And Tested It}
\label{sec:eval}
% =====================================================================

Several measures were taken so that nothing from the test period could influence training.

We ran three tests, and each answers a different question. They disagree for an
informative reason: the country split always scores lower than the time split, and that
gap is the price of meeting a country the model has never seen.

FIGURE_EVALFLOW

A random split would put the same country in both training and testing, which lets the
model memorise country patterns and look good for the wrong reason. Grouping by country
prevents that. The scores are defined in the glossary. In short, PR-AUC is the main one
because rare yes rows are what we care about, ROC-AUC is reported so others can compare,
and Brier plus calibration error check whether the percentages are believable.

Five things stayed inside the training data: model settings, the alert threshold, the
calibration step, the missing-value fill, and the choice of which columns to drop. The test
years could not touch any of them. Every input comes from the current year or earlier, with
only the answer taken from the following year.

FIGURE_TRAINFLOW

% =====================================================================
\section{How The Maths Works}
\label{sec:maths}

Four ideas carry most of the analysis.

\paragraph{Precision and recall.} The model flags some rows as risky. \emph{Precision}
asks what share of the flagged rows were real, and \emph{recall} asks what share of the real
events we flagged. They pull against each other, since flagging more rows raises recall and
lowers precision. \emph{F1} combines the two. For an alert system this trade-off is the
whole design decision: a missed outbreak costs lives, and crying wolf costs attention,
because owners stop reading.

\paragraph{Why PR-AUC instead of accuracy.} Sort every row by predicted risk, walking from
most to least risky, and at each step compute precision and recall. The area under that
curve is PR-AUC, which answers how quickly picking the riskiest rows surfaces real events. A
method with no skill scores the prevalence, 0.056 here. The 2,906 easy negative rows cannot
inflate it, which is why it suits rare events. ROC-AUC has the opposite weakness: the large
negative class makes a mediocre model look strong. We report it so our numbers can be
compared with other papers.

\paragraph{Calibration.} A ranking can sort countries, but a message quoting a ``30\%
chance'' needs that number to be true. We group predictions into buckets and compare each
bucket's average prediction with how often the event happened. The averaged gap is
the expected calibration error, or ECE, which is ECE here. The correction is fitted on
training data only, and it never reorders rows, only the numbers on the axis.

\paragraph{SHAP.} SHAP comes from cooperative game theory. If each feature were a player
contributing to a prediction, what is each player's fair share of the credit? Fair here
means averaging the contribution over every possible order in which features could be
added. One property makes it far more useful than simpler measures:

\begin{quote}
\small The contributions add up exactly to the gap between the model's average prediction
and this particular prediction.
\end{quote}

That property is called local accuracy. It lets us say that a prediction is 54\% rather
than the 5.6\% average, and give the exact breakdown of why, with nothing left over.

FIGURE_SHAP

SHAP distributes credit \emph{inside} the model. When two features carry the same
information the split between them is arbitrary, and a large value is not evidence of
cause.

% =====================================================================
\section{Results}
\label{sec:results}
% =====================================================================

\begin{table}[htbp]
\centering
\caption{Main results. Every column except Precision and Recall is a 0 to 1 score where
higher is better. The first four columns come from the time split, where the model is tested
on later years. The fifth repeats the main score under the harder country split, where the
model is tested on unseen countries. Precision and Recall describe what happens at the
alert threshold on the time split.}
\small
\resizebox{\textwidth}{!}{%
\begin{tabular}{@{}lcccccc@{}}
\toprule
\textbf{Model} & \textbf{PR-AUC} & \textbf{95\% interval} & \textbf{ROC-AUC} &
\textbf{PR-AUC} & \textbf{Precision} & \textbf{Recall} \\
 & \textbf{(time split)} & \textbf{on PR-AUC} & \textbf{(time split)} &
\textbf{(country split)} & \textbf{(time split)} & \textbf{(time split)} \\
\midrule
RESULTS_TABLE
\bottomrule
\end{tabular}}
\end{table}

The two PR-AUC columns measure the same thing on different tests. Time split trains on 2005
to 2017 and tests on 2018 to 2023. Country split trains without some countries and tests on
those, which is harder and closer to real use. Neither is a precision score.

PR-AUC sits at 0.056 for a model with no skill. On the time split the best model reaches
BEST_PR; on the country split, which is closer to real use, the logistic regression leads at
CHAMP_LOCO. The uncertainty column is wide: with 74 positives in the test years a score can
move a long way within that range, so neighbouring models should not be separated with
confidence.

The ensembles lead on the time split, but on the country split the logistic regression is
ahead, and the single tree comes last on both. With only fourteen inputs the relationships are
close enough to additive that a regularised linear model transfers best.

"""
