"""Chapter 6: The RAG explanation layer."""

BODY_RAG = r"""
% =====================================================================
\chapter{The RAG Explanation Layer}
\label{ch:rag}
% =====================================================================

\section{The Problem This Layer Solves}

A calibrated probability of 0.24 is actionable for a veterinary officer and meaningless for an
equine owner. The owner needs to know what happened, what it means for their animals, and what to
do next. The officer needs to know which factors drove the number, because a forecast they cannot
interrogate is a forecast they will not act on.

The obvious answer is to ask a large language model to explain the prediction. The obvious problem
is that a language model asked about glanders will answer from its training data, which may be
outdated, may conflate glanders with melioidosis, and may invent a treatment protocol. For a
zoonosis with a statutory control programme, an invented instruction is worse than no instruction.

Retrieval-augmented generation \cite{lewis2020} resolves this by changing what the model is
allowed to use. The
model is not asked what it knows about glanders. It is given a small set of passages retrieved
from official guidance, given the prediction's own numbers, and asked to answer using only those.
Every claim must be traceable to a passage, and the passage must be shown to the reader.

The design goal is therefore narrow and testable: produce an answer that a veterinary officer
would accept as consistent with the National Action Plan, and refuse rather than guess when the
corpus does not support an answer.

\section{Why Retrieval Rather Than Fine-Tuning}

Fine-tuning a model on glanders documents would produce fluent text with no citations and no way
to tell whether a statement came from the guidance or from the base model's priors. It would also
freeze the knowledge at training time, so a revised National Action Plan would require retraining.

Retrieval keeps the knowledge in a corpus that can be updated by re-ingesting a document, makes
every answer auditable by construction, and allows a refusal path that fine-tuning does not. The
cost is latency and the possibility of retrieval failure, both of which are handled explicitly
below.

\section{Knowledge Base}

The corpus is restricted to sources with authority, because the layer's value is that it cites
them. Each document carries an authority tier, which is used as a tie-breaker during retrieval.

\begin{table}[htbp]
\centering
\caption{Knowledge base, by authority tier.}
\label{tab:corpus}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{5.3cm}>{\raggedright\arraybackslash}p{2.2cm}>{\raggedright\arraybackslash}p{6.6cm}@{}}
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

Tier 3 material is allowed to inform an explanation but is never allowed to override tier 1 on a
control instruction. When two passages conflict, the higher tier wins and the conflict is logged,
because a silent contradiction between sources is exactly the failure this layer exists to
prevent.

\section{Ingestion and Chunking}

Ingestion runs offline as a job, not per request. A document is parsed, split at section
boundaries, and each chunk is stored with enough metadata to be cited and filtered.

Chunking is section-aware rather than fixed-width. A fixed 512-token window cuts control
instructions in half, so a retrieved chunk can end mid-sentence and the model completes it. The
splitter therefore respects heading structure first, then paragraph boundaries, and only falls back
to a sliding window for a section longer than the chunk ceiling.

\begin{table}[htbp]
\centering
\caption{Chunking parameters.}
\label{tab:chunking}
\small
\begin{tabular}{@{}lr@{}}
\toprule
\textbf{Parameter} & \textbf{Value} \\
\midrule
Target chunk size & 400 to 700 tokens \\
Overlap & 15 per cent, applied only within a section \\
Minimum chunk & 80 tokens, shorter sections merged into the parent \\
Metadata retained & doc id, title, section path, page, year, authority tier \\
\bottomrule
\end{tabular}
\end{table}

The section path is retained in full, for example
\texttt{NAP-2025 > 5.2 Movement control}, so a citation can point to a specific
subsection rather than to a 90-page document.

\section{Embedding and Index}

Chunks are embedded and stored in pgvector alongside the relational tables. Keeping the vectors in
the same database as the predictions removes a synchronisation problem: a re-ingestion and a
prediction are covered by the same transaction boundary, and there is no second store to keep
consistent.

The default model is a compact sentence-transformer \cite{reimers2019} producing
384-dimensional vectors, which is
sufficient for a corpus of this size and cheap enough to embed on a laptop. A multilingual variant
is used when the corpus or the questions are in Hindi, because an English-only embedding degrades
badly on Devanagari text.

The index is HNSW with cosine distance \cite{malkov2020}. An approximate index is acceptable here because the
reranker corrects recall at the top of the list, and the corpus is small enough that even exact
search would be fast; the index is there to keep the query cost flat as the corpus grows.

\section{Retrieval}

Figure~\ref{fig:rag} shows the complete layer, with ingestion as an offline job along the top and
the per-request path below.

\input{fig_rag.tex}

Retrieval is hybrid, because dense and lexical search \cite{robertson2009} fail in different ways
on this corpus. A
dense query for "what should I do if I suspect glanders" retrieves passages about suspicion, which
is useful. A dense query for the exact phrase "movement control" may miss a passage that uses
"restriction of equid movement", where a lexical match would succeed. Conversely a lexical query
for a rare acronym retrieves noise that a dense query would ignore.

Both result lists are retrieved, then fused by reciprocal rank fusion \cite{cormack2009}, which
combines rankings without requiring the two scores to be on a comparable scale.

\[
\mathrm{RRF}(d) = \sum_{i \in \{\text{dense},\text{lexical}\}} \frac{1}{k + \mathrm{rank}_i(d)},
\qquad k = 60
\]

The fused top fifty are then reranked by a cross-encoder that scores each passage against the
question jointly. A cross-encoder is much slower per pair than an embedding dot product, which is
why it runs on fifty candidates rather than on the corpus. The top five surviving passages become
the context.

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

The relevance floor is the mechanism behind the refusal path. If fewer than two passages clear it,
the layer returns a refusal with the SHAP factors instead of an answer, because a context assembled
from marginal passages produces a confident answer built on nothing.

\section{Context Assembly}

The prompt is assembled from three parts, in this order: a fixed system instruction, the retrieved
passages with identifiers, and the structured prediction facts.

The prediction facts are what make the answer specific to this forecast rather than to glanders in
general. They are injected as structured data rather than as prose, so the model cannot restate a
factor as causal when it is only associated.

\begin{verbatim}
Area:            IN-UP-057, period 2026-11
Risk level:      HIGH
Probability:     0.2431  (calibrated; 4.3x the base rate)
Model:           gw-xgb-2026.11.1
Top factors:     equid_density      +0.184
                 recent_events_2y   +0.121
                 temp_anomaly       -0.038

Passages:
[P1] dahd-nap-2025, 5.2 Movement control
     ...
[P2] woah-glanders-2024, Epidemiology
     ...
\end{verbatim}

The system instruction is fixed and is not influenced by user input. It states four constraints:
answer only from the passages; cite every claim with a passage identifier; never diagnose an
individual animal; and state that the output is a population-level forecast.

\section{Generation}

Generation uses temperature 0.1 and a bounded output length. A low temperature is chosen not for
creativity but for consistency: two officers asking the same question about the same area should
receive the same instruction, and a creative sampling temperature makes that untrue.

The provider sits behind an interface with a single method, so the same retrieval, grounding and
citation code runs against a local model served by Ollama or a hosted API. This is the reuse path
described in Chapter~\ref{ch:arch}: the guardrails are provider-independent, so switching model
cannot silently disable them.

\section{Guardrails}

The layer is designed to refuse. Four checks run, and any of them can terminate the response.

\begin{table}[htbp]
\centering
\caption{Guardrails and their failure behaviour.}
\label{tab:guardrails}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.2cm}>{\raggedright\arraybackslash}p{5.0cm}>{\raggedright\arraybackslash}p{5.6cm}@{}}
\toprule
\textbf{Check} & \textbf{What it verifies} & \textbf{On failure} \\
\midrule
Retrieval floor & At least two passages above the relevance threshold & Refusal with the top SHAP factors, which need no retrieval \\
Citation resolution & Every cited identifier exists in the retrieved set & Answer rejected and regenerated once; then refusal \\
Diagnosis scope & No individual-animal diagnosis or treatment prescription & Response rewritten without the clinical claim, and the attempt is logged \\
Out-of-scope & Question is about glanders control, not unrelated topics & Refusal with a statement of what the layer covers \\
\bottomrule
\end{tabular}
\end{table}

The citation check is the important one and is mechanical rather than prompted. The answer is
parsed for citation identifiers, and each one is looked up in the retrieved set. An identifier that
does not resolve means the model cited a document it was not given, which is a hallucination
regardless of whether the sentence happens to be true. Prompting the model to be accurate is not a
control; checking its output is.

\section{Evaluation}

The layer is evaluated on four things, none of which is whether the prose reads well.

\textbf{Retrieval quality.} A hand-built set of questions with known relevant passages, scored by
recall@5 and mean reciprocal rank. This isolates retrieval from generation: if the right passage is
not retrieved, no amount of generation quality helps.

\textbf{Faithfulness.} Whether each claim in an answer is supported by the retrieved context,
scored by a judge model and reviewed manually on a sample. This is the metric that catches a
model that cites a passage but states something the passage does not say.

\textbf{Citation precision.} The fraction of citations that resolve to a passage that supports
the sentence they are attached to. Distinct from resolution, which only checks existence.

\textbf{Refusal behaviour.} The refusal rate on a set of deliberately out-of-scope and
underdetermined questions, and the false refusal rate on questions the corpus does answer. A layer
that never refuses is unsafe; a layer that always refuses is useless. Both numbers are reported.

The evaluation set is built from the questions the layer is designed to answer, not from
generic reading-comprehension data, because the failure modes that matter here are specific to
control guidance.

\section{Worked Example}

The following is the intended shape of a response for a high-risk area, with citations to the
corpus described above.

\begin{quote}
\small
\textbf{Question.} Why is district IN-UP-057 rated HIGH this month?

\textbf{Answer.} Risk is elevated mainly because the district has a high equine density and there
has been reported glanders activity in the surrounding districts within the last two years.
Animals in areas with recent reported activity are at higher risk, and movement of equids is a
recognised route of spread [P1]. Owners are advised to avoid unnecessary movement or mixing of
equids, to isolate animals showing nasal discharge or skin lesions, and to inform the local
veterinary authority rather than attempt treatment themselves [P1, P2]. Glanders is zoonotic, so
handlers should use gloves when examining a suspected animal [P2].

This is a population-level forecast for the area. It is not a diagnosis of any individual animal,
and suspected cases require laboratory confirmation [P1].
\end{quote}

Every sentence in that answer is attributable to a retrieved passage, the control instruction cites
the National Action Plan, the zoonotic warning cites the WOAH sheet, and the disclaimer is
appended by the layer rather than generated.

\section{What Would Be Tested Before Deployment}

Because the layer is specified rather than deployed, the validation that would precede deployment
is stated explicitly, so the claim is falsifiable.

\begin{enumerate}
  \item Recall@5 above 0.85 on the hand-built question set.
  \item Faithfulness above 0.90 on a manually reviewed sample of 100 answers.
  \item Citation precision above 0.95, with every failure inspected by hand.
  \item Zero individual-animal diagnoses across the adversarial probe set.
  \item Refusal on every question in the out-of-scope set, and a false refusal rate below 10 per
        cent on the in-scope set.
  \item p95 latency under two seconds for the full path on the reference hardware.
\end{enumerate}

These are targets, not results. The distinction is maintained throughout this chapter because the
layer has not been run against the corpus at the time of writing.
"""

BODY_ALERT = r"""
% =====================================================================
\chapter{The Alert Service}
\label{ch:alerts}
% =====================================================================

\section{Why the Alert Is the Hard Part}

The risk engine produces a probability and the RAG layer explains it, but neither reaches the
person who owns the animals. For most Indian equid owners the interaction is a message on a phone,
not a dashboard, and the message competes with everything else on that phone.

The design problem is therefore not how to send a message. It is how to send few enough messages
that the ones which arrive are read. A system that warns about every area every month trains its
users to ignore it, and then fails silently at exactly the moment it was built for. Alert fatigue
is the dominant failure mode of an early-warning system for a rare disease, and the rules below
exist to prevent it.

\section{Trigger Path}

The service is event-driven. When the prediction job completes it publishes
\texttt{predictions\_ready}, and the alert evaluator consumes it. There is no polling and no
scheduled evaluation of its own, which means an alert can never be sent for a period whose
predictions were not recomputed.

\input{fig_alertflow.tex}

For each area with at least one active subscription, the evaluator reads the new prediction and the
area's previous alert state. Those two values are the entire input to the rules. The evaluator does
not read features or model internals, so a model change cannot alter alert behaviour except through
the probability it produces.

\section{Rule 1: Threshold with Hysteresis}

The calibrated probability is mapped to one of three levels. The boundaries are configuration
values derived from the operating curve in Chapter~\ref{ch:results}, not defaults and not 0.5.

\begin{table}[htbp]
\centering
\caption{Level thresholds and their basis.}
\label{tab:thresholds}
\small
\begin{tabular}{@{}p{1.8cm}p{2.8cm}p{5.0cm}p{3.2cm}@{}}
\toprule
\textbf{Level} & \textbf{Band} & \textbf{Meaning for the recipient} & \textbf{Basis} \\
\midrule
LOW & below the medium boundary & No message. Routine monitoring. & Below the alert budget where precision collapses \\
MEDIUM & medium to high boundary & Prepare; check animals; note the veterinary contact & Operating point where recall exceeds 80 per cent \\
HIGH & above the high boundary & Act: restrict movement, isolate suspects, inform the authority & Top of the operating curve, precision above 0.5 \\
\bottomrule
\end{tabular}
\end{table}

Hysteresis addresses a specific defect. With a single boundary, an area whose probability oscillates
around the threshold produces an alert every period, because each crossing is a state change. The
rule therefore uses two boundaries: an area enters HIGH at the high threshold and only leaves HIGH
when the probability falls below that threshold minus a margin.

\[
\text{enter HIGH at } p \ge T_H, \qquad
\text{leave HIGH only at } p < T_H - \delta, \qquad \delta = 0.05
\]

The margin is configurable per disease. A larger margin produces a more stable state at the cost of
slower de-escalation, and for a disease where the cost of a missed warning exceeds the cost of a
late all-clear, that trade is the right one.

\section{Rule 2: Suppression}

Suppression decides whether a message is warranted at all, given that the level has changed. Six
conditions are applied, and any one of them can stop the message.

\begin{table}[htbp]
\centering
\caption{Suppression conditions.}
\label{tab:suppression}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{3.1cm}>{\raggedright\arraybackslash}p{5.2cm}>{\raggedright\arraybackslash}p{5.5cm}@{}}
\toprule
\textbf{Condition} & \textbf{Rule} & \textbf{Rationale} \\
\midrule
State change & Send only on a transition, not while the level is held & A monthly reminder at the same level carries no new information \\
Cooldown & No repeat of the same level within a configurable window & Prevents oscillation at a level boundary from producing repeated messages \\
Escalation bypass & An upward transition ignores the cooldown & A genuine worsening must never be delayed by a timer \\
Per-user daily cap & At most one message per recipient per day & Protects against several areas escalating at once \\
Quiet hours & Nothing sent between 21:00 and 07:00 local time; queued instead & A warning that wakes a household at night is resented, and is not actionable then \\
Stale-data guard & No send if \texttt{data\_freshness.passes} is false & An alert about a prediction computed on stale inputs is worse than no alert \\
\bottomrule
\end{tabular}
\end{table}

A manual mute per area is also supported, so an officer who knows a zone is under active
surveillance can silence it without disabling the service.

De-escalation is handled separately: when a level falls, an optional short all-clear is sent,
because a recipient who was told to act needs to be told when to stop. Whether that message is sent
is a configuration choice, since an all-clear costs a message but prevents a user from maintaining
a restriction indefinitely.

\section{Rule 3: Deduplication}

The service must be safe to re-run. Jobs are retried, deployments restart workers, and a model may
be re-scored for the same period. None of those events may produce a second message.

Deduplication is enforced at three levels, each with its own key and its own database constraint.

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

The first two are unique constraints in the database, so the protection does not depend on
application logic being correct. The alert identifier is derived deterministically from its key
rather than generated randomly, so two concurrent workers computing the same alert arrive at the
same identifier and one of them loses the insert. A random identifier would let both succeed.

The send-level check reads the delivery log before each attempt. This handles the specific case
where a provider accepts a message, the response times out, and the retry would otherwise deliver
it twice.

\section{Fan-Out and Channels}

\begin{figure}[htbp]
\centering
\includegraphics[width=\textwidth]{proposal_alert_architecture.png}
\caption{The alert pipeline as specified in the project proposal, showing the stages downstream of
the rule decision: fan-out to one job per subscription, template rendering, channel adapters,
retry with backoff, and delivery status flowing back to the admin dashboard.}
\label{fig:alertarch}
\end{figure}

Once an alert record exists, one delivery job per subscription is queued through Redis. A channel
adapter receives a rendered message and a recipient, and returns a delivery status. Adapters exist
for SMS, WhatsApp and Telegram, the last of which is used for demonstration because it requires no
commercial onboarding.

Retries use exponential backoff with jitter. A permanent failure, such as an invalid number, is not
retried; a transient failure, such as a provider timeout, is. The distinction is recorded in the
delivery log, because a silent permanent failure means a subscriber who believes they are covered
and is not.

Templates are separate from the rules engine. The engine produces a level and a set of facts; the
template renderer produces the words, in the recipient's chosen language. English and Hindi are
supported, and adding a language adds a template set rather than touching the rules.

\section{Worked Example}

A HIGH alert as rendered for SMS. The length is bounded because a long message is truncated by the
carrier, and a truncated message that loses the action instruction is worse than a short one.

\begin{verbatim}
GLANDERS WATCH  |  IN-UP-057  |  NOV 2026
Risk: HIGH (was MEDIUM)
Elevated risk for your area. Avoid unnecessary
movement or mixing of equids. Isolate animals with
nasal discharge or skin lesions and inform the local
veterinary authority.
Helpline: <district veterinary contact>
Forecast for the area, not a diagnosis.
\end{verbatim}

The same alert delivered through a richer channel carries the explanation paragraph from the RAG
layer, with its citations. The rule that decides whether a message is sent is identical; only the
adapter and the template differ. That separation is what allows one alert to serve a feature phone
and a smartphone without duplicating the decision logic.

\section{Evaluation of the Alert Layer}

The service is evaluated as a warning system, not as a messaging system. Four quantities matter.

\textbf{Alert precision.} Of the area-periods that triggered a HIGH alert, what fraction were
followed by a documented event. This is the number that determines whether recipients trust the
message.

\textbf{Event coverage at budget.} The fraction of events captured as a function of the number of
areas alerted, which is the operating curve already reported in Chapter~\ref{ch:results}. The
thresholds are read off this curve, which is what connects the modelling in this report to the
behaviour of the service.

\textbf{Noise per recipient.} Messages per subscriber per year. This is the maintainability metric,
because it predicts whether the service will still be read in its second year.

\textbf{Delivery reliability.} The fraction of queued deliveries that reached a terminal success
state within the retry window, reported per channel, since channels fail differently.

The first two are computed from historical predictions and labels. The last two require a deployed
service and are stated as the protocol that would measure them rather than as results.
"""
