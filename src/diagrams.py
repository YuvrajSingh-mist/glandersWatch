"""TikZ diagrams: flowcharts for the training and evaluation pipelines, plus a
visual explanation of how SHAP and the model families work.

Kept as LaTeX so the diagrams stay vector-sharp in the PDF.
"""

PREAMBLE_LIBS = r"""\usetikzlibrary{shapes.geometric,arrows.meta,positioning,fit,backgrounds,calc,decorations.pathreplacing}"""

STYLES = r"""
\tikzset{
  src/.style={rectangle,rounded corners=2pt,draw=blue!55!black,fill=blue!7,
              align=center,minimum height=0.62cm,text width=2.55cm,
              font=\scriptsize\sffamily,inner sep=3pt},
  proc/.style={rectangle,rounded corners=2pt,draw=black!55,fill=black!4,
               align=center,minimum height=0.62cm,text width=2.55cm,
               font=\scriptsize\sffamily,inner sep=3pt},
  dec/.style={diamond,draw=orange!70!black,fill=orange!10,aspect=2.1,
              align=center,font=\scriptsize\sffamily,inner sep=1.5pt},
  res/.style={rectangle,rounded corners=2pt,draw=teal!60!black,fill=teal!8,
              align=center,minimum height=0.62cm,text width=2.55cm,
              font=\scriptsize\sffamily,inner sep=3pt},
  arr/.style={-{Stealth[length=1.8mm]},thick,draw=black!65},
  darr/.style={-{Stealth[length=1.8mm]},thick,dashed,draw=black!45},
  lbl/.style={font=\scriptsize\sffamily,inner sep=1.5pt,fill=white,align=center},
  grp/.style={rectangle,rounded corners=4pt,draw=black!25,fill=black!2,
              inner sep=6pt},
  hdr/.style={font=\scriptsize\sffamily\bfseries,anchor=south west,inner sep=1pt},
}
"""


# --------------------------------------------------------------------------- #
# 1. Training pipeline
# --------------------------------------------------------------------------- #
TRAINING = r"""
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
  st/.style={rectangle,rounded corners=2pt,draw=black!50,fill=black!4,
             align=center,minimum height=0.40cm,text width=7.0cm,
             font=\scriptsize\sffamily,inner sep=2.5pt},
  srcbox/.style={rectangle,rounded corners=2pt,draw=blue!55!black,fill=blue!7,
             align=center,minimum height=0.80cm,text width=9.0cm,
             font=\scriptsize\sffamily,inner sep=3pt},
  dec/.style={diamond,draw=orange!70!black,fill=orange!10,aspect=2.4,
              align=center,font=\scriptsize\sffamily,inner sep=1pt},
  final/.style={rectangle,rounded corners=2pt,draw=teal!60!black,fill=teal!8,
             align=center,minimum height=0.40cm,text width=7.0cm,
             font=\scriptsize\sffamily,inner sep=2.5pt},
  testb/.style={rectangle,rounded corners=2pt,draw=black!40,fill=white,
             align=center,minimum height=0.52cm,text width=2.9cm,
             font=\scriptsize\sffamily,inner sep=2.5pt},
  fl/.style={-{Stealth[length=1.7mm]},thick,draw=black!60},
  step/.style={font=\scriptsize\sffamily\bfseries,text=black!45,anchor=east},
]

  \node[srcbox] (src) at (0,0)
    {\textbf{1. Four public data sources}\\[2pt]
     Europe PMC (6{,}674 papers)\quad$\cdot$\quad FAOSTAT (7 stock series)\\
     World Bank (10 indicators)\quad$\cdot$\quad NASA POWER (6 climate measures)};

  \node[st,below=0.20cm of src] (clean) {\textbf{2. Clean}: reconcile country names to ISO-3, drop duplicates};
  \node[st,below=0.12cm of clean] (panel) {\textbf{3. Assemble panel}: 2{,}880 rows $\times$ 60 columns};
  \node[st,below=0.12cm of panel] (feat) {\textbf{4. Feature engineering}: lags, growth rates, climate anomalies};
  \node[st,below=0.12cm of feat] (shift) {\textbf{5. Shift targets}: answer comes from year $t{+}1$};
  \node[dec,below=0.18cm of shift] (split) {\textbf{6. Chronological split}};

  % training branch (down)
  \node[st,below=0.22cm of split] (train) {\textbf{7. Train on 2005--2017}, tuned inside training folds only};
  \node[st,below=0.12cm of train] (fit) {\textbf{8. Fit 6 model families}};
  \node[st,below=0.12cm of fit] (cal) {\textbf{9. Calibrate probabilities}, fitted on training folds};
  \node[st,below=0.12cm of cal] (sel) {\textbf{10. Select by leave-country-out PR-AUC}};
  \node[final,below=0.12cm of sel] (saved) {\textbf{11. Saved model + fixed alert threshold}};

  % test branch (right)
  \node[testb,right=0.42cm of split] (test) {\textbf{Test} years\\2018--2023\\\tiny never seen};

  \draw[fl] (src) -- (clean);
  \draw[fl] (clean) -- (panel);
  \draw[fl] (panel) -- (feat);
  \draw[fl] (feat) -- (shift);
  \draw[fl] (shift) -- (split);
  \draw[fl] (split) -- node[font=\scriptsize\sffamily,right=1pt,inner sep=1pt] {train} (train);
  \draw[fl] (train) -- (fit);
  \draw[fl] (fit) -- (cal);
  \draw[fl] (cal) -- (sel);
  \draw[fl] (sel) -- (saved);
  \draw[fl,dashed] (split.east) -- node[font=\scriptsize\sffamily,above,inner sep=2pt] {hold out} (test.west);

  % brace showing where leakage protection sits
  \draw[decorate,decoration={brace,amplitude=4pt,mirror},black!35]
       ([xshift=0.10cm]shift.north east) -- ([xshift=0.10cm]split.south east)
       node[midway,right=3pt,font=\tiny\sffamily,text=black!55,align=left]
       {split before\\any fitting};
\end{tikzpicture}
\caption{Training pipeline. The chronological split sits before any model sees the
data, so the 2018--2023 years never influence training. Tuning and calibration both
happen strictly inside the training years.}
\label{fig:trainflow}
\end{figure}
"""


# --------------------------------------------------------------------------- #
# 2. Evaluation pipeline
# --------------------------------------------------------------------------- #
EVALUATION = r"""
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
  bx/.style={rectangle,rounded corners=2pt,draw=black!50,fill=black!4,
             align=center,font=\scriptsize\sffamily,inner sep=2.5pt},
  top/.style={rectangle,rounded corners=2pt,draw=blue!55!black,fill=blue!7,
             align=center,font=\scriptsize\sffamily,inner sep=3pt},
  fin/.style={rectangle,rounded corners=2pt,draw=teal!60!black,fill=teal!8,
             align=center,font=\scriptsize\sffamily,inner sep=2.5pt},
  fl/.style={-{Stealth[length=1.7mm]},thick,draw=black!60},
]

  \node[top,text width=4.6cm,minimum height=0.5cm] (m) at (0,0)
       {\textbf{Trained model} + fixed alert threshold};

  % three schemes
  \node[bx,text width=3.0cm,minimum height=0.95cm] (s1) at (-5.0,-1.15)
       {\textbf{A. Time split}\\train 2005--17\\test 2018--23};
  \node[bx,text width=3.0cm,minimum height=0.95cm] (s2) at (0,-1.15)
       {\textbf{B. Country split}\\5 folds grouped\\by ISO-3};
  \node[bx,text width=3.0cm,minimum height=0.95cm] (s3) at (5.0,-1.15)
       {\textbf{C. Repeated CV}\\5 folds $\times$ 3 seeds\\\tiny stability check};

  \node[font=\tiny\sffamily,text=black!60,anchor=north,text width=3.0cm,align=center] (q1)
       at (-5.0,-1.80) {can we use it next year?};
  \node[font=\tiny\sffamily,text=black!60,anchor=north,text width=3.0cm,align=center] (q2)
       at (0,-1.80) {does it work in a new country?};
  \node[font=\tiny\sffamily,text=black!60,anchor=north,text width=3.0cm,align=center] (q3)
       at (5.0,-1.80) {are the scores stable?};

  % collector rail
  \coordinate (railL) at (-5.0,-2.42);
  \coordinate (railR) at (5.0,-2.42);
  \draw[fl] (s1.south) -- (railL);
  \draw[fl] (s2.south) -- (0,-2.42);
  \draw[fl] (s3.south) -- (railR);
  \draw[thick,draw=black!60] (railL) -- (railR);

  \node[bx,text width=11.4cm,minimum height=0.78cm] (met) at (0,-3.05)
       {\textbf{Predictions scored with}\\[1pt]
        PR-AUC (main) $\;\cdot\;$ ROC-AUC $\;\cdot\;$ Brier $\;\cdot\;$ calibration error
        $\;\cdot\;$ precision $\;\cdot\;$ recall $\;\cdot\;$ specificity $\;\cdot\;$ F1
        $\;\cdot\;$ MCC};
  \draw[fl] (0,-2.42) -- (met.north);

  \node[bx,text width=4.6cm,minimum height=0.62cm] (boot) at (-2.85,-4.02)
       {\textbf{1{,}000 bootstrap resamples}\\$\rightarrow$ 95\% interval};
  \node[bx,text width=4.6cm,minimum height=0.62cm] (alert) at (2.85,-4.02)
       {\textbf{Alert-budget curve}\\recall vs share warned};

  \node[fin,text width=4.6cm,minimum height=0.55cm] (pick) at (-2.85,-4.90)
       {\textbf{Pick model} by country-split PR-AUC};
  \node[fin,text width=4.6cm,minimum height=0.55cm] (sub) at (2.85,-4.90)
       {\textbf{Subgroup report}\\by region and income};

  \draw[fl] (met.south) -- ++(0,-0.16) -| (boot.north);
  \draw[fl] (met.south) -- ++(0,-0.16) -| (alert.north);
  \draw[fl] (boot) -- (pick);
  \draw[fl] (alert) -- (sub);

\end{tikzpicture}
\caption{Evaluation pipeline. One trained model is scored three different ways, each
answering a different question, then reported with uncertainty intervals.}
\label{fig:evalflow}
\end{figure}
"""


# --------------------------------------------------------------------------- #
# 3. Bagging vs boosting (explains the model families)
# --------------------------------------------------------------------------- #
ALGORITHMS = r"""
\begin{figure}[htbp]
\centering
\resizebox{\textwidth}{!}{%
\begin{tikzpicture}
  % =================== LEFT: BAGGING ===================
  \node[font=\footnotesize\sffamily\bfseries,anchor=south] (bht) at (0,0.05)
       {A. Bagging \textnormal{(random forest, extra trees)}};

  \node[proc,text width=2.5cm,anchor=north] (bd) at (0,-0.12) {one training set};

  \foreach \i/\x in {1/-2.7,2/-0.9,3/0.9,4/2.7} {
    \node[proc,text width=0.95cm,minimum height=0.52cm,anchor=north]
         (bt\i) at (\x,-0.95) {tree \i};
    \draw[arr] (bd.south) -- ++(0,-0.10) -| (bt\i.north);
  }
  \node[font=\tiny\sffamily,text=black!60,anchor=north,text width=6.4cm,align=center]
       at (0,-0.86) {};

  \node[proc,text width=2.1cm,anchor=north] (bavg) at (0,-1.78) {vote / average};
  \foreach \i/\x in {1/-2.7,2/-0.9,3/0.9,4/2.7} {
    \draw[arr] (bt\i.south) -- ++(0,-0.10) -| (bavg.north);
  }
  \node[res,text width=1.75cm,anchor=north] (bout) at (0,-2.58) {prediction};
  \draw[arr] (bavg) -- (bout);

  \node[font=\tiny\sffamily,text=black!60,anchor=north,text width=6.2cm,align=center]
       at (0,-3.16) {trees built \emph{in parallel}, each on a random subset};

  % =================== RIGHT: BOOSTING ===================
  \begin{scope}[xshift=8.2cm]
  \node[font=\footnotesize\sffamily\bfseries,anchor=south] (xht) at (0,0.05)
       {B. Boosting \textnormal{(XGBoost, LightGBM)}};

  \node[proc,text width=2.5cm,anchor=north] (xd) at (0,-0.12) {one training set};

  \foreach \i/\lab/\x in {1/{1st}/-1.85,2/{2nd}/0,3/{3rd}/1.85} {
    \node[proc,text width=1.05cm,minimum height=0.52cm,anchor=north]
         (xt\i) at (\x,-0.95) {\lab\ tree};
    \draw[arr] (xd.south) -- ++(0,-0.10) -| (xt\i.north);
  }

  \node[proc,text width=2.1cm,anchor=north] (xsum) at (0,-1.78) {weighted sum};
  \foreach \i/\x in {1/-1.85,2/0,3/1.85} {
    \draw[arr] (xt\i.south) -- ++(0,-0.10) -| (xsum.north);
  }
  \node[res,text width=1.75cm,anchor=north] (xout) at (0,-2.58) {prediction};
  \draw[arr] (xsum) -- (xout);

  \node[font=\tiny\sffamily,text=black!60,anchor=north,text width=6.0cm,align=center]
       at (0,-3.16) {trees built \emph{one after another}, each fixing prior errors};
  \end{scope}

\end{tikzpicture}}
\caption{The two ensemble strategies. Bagging trains many trees independently and
averages them, reducing variance. Boosting trains trees in sequence, each on the error
left by the previous one, reducing bias.}
\label{fig:algorithms}
\end{figure}
"""


# --------------------------------------------------------------------------- #
# 4. SHAP visual explanation
# --------------------------------------------------------------------------- #
SHAP = r"""
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
  bx/.style={rectangle,rounded corners=2pt,draw=black!50,fill=black!4,
             align=center,font=\scriptsize\sffamily,inner sep=3pt},
  fl/.style={-{Stealth[length=1.8mm]},thick,draw=black!60},
]
  \node[bx,text width=2.7cm,minimum height=0.85cm] (a) at (0,0)
       {\textbf{Model average}\\[1pt]5.6\%};
  \node[bx,text width=4.6cm,minimum height=0.85cm] (b) at (5.0,0)
       {\textbf{Seven contributions}\\[1pt]\tiny years since last $+0.13$
        \quad internet $+0.11$\\[-1pt]\tiny log equids $+0.09$ \quad
        equid share $+0.05$ \quad others $+0.09$};
  \node[bx,text width=2.7cm,minimum height=0.85cm] (c) at (10.4,0)
       {\textbf{This row}\\[1pt]54\%};

  \draw[fl] (a) -- node[font=\tiny\sffamily,above,inner sep=2pt]{$+$} (b);
  \draw[fl] (b) -- node[font=\tiny\sffamily,above,inner sep=2pt]{$=$} (c);

  \node[font=\tiny\sffamily,text=black!60,anchor=north,text width=12.4cm,align=center]
       at (5.2,-0.95)
       {The contributions add up exactly to the gap between the average and this
        prediction, leaving nothing unexplained.};
\end{tikzpicture}
\caption{SHAP attributes one prediction to its inputs. Because the contributions must
sum exactly to the gap, the explanation is arithmetic rather than a plausible story.}
\label{fig:shap}
\end{figure}
"""
