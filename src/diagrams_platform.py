"""TikZ diagrams for the platform chapters: component architecture, model
serving, the RAG pipeline and the alert rules engine.

Separate from diagrams.py so the existing training/evaluation figures stay
exactly as they were. Pure LaTeX, so everything stays vector-sharp.
"""

ARCHITECTURE = r"""
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
  comp/.style={rectangle,rounded corners=3pt,draw=blue!55!black,fill=blue!7,
               align=center,minimum height=1.05cm,text width=3.35cm,
               font=\scriptsize\sffamily,inner sep=3pt},
  ext/.style={rectangle,rounded corners=2pt,draw=black!45,fill=black!4,
              align=center,minimum height=0.72cm,text width=3.35cm,
              font=\scriptsize\sffamily,inner sep=3pt},
  store/.style={cylinder,draw=teal!60!black,fill=teal!9,shape border rotate=90,
                aspect=0.22,minimum width=3.1cm,minimum height=1.15cm,
                font=\scriptsize\sffamily,align=center,inner sep=1pt},
  chan/.style={rectangle,rounded corners=2pt,draw=orange!70!black,fill=orange!10,
               align=center,minimum height=0.62cm,text width=3.35cm,
               font=\scriptsize\sffamily,inner sep=2pt},
  fl/.style={-{Stealth[length=1.9mm]},thick,draw=black!65},
  dfl/.style={-{Stealth[length=1.9mm]},thick,dashed,draw=black!45},
  clbl/.style={font=\tiny\sffamily,fill=white,inner sep=1.2pt,align=center},
]

  % ---- sources -----------------------------------------------------------
  \node[ext] (src) at (0,0)
    {\textbf{Public data sources}\\ Europe PMC $\cdot$ FAOSTAT $\cdot$ World Bank $\cdot$ NASA POWER};

  % ---- component 1 -------------------------------------------------------
  \node[comp,minimum height=1.30cm,text width=5.2cm] (c1) at (0,-1.55)
    {\textbf{Component 1 \quad ML Risk Engine}\\[2pt]
     train $\rightarrow$ calibrate $\rightarrow$ register a versioned model};

  % ---- prediction store --------------------------------------------------
  \node[store] (db) at (0,-3.35)
    {\textbf{predictions}, \texttt{model\_versions}\\
     PostgreSQL / PostGIS};

  % ---- the three consumers ----------------------------------------------
  \node[ext,text width=2.75cm] (dash) at (-4.15,-5.05)
    {\textbf{Web dashboard}\\ Next.js, MapLibre};

  \node[comp,text width=3.05cm] (c2) at (0,-5.05)
    {\textbf{Component 2 \quad RAG}\\ cited explanation};

  \node[comp,text width=3.05cm] (c3) at (4.15,-5.05)
    {\textbf{Component 3 \quad Alerts}\\ threshold $\cdot$ suppress $\cdot$ dedup};

  % ---- leaf stores -------------------------------------------------------
  \node[store,minimum width=2.6cm] (kb) at (0,-7.05)
    {\textbf{documents}, \texttt{chunks}\\ pgvector};
  \node[chan] (ch) at (4.15,-7.05)
    {SMS $\cdot$ WhatsApp $\cdot$ Telegram};

  % ---- edges -------------------------------------------------------------
  \draw[fl] (src) -- (c1);
  \draw[fl] (c1) -- node[clbl,right=2pt]{PredictionRecord} (db);

  \draw[fl] (db.south) -- ++(0,-0.30) -| ([xshift=-0.0cm]dash.north);
  \draw[fl] (db) -- (c2);
  \draw[fl] (db.south) -- ++(0,-0.30) -| (c3.north);

  \draw[dfl] (c2) -- node[clbl,right=2pt]{top-$k$} (kb.north);
  \draw[fl] (c3) -- node[clbl,right=2pt]{fan-out} (ch.north);

\end{tikzpicture}
\caption{The platform decomposed into three components. The ML risk engine
writes one \texttt{PredictionRecord} per area and period; the dashboard, the RAG
layer and the alert service consume it independently. No component reads another
component's tables, so any one of them can be replaced without touching the other
two.}
\label{fig:arch}
\end{figure}
"""

SERVING = r"""
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
  n/.style={rectangle,rounded corners=2pt,draw=black!50,fill=black!4,
            align=center,minimum height=0.62cm,text width=3.5cm,
            font=\scriptsize\sffamily,inner sep=2.5pt},
  hit/.style={rectangle,rounded corners=2pt,draw=teal!60!black,fill=teal!9,
              align=center,minimum height=0.62cm,text width=3.5cm,
              font=\scriptsize\sffamily,inner sep=2.5pt},
  stop/.style={rectangle,rounded corners=2pt,draw=orange!70!black,fill=orange!10,
               align=center,minimum height=0.56cm,text width=2.75cm,
               font=\scriptsize\sffamily,inner sep=2pt},
  fl/.style={-{Stealth[length=1.8mm]},thick,draw=black!65},
  l/.style={font=\tiny\sffamily,fill=white,inner sep=1pt,align=center},
]
  \node[n,text width=3.0cm]  (req)   at (0, 0.00) {POST \texttt{/v1/predict}};
  \node[n]                   (val)   at (0,-1.15) {Schema and range check};
  \node[hit]                 (cache) at (0,-2.30) {Redis lookup};
  \node[n]                   (load)  at (0,-3.45) {Load model bundle, check checksum};
  \node[hit]                 (pred)  at (0,-4.60) {Predict and calibrate};
  \node[n]                   (store) at (0,-5.75) {Write prediction, populate cache};
  \node[hit]                 (resp)  at (0,-6.90) {Response JSON};

  \node[stop] (rej) at (5.6,-1.15) {HTTP 422\ invalid payload};
  \node[stop] (hitn) at (5.6,-2.30) {return the\ cached record};
  \node[stop] (fb)  at (5.6,-3.45) {promote previous\ champion};

  \draw[fl] (req) -- (val);
  \draw[fl] (val) -- (cache);
  \draw[fl] (cache) -- (load);
  \draw[fl] (load) -- (pred);
  \draw[fl] (pred) -- (store);
  \draw[fl] (store) -- (resp);

  \draw[fl] (val.east) -- node[l,above=1pt]{fails} (rej.west);
  \draw[fl] (cache.east) -- node[l,above=1pt]{hit} (hitn.west);
  \draw[fl] (load.east) -- node[l,above=1pt]{fails} (fb.west);
\end{tikzpicture}
\caption{Request lifecycle of the prediction endpoint. Validation precedes model loading, the
cache is consulted before inference, and a bundle that fails its checksum or its feature-schema
check is replaced by the previous champion rather than served.}
\label{fig:serving}
\end{figure}
"""

RAG = r"""
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
  st/.style={rectangle,rounded corners=2pt,draw=black!50,fill=black!4,
             align=center,minimum height=0.62cm,text width=2.8cm,
             font=\scriptsize\sffamily,inner sep=2.5pt},
  doc/.style={rectangle,rounded corners=2pt,draw=blue!55!black,fill=blue!7,
              align=center,minimum height=0.62cm,text width=2.8cm,
              font=\scriptsize\sffamily,inner sep=2.5pt},
  gate/.style={rectangle,rounded corners=2pt,draw=orange!70!black,fill=orange!10,
               align=center,minimum height=0.62cm,text width=2.8cm,
               font=\scriptsize\sffamily,inner sep=2.5pt},
  emit/.style={rectangle,rounded corners=2pt,draw=teal!60!black,fill=teal!9,
               align=center,minimum height=0.62cm,text width=2.8cm,
               font=\scriptsize\sffamily,inner sep=2.5pt},
  fl/.style={-{Stealth[length=1.8mm]},thick,draw=black!65},
  dfl/.style={-{Stealth[length=1.8mm]},thick,dashed,draw=black!45},
  l/.style={font=\tiny\sffamily,fill=white,inner sep=1pt,align=center},
]
  % ---- offline ingestion, row 1 -----------------------------------------
  \node[doc] (corpus) at (0,0)      {Guidance corpus\ DAHD, WOAH, ICAR};
  \node[st]  (parse)  at (3.5,0)    {Section-aware\ chunking};
  \node[st]  (emb)    at (7.0,0)    {Embedding\ 384-dim};
  \node[emit] (idx)   at (10.5,0)   {pgvector index\ HNSW};

  % ---- online retrieval, row 2 ------------------------------------------
  \node[st] (q)   at (0,-2.35)   {User question\ plus area context};
  \node[st] (qe)  at (3.5,-2.35) {Query\ embedding};
  \node[st] (hyb) at (7.0,-2.35) {Hybrid recall\ dense and lexical};
  \node[st] (rr)  at (10.5,-2.35){Cross-encoder\ rerank};

  % ---- assembly and generation, row 3 (right to left) -------------------
  \node[st]   (ctx) at (10.5,-4.70) {Context\ assembly};
  \node[gate] (gen) at (7.0,-4.70)  {LLM\ temperature 0.1};
  \node[gate] (gd)  at (3.5,-4.70)  {Citation and\ scope check};
  \node[emit] (ans) at (0,-4.70)    {Cited answer\ plus disclaimer};

  \node[doc,text width=3.3cm] (facts) at (10.5,-6.55)
    {Prediction facts: risk level,\ probability, top-3 SHAP};

  \draw[fl] (corpus) -- (parse);
  \draw[fl] (parse) -- (emb);
  \draw[fl] (emb) -- (idx);

  \draw[fl] (q) -- (qe);
  \draw[fl] (qe) -- (hyb);
  \draw[fl] (hyb) -- (rr);

  \draw[fl] (idx) -- node[l,right=1pt]{top-50} (rr);
  \draw[fl] (rr) -- (ctx);
  \draw[fl] (ctx) -- (gen);
  \draw[fl] (gen) -- (gd);
  \draw[fl] (gd) -- node[l,above=1pt]{passes} (ans);

  \draw[dfl] (facts) -- node[l,right=1pt]{grounding} (ctx);
\end{tikzpicture}
\caption{The RAG layer. Ingestion (top row) is an offline job; retrieval, assembly and generation
(below) run per request. Predicted risk and SHAP factors are injected as structured facts, so the
answer explains this forecast rather than glanders in general. The citation check sits after
generation and can return a refusal instead of an unsupported answer.}
\label{fig:rag}
\end{figure}
"""

ALERT = r"""
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
  n/.style={rectangle,rounded corners=2pt,draw=black!50,fill=black!4,
            align=center,minimum height=0.62cm,text width=3.5cm,
            font=\scriptsize\sffamily,inner sep=2.5pt},
  rule/.style={rectangle,rounded corners=2pt,draw=orange!70!black,fill=orange!10,
               align=center,minimum height=0.62cm,text width=3.5cm,
               font=\scriptsize\sffamily,inner sep=2.5pt},
  ok/.style={rectangle,rounded corners=2pt,draw=teal!60!black,fill=teal!9,
             align=center,minimum height=0.62cm,text width=3.5cm,
             font=\scriptsize\sffamily,inner sep=2.5pt},
  stop/.style={rectangle,rounded corners=2pt,draw=red!50!black,fill=red!6,
               align=center,minimum height=0.56cm,text width=2.75cm,
               font=\scriptsize\sffamily,inner sep=2pt},
  fl/.style={-{Stealth[length=1.8mm]},thick,draw=black!65},
  l/.style={font=\tiny\sffamily,fill=white,inner sep=1pt,align=center},
]
  \node[n,text width=3.0cm] (ev)   at (0, 0.00) {\texttt{predictions\_ready}};
  \node[n]                  (eval) at (0,-1.15) {Alert evaluator\ per subscribed area};
  \node[rule]               (th)   at (0,-2.30) {Rule 1: threshold\ with hysteresis};
  \node[rule]               (sup)  at (0,-3.45) {Rule 2: suppression\ cooldown, hours, freshness};
  \node[rule]               (ded)  at (0,-4.60) {Rule 3: deduplication\ idempotency key};
  \node[ok]                 (fan)  at (0,-5.75) {Fan-out per subscription};
  \node[ok]                 (snd)  at (0,-6.90) {Channel adapter with backoff};
  \node[ok]                 (log)  at (0,-8.05) {Delivery log and status webhook};

  \node[stop] (s1) at (5.6,-3.45) {level unchanged\ or cooldown active};
  \node[stop] (s2) at (5.6,-4.60) {key already used};

  \draw[fl] (ev) -- (eval);
  \draw[fl] (eval) -- (th);
  \draw[fl] (th) -- (sup);
  \draw[fl] (sup) -- (ded);
  \draw[fl] (ded) -- (fan);
  \draw[fl] (fan) -- (snd);
  \draw[fl] (snd) -- (log);

  \draw[fl] (sup.east) -- node[l,above=1pt]{stop} (s1.west);
  \draw[fl] (ded.east) -- node[l,above=1pt]{stop} (s2.west);
\end{tikzpicture}
\caption{The alert rules engine. Each rule can terminate the path on its own, which is what keeps a
rare disease from generating routine noise: a level that has not changed and a key that has already
been used are both stops, and only an escalation bypasses the cooldown.}
\label{fig:alertflow}
\end{figure}
"""
