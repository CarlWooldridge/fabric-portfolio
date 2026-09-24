# Data samples

- **`*_sample.csv`**: the first 25 rows of each gold table, read from OneLake on 2026-09-24. `rls_user_state` is left out: it maps test-user UPNs to states.
- **`job_runs.csv`**: the workspace's run history for its 26 runnable items (79 runs): notebooks, pipelines and dataflows, with status and UTC start/end times. IDs are dropped.

**License.** These samples are derived from the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Olist, Kaggle), licensed [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Changes: typed, deduplicated and keyed into a star schema, with synthetic customer, seller and product names added by [`../scripts/generate_synthetic_names.py`](../scripts/generate_synthetic_names.py). They are shared under the same license, for non-commercial use.
