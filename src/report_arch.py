"""Chapter 3: System Architecture. The modularity and reusability argument."""

BODY_ARCH = r"""
% =====================================================================
\chapter{System Architecture}
\label{ch:arch}
% =====================================================================

\section{What the Platform Has to Do}

The platform answers one question and produces three kinds of output from it. The question is
whether glanders is likely to be documented in a given area in the next period. The outputs are a
number on a map, an explanation in words, and a message to an owner. Each output is consumed by a
different person, at a different time, through a different device, and each can fail without the
others failing.

That asymmetry is the reason the system is built as three components rather than one application.
A district officer looking at a map needs the prediction immediately and the explanation on
demand. An owner with a feature phone needs a short message and nothing else. A researcher
auditing a decision needs the cited passages months later. Building a single service that serves
all three would tie the alert delivery rate to the latency of an LLM call and would make the risk
model impossible to test on its own.

\input{fig_architecture.tex}

\section{Design Principles}

Five rules govern the decomposition. They are stated explicitly because every later design
decision follows from them, and because they are the part of this project that transfers to other
diseases.

\subsection*{1. One responsibility per component}

Each component owns exactly one transformation. The risk engine turns features into a calibrated
probability. The RAG layer turns a prediction into a cited explanation. The alert service turns a
prediction into a delivered message. None of them computes something another one could compute
instead.

\subsection*{2. Contracts before implementations}

Components exchange versioned schemas, never shared database tables or in-process calls. The
contract is defined first, and each side can be built, tested and deployed against a fixture that
satisfies it. This is what allows the RAG layer to be developed while the alert service is still
being written.

\subsection*{3. The core is disease-agnostic}

Nothing in the risk engine, the RAG layer or the alert service hardcodes glanders. A disease is a
configuration record: which label extractor to use, which knowledge-base collection to retrieve
from, which message templates to render, which thresholds to apply. Adding a second disease is a
configuration change plus a retrain, not a code fork.

\subsection*{4. Fail soft, never fail silent}

A degraded component returns a degraded answer, not an error to the user. If the RAG layer is
unavailable, the alert is still delivered, with the risk level and the standing action text but
without the explanation paragraph. If the explanation is requested and retrieval returns nothing
above the relevance floor, the layer returns a refusal plus the top SHAP factors, which are
computed by the model and do not depend on the LLM. Neither case produces a wrong statement, and
neither produces silence.

\subsection*{5. Every output is traceable}

Every prediction carries the model version that produced it. Every explanation carries the
document identifiers it was grounded in. Every alert carries the prediction that triggered it and
the rule outcomes that allowed it. A decision can therefore be reconstructed after the fact, which
is the minimum requirement for a tool that advises on animal disease.

\section{The Three Components}

\begin{table}[htbp]
\centering
\caption{Component responsibilities, interfaces and failure behaviour.}
\label{tab:components}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{2.35cm}>{\raggedright\arraybackslash}p{3.35cm}>{\raggedright\arraybackslash}p{3.5cm}>{\raggedright\arraybackslash}p{4.5cm}@{}}
\toprule
\textbf{Component} & \textbf{Responsibility} & \textbf{Interface} & \textbf{On failure} \\
\midrule
ML risk engine & Features to calibrated probability, with attribution & \texttt{POST /v1/predict}, \texttt{GET /v1/risk-map} & Returns \texttt{503} with the champion version id; the last good prediction stays in the table and is marked stale. \\
RAG layer & Prediction plus question to a cited explanation & \texttt{POST /v1/explain}, \texttt{POST /v1/chat} & Alert text is sent without the explanation paragraph; the chat endpoint returns a refusal rather than an ungrounded answer. \\
Alert service & Prediction to a delivered, deduplicated message & \texttt{POST /v1/alerts/evaluate}; consumes \texttt{predictions\_ready} & Alerts queue in Redis and drain on recovery; the map and explanations are unaffected. \\
\bottomrule
\end{tabular}
\end{table}

\section{Component Contracts}

A contract here means a JSON schema plus the guarantees that accompany it. The three schemas
below are the actual interfaces between the components. They are deliberately small, because a
narrow contract is what makes a component replaceable.

\subsection*{PredictionRecord}

Emitted by the risk engine, consumed by all three downstream outputs.

\begin{verbatim}
{
  "schema_version": "1.0",
  "area_id":        "IN-UP-057",        // ISO 3166-2 where available
  "period":         "2026-11",
  "probability":    0.2431,             // calibrated, in [0,1]
  "risk_level":     "HIGH",             // LOW | MEDIUM | HIGH
  "model_id":       "gw-xgb-2026.11.1",
  "predicted_at":   "2026-11-08T00:12:04Z",
  "data_freshness": {"fao_days": 34, "nasa_days": 2, "passes": true},
  "top_factors": [
    {"feature": "equid_density",     "shap":  0.184, "direction": "increases"},
    {"feature": "recent_events_2y",  "shap":  0.121, "direction": "increases"},
    {"feature": "temp_anomaly",      "shap": -0.038, "direction": "decreases"}
  ]
}
\end{verbatim}

The guarantees that accompany it are: \texttt{probability} is calibrated on held-out data, so it
may be read as a frequency; \texttt{risk\_level} is derived from \texttt{probability} by the
threshold configuration, so the two cannot contradict each other; and \texttt{top\_factors} is
computed from the model itself, so it is available even when the RAG layer is not.

\subsection*{ExplainRequest and ExplainResponse}

\begin{verbatim}
// request
{ "schema_version": "1.0",
  "prediction": <PredictionRecord>,
  "question":   "Why is this area high risk?",
  "language":   "en" }

// response
{ "schema_version": "1.0",
  "answer":     "Risk is elevated mainly because ...",
  "citations": [ {"doc_id": "dahd-nap-2025", "section": "5.2", "page": 18},
                 {"doc_id": "woah-glanders-2024", "section": "Epidemiology"} ],
  "grounded":   true,
  "refusal":    null,
  "latency_ms": 1840 }
\end{verbatim}

The response is grounded when at least one citation resolves to a retrieved passage. A refusal
carries \texttt{grounded: false}, a reason code and no answer text, so a caller cannot render a
refusal as if it were an explanation.

\subsection*{AlertEvent}

\begin{verbatim}
{ "schema_version": "1.0",
  "alert_id":     "a7f3...",           // deterministic, see Section 7.4
  "area_id":      "IN-UP-057",
  "period":       "2026-11",
  "level":        "HIGH",
  "previous":     "MEDIUM",
  "prediction_id": "...",              // foreign key to the prediction
  "rules":        {"threshold": "pass", "suppression": "escalation",
                   "deduplication": "new"},
  "recipients":   42 }
\end{verbatim}

\section{Shared Data Model}

The components share a database but not tables. Each table has a single owning writer, and the
others read it; no component updates another's rows.

\begin{table}[htbp]
\centering
\caption{Core tables and their owning writer.}
\label{tab:tables}
\small
\begin{tabular}{@{}p{3.5cm}p{2.5cm}p{4.0cm}p{2.4cm}@{}}
\toprule
\textbf{Table} & \textbf{Owner} & \textbf{Key} & \textbf{Read by} \\
\midrule
\texttt{observations} & ingestion job & \texttt{(area\_id, period)} & risk engine \\
\texttt{features} & feature job & \texttt{(area\_id, period)} & risk engine \\
\texttt{model\_versions} & training job & \texttt{model\_id} & risk engine, dashboard \\
\texttt{predictions} & risk engine & \texttt{(area\_id, period, model\_id)} & all three \\
\texttt{documents}, \texttt{chunks} & RAG ingestion & \texttt{(doc\_id, chunk\_id)} & RAG layer \\
\texttt{subscriptions} & API & \texttt{subscription\_id} & alert service \\
\texttt{alerts} & alert service & \texttt{(area\_id, period, level)} unique & dashboard \\
\texttt{alert\_delivery\_logs} & alert service & \texttt{(alert\_id, subscription\_id)} & dashboard \\
\bottomrule
\end{tabular}
\end{table}

Spatial columns use PostGIS geometry, and document embeddings use pgvector, so spatial and vector
queries run in the same database as the relational joins. This removes a synchronisation problem
that a separate vector store would introduce.

\section{Implementation Status}

The report distinguishes throughout between what has been built and evaluated and what has been
specified. Table~\ref{tab:status} is the honest summary.

\begin{table}[htbp]
\centering
\caption{Status of each part of the platform at the time of writing.}
\label{tab:status}
\small
\begin{tabular}{@{}>{\raggedright\arraybackslash}p{4.1cm}>{\raggedright\arraybackslash}p{2.5cm}>{\raggedright\arraybackslash}p{6.6cm}@{}}
\toprule
\textbf{Part} & \textbf{Status} & \textbf{Evidence in this report} \\
\midrule
ML risk engine & Built and evaluated & Panel construction, six model families, three validation schemes, calibration, ablation, SHAP (Chapters 4 and 8). Every number is reproducible from the committed scripts. \\
Model serving and MLOps & Designed, contract fixed & Endpoint specification, model-bundle format, request lifecycle, monitoring plan (Chapter 5). The model object exists and is serialisable; the HTTP layer is specified rather than deployed. \\
RAG layer & Designed, contract fixed & Corpus definition, chunking, hybrid retrieval, reranking, grounding and citation checks, evaluation protocol (Chapter 6). \\
Alert service & Designed, contract fixed & Three rules with their exact semantics, fan-out, delivery logging, worked example (Chapter 7). \\
Dashboard & Out of scope & Named as the fourth consumer in the architecture; not specified in detail here. \\
\bottomrule
\end{tabular}
\end{table}

The distinction matters for how the report should be read. The evaluation results in Chapter 8
are measurements. The RAG and alert chapters specify behaviour precisely enough to be
implemented and tested, and they state the tests that would validate them, but they do not report
measured performance, because the system is not deployed.

\section{Modularity and Reuse}

The decomposition is only worth its overhead if the parts can be reused. Five concrete reuse
paths follow from the design, and each is a small change rather than a rewrite.

\textbf{Another disease.} The risk engine reads its label extractor, feature groups and
thresholds from a disease configuration. A second disease supplies a new gazetteer and lexicon
for extraction, a new guidance collection for retrieval, and its own tuned thresholds. The
modelling code does not change, because it never refers to glanders by name.

\textbf{Another LLM provider.} The RAG layer calls a provider interface with a single completion
method, which takes a system instruction, a context block and a question, and a provider adapter
supplies that method for either a local model served by Ollama or a hosted API. Switching provider is a configuration value. The retrieval and
guardrail code is provider-independent, so the citation check and the refusal path behave
identically either way.

\textbf{Another notification channel.} A channel adapter exposes one send operation, which takes
a recipient and a rendered message and returns a delivery status. Adding a channel means
adding an adapter and a template, not touching the rules engine, which never knows which channel
will carry the message.

\textbf{Embedding the engine as a library.} The trained pipeline is a scikit-learn compatible
object with \texttt{predict\_proba}, exported with a manifest that records its feature order,
its calibration and its metrics. Any Python process can load it without running the API, which is
what makes offline batch scoring and notebook analysis possible.

\textbf{Replacing the model.} Because the prediction record carries \texttt{model\_id} and the
registry keeps previous versions, a new model can be scored against the incumbent on a shadow
period before promotion. Nothing downstream changes, since downstream components read the record
and not the model.

\section{Deployment}

The services are containerised and described by a single Docker Compose file: the API, the worker,
PostgreSQL with PostGIS and pgvector, Redis, and the frontend. This keeps the local demonstration
and a server deployment identical in structure, which matters for a project whose claims are about
reproducibility.

The scheduled path is a Celery beat job that runs the feature job, then the prediction job, then
publishes \texttt{predictions\_ready}. Alerts and explanations are computed after that event, so a
failed explanation never blocks a prediction and a failed prediction never sends an alert about
stale data.
"""
