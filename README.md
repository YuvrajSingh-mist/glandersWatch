# GlandersWatch — Final Project Report

This branch (`final-report`) holds the submitted project report and the figures it uses. Nothing else.

## Contents

```
GlandersWatch_Final_v2.pdf      the report, 38 pages
GlandersWatch_Final_v2.tex      LaTeX source for the PDF above
figures/
  fig10a_label_volume.png       annual positives and prevalence
  fig10b_label_concentration.png  positive years per country
  fig10c_label_region.png       prevalence by World Bank region
  fig10_label_anatomy.png       stacked archive of the three panels above
  fig07_alert_budget.png        alert economics
  fig14_background.png          background context chart
  iiit_logo.png                 institute logo on the title page
  fig_architecture.tex          TikZ platform diagram
  fig_rag.tex                   TikZ retrieval pipeline diagram
  alerts_pipeline.tex           TikZ end-to-end alert pipeline
  alerting_modular_arch.tex     TikZ alert modular architecture
  diagstyles.tex                TikZ styles used by the diagrams above
```

`GlandersWatch_Final_v2.tex` is the report source. Rebuild with `tectonic GlandersWatch_Final_v2.tex` from this branch root. The TikZ files under `figures/` are drawings included by that source, not the report itself.

## Before you change anything

Read this section. The rules exist so the submitted PDF cannot be altered by accident.

**`main` is off limits.** It holds the full project: pipeline, data, evaluation code, generator scripts. Any commit to `main` risks moving a number that the report quotes. Do not edit it, do not force-push it, do not open a pull request into it.

**`final-report` is a frozen reference.** It is what was submitted. Treat it as read-only.

### Workflow

Work on your own branch. Never on `main`, never on `final-report`.

```bash
# 1. Clone once, if you have not already
git clone https://github.com/YuvrajSingh-mist/glandersWatch.git
cd glandersWatch
git fetch origin

# 2. Start your own branch from this one
git switch -c <your-name>/<what-you-are-changing> origin/final-report

# 3. Edit files. Commit to your branch only.
git add <files>
git commit -m "Describe the change"

# 4. Push your branch
git push -u origin <your-name>/<what-you-are-changing>
```

For example, `aisha/fix-typo-chapter-4`.

Then stop. Open a pull request from your branch if your reviewer asks for one, but do not merge it yourself.

### The five rules

1. **Create your own branch.** Never commit on `main` or `final-report`.
2. **Edit only files on your branch.** Do not switch to `main` and edit there.
3. **Never merge.** Not into `main`, not into `final-report`, not into anyone else's branch.
4. **Never force-push.** `git push --force` and `git push -f` are not allowed on any shared branch. If you have made a mistake, make a new commit that corrects it.
5. **Only the repository owner merges.** Merging is a single-person decision. If your change is approved, the owner merges it and re-exports the PDF.

### If your change affects the PDF

The PDF is generated, not hand-edited. Change the report's source and rebuild, then let the owner decide when the PDF on this branch is replaced. Do not commit a rebuilt binary over the submitted one on your own.

## Rebuilding the PDF

From the full project on `main`:

```bash
python src/10_make_condensed_report.py
cd report && tectonic GlandersWatch_Final_v2.tex
```

The report is built from `reports/*.json`, so every number in it comes from the pipeline output rather than being typed in. If a figure or a number changes, the pipeline has to be re-run first.

## Licence

Coursework for the B.Tech programme at IIIT Bhubaneswar. Not for redistribution.
