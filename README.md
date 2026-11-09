# GlandersWatch

A modular platform for glanders risk prediction, retrieval-augmented explanation and owner alerting.

Built as a B.Tech project at the International Institute of Information Technology, Bhubaneswar.

**Authors:** Pedapatruni Shanmuk Vardhan (B123089), Shaktimayee Mohanty (B123118), Yuvraj Singh (B123153)
**Supervisor:** Dr. Sangita Dhara

---

## What this is

Three independently deployable components around one prediction:

| Component | What it does | Status |
|---|---|---|
| Risk engine | Country-year probability that glanders is documented next year, from 8 selected features | Built and evaluated |
| Explanation layer | Retrieval-augmented answers grounded in official guidance, with citations | Specified |
| Alert service | Threshold, suppression and deduplication rules turning a probability into messages | Specified |

The decomposition is the point as much as the model: each component has a fixed contract, none hardcodes the disease, and each can be replaced without touching the others.

## Results at a glance

| | |
|---|---|
| Modelling rows | 2,880 country-years, 160 countries, 2006-2023 |
| Positives | 169 (5.87%) |
| Features | 8, chosen by SHAP on the training years only |
| Temporal holdout | train 2006-2017, test 2018-2023 (960 rows, 74 positives) |
| Champion | logistic regression, leave-country-out PR-AUC 0.381 |
| Best temporal | random forest, PR-AUC 0.495 |

The two schemes disagree on purpose. Random forest wins the forward split; logistic regression wins when whole countries are held out, which is the deployment case, so it is the champion.

## Dataset

```
data/processed/model_matrix.csv          2,880 x 8   the feature matrix
data/processed/model_matrix_labels.csv   2,880 x 1   the target, kept separate
data/processed/country_year_panel.csv      60 cols   the full assembled panel
data/processed/literature_events.csv        263      raw occurrence events
```

`model_matrix.csv` holds exactly the eight features the models consume and nothing else. The label lives in the sibling file so the feature table stays pure.

The eight features, with units:

| Feature | Unit |
|---|---|
| `pop_total` | persons |
| `years_since_last` | years (99 = no event in window) |
| `temp_mean_anom` | °C from that country's prior-year mean |
| `internet_pct` | % of population |
| `humidity_anom` | % RH from baseline |
| `precip_cv` | ratio, sd / mean |
| `log_livestock` | ln(1 + livestock units) |
| `goats` | head |

## Reproducing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python src/01_fetch_data.py          # download public sources
python src/01c_extract_faostat.py    # unpack the FAOSTAT archive
python src/02_build_panel.py         # assemble the country-year panel
python src/shap_select.py            # rank features on the training years
python src/03_train_evaluate.py      # train, tune and evaluate (~5 min)
python src/05_dataset_analysis.py    # association, redundancy, selection
python src/04_report.py              # result figures
python src/06_analysis_figures.py    # dataset figures

python src/09_make_full_report.py    # the 52-page report
python src/10_make_condensed_report.py
```

Every number in the reports is injected from `reports/*.json`, so the documents cannot drift from the pipeline.

---

## Contributing

Read this before you touch anything. The rules exist so a submitted report cannot be changed by accident.

**`main` is the integration branch.** It holds the pipeline, the data and the reports. Changes land there only by merge, and only the owner merges.

### Workflow

Work on your own branch. Never commit directly to `main`.

```bash
# 1. Clone once
git clone https://github.com/YuvrajSingh-mist/glandersWatch-demo.git
cd glandersWatch-demo
git fetch origin

# 2. Branch from main
git switch -c <your-name>/<what-you-are-changing> origin/main

# 3. Work. Commit to your branch only.
git add <files>
git commit -m "Describe the change"

# 4. Push your branch
git push -u origin <your-name>/<what-you-are-changing>
```

For example `aisha/fix-chapter-4-typo`.

Then stop. Open a pull request if your reviewer asks for one, but do not merge it yourself.

### The rules

1. **Create your own branch.** Never commit on `main`.
2. **Edit only files on your branch.**
3. **Never merge.** Not into `main`, not into anyone else's branch. Merging is the owner's decision.
4. **Never force-push.** Not `--force`, not `-f`. If you made a mistake, correct it with a new commit.
5. **Do not commit regenerated data or PDFs** unless the change is the point. The pipeline rebuilds them.

### Things that will bite you

**Numbers come from `reports/*.json`, not from the text.** Editing a number in a `.tex` or `.py` report source will be overwritten on the next build. Change the pipeline, then rebuild.

**Two things must stay in sync:** `reports/selected_features.json` (which features the models use) and `data/processed/model_matrix.csv` (the exported matrix). `11_export_model_matrix.py` reads the former to write the latter, so run it after any selection change.

**The loader is shared.** `03_train_evaluate.py::load_level1` applies the row filters, and `05_dataset_analysis.py` imports it rather than keeping its own copy. Do not reintroduce a private filter — that is how the analysis and the models previously drifted apart.

**Do not add dates, country codes or region names as features without reading Section 8.5 of the report.** The country code is an identifier, not a predictor: it cannot transfer to an unseen country, and in-sample it memorises reporting capacity.

## Licence

Coursework for the B.Tech programme at IIIT Bhubaneswar. Not for redistribution.
