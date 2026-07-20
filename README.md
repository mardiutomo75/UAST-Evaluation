# AST/UAST Research Pipeline

This directory contains the reproducible Python pipeline used in the UAST (Unified Abstract Syntax Tree) research experiments. It parses source code with Tree-sitter, constructs original AST and UAST representations, computes intrinsic metrics, and evaluates the representations on downstream tasks.

The experiments compare **original AST** with two UAST forms:

- **Flat UAST**: a canonical, language-independent node representation.
- **Structural UAST**: the canonical representation after structural normalization and compression.

The pipeline is intended for research reproducibility, not production use.

## 1. Experiment overview

| Component | Current setup |
|---|---|
| Database | PostgreSQL database **`codesearchnet`** |
| Parser | Tree-sitter |
| Languages | Go, Python, Ruby, PHP, Java, JavaScript, C#, C++, Rust |
| Intrinsic metrics | PEC-core, PEC-all, CLSA, RESR, TED/similarity, CO-time, CO-memory |
| Downstream tasks | Code retrieval, clone detection, code summarization |
| Baselines | Lexical retrieval, structural retrieval, and CodeBERT raw-code cosine |
| Sensitivity validation | Controlled corruption levels and Spearman correlation |
| Ablation | Stage-wise Tm, Tn, and Tc |

### Dataset roles and CLSA limitation

1. **CodeXGLUE Code2Text** contains Go, Ruby, Java, JavaScript, Python, and PHP functions with docstrings. It is used for code summarization and single-sample measurements. It has no cross-language same-function pairs in this experiment, so CLSA is not computed for this dataset.
2. **CodeXGLUE Code2Code** contains paired Java--C# functions. It is used for CLSA, code retrieval, and downstream comparisons.
3. **HumanEval-X** contains equivalent functions across C++, Java, JavaScript, Python, Rust, and Go in the local experiment data. It is used for CLSA, retrieval, and downstream validation.

CLSA is therefore not reported for PHP or Ruby. A dash (`—`) in a result table means that no valid cross-language equivalent-function pair was available.

## 2. Repository layout

```text
dataset_preparation/
├── 01_prepare_db.py                 # Initialize schema and CodeXGLUE data
├── 02_parsing_ast.py                # Parse CodeXGLUE Code2Text
├── 03_code2code_insert.py           # Import Java--C# Code2Code data
├── 04_parsing_ast_c2c.py            # Parse Code2Code AST/UAST
├── 05_humaneval_insert.py            # Import HumanEval-X
├── 06_humaneval_insert_1.py         # Continue HumanEval-X import
├── 07_humaneval_parsing.py          # Parse HumanEval-X AST/UAST
├── 09_recalculate_pec.py             # Recalculate PEC from stored ASTs
├── 10_humaneval_downstream_correlation.py
├── 11_record_experiment_metadata.py # Hardware/runtime metadata
├── 12_build_raw_measurement_audit.py# Audit raw measurements
├── 13_ast_uast_downstream_retrieval.py
├── 14_clone_detection.py             # AST vs UAST clone detection
├── 15_code2code_downstream_retrieval.py
├── 16_structural_retrieval.py        # Structural retrieval
├── 17_code2text_retrieval_summarization.py
├── 18_intrinsic_sensitivity.py        # Controlled corruption + Spearman
├── 19_baseline_comparison.py         # Baseline comparison
├── 20_dataset_artifact_hash.py       # Dataset reproducibility hashes
├── 21_baseline_comparison_full.py    # Full baseline, including CodeBERT
├── 22_stagewise_ablation.py           # Original, Tm, Tm+Tn, Tm+Tn+Tc
├── parserfunc.py                      # Tree-sitter parser and UAST normalizer
├── constant.py                        # Node mapping, keywords, PEC groups
├── create_table.sql                   # Tables, views, indexes, and functions
├── eval_bleu.py                       # BLEU/METEOR/ROUGE evaluation helper
├── prepare_ast_dataset.py             # Optional AST/UAST export
├── app.py                             # FastAPI inspection service
└── README.md
```

`08_parseheval.py` is obsolete and is not part of the current pipeline. Notebooks, manuscripts, PDFs, local databases, caches, and experiment outputs are not required to execute the Python scripts and are excluded by `.gitignore`.

## 3. Required directory and file layout

The scripts use paths relative to the parent directory of this folder. Create the dataset directory beside `dataset_preparation`:

```text
/home/user/
├── dataset_preparation/
└── disertasi_datasets/
    ├── codexglue/
    │   ├── go/{train,valid,test}.jsonldisertasi_
    │   ├── java/{train,valid,test}.jsonl
    │   ├── javascript/{train,valid,test}.jsonl
    │   ├── php/{train,valid,test}.jsonl
    │   ├── python/{train,valid,test}.jsonl
    │   └── ruby/{train,valid,test}.jsonl
    ├── code2code/
    │   ├── train.java-cs.txt.java
    │   ├── train.java-cs.txt.cs
    │   ├── valid.java-cs.txt.java
    │   ├── valid.java-cs.txt.cs
    │   ├── test.java-cs.txt.java
    │   └── test.java-cs.txt.cs
    └── humaneval-x/
        ├── python/humaneval_python.jsonl
        ├── java/humaneval_java.jsonl
        ├── cpp/humaneval_cpp.jsonl
        ├── javascript/humaneval_javascript.jsonl
        ├── rust/humaneval_rust.jsonl
        └── go/humaneval_go.jsonl
```

The import scripts do not discover arbitrary filenames. Rename or copy files to the names above before running the import stage.

## 4. Download and install the datasets

### 4.1 Create the dataset directory

```bash
cd /home/user
mkdir -p disertasi_datasets/{codexglue,code2code,humaneval-x}
```

Official sources:

- [Microsoft CodeXGLUE repository](https://github.com/microsoft/CodeXGLUE)
- [CodeXGLUE Code2Text instructions](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Text/code-to-text)
- [CodeXGLUE Code2Code instructions](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/code-to-code-trans)
- [HumanEval-X dataset](https://huggingface.co/datasets/zai-org/humaneval-x)
- [Original CodeGeeX repository](https://github.com/THUDM/CodeGeeX)

Follow the official license and dataset terms when downloading or redistributing the data.

### 4.2 CodeXGLUE Code2Text / CodeSearchNet

The CodeXGLUE Code2Text release provides one directory per language and `train.jsonl`, `valid.jsonl`, and `test.jsonl` after preprocessing. The following commands download the language archives referenced by the official CodeXGLUE instructions:

```bash
cd /home/user
mkdir -p /tmp/codexglue-code2text
cd /tmp/codexglue-code2text

for lang in go java javascript php python ruby; do
  wget -c "https://zenodo.org/record/7857872/files/${lang}.zip"
done

mkdir -p /home/user/disertasi_datasets/codexglue
for lang in go java javascript php python ruby; do
  mkdir -p "/home/user/disertasi_datasets/codexglue/${lang}"
  unzip -o "${lang}.zip" -d "/home/user/disertasi_datasets/codexglue/${lang}"
done
```

If an archive contains an extra nested directory, move the three JSONL files into the required language directory:

```bash
for lang in go java javascript php python ruby; do
  find "/home/user/disertasi_datasets/codexglue/${lang}" \
    -type f \( -name train.jsonl -o -name valid.jsonl -o -name test.jsonl \) \
    -exec cp -f {} "/home/user/disertasi_datasets/codexglue/${lang}/" \;
done
```

Verify the layout:

```bash
for lang in go java javascript php python ruby; do
  test -s "/home/user/disertasi_datasets/codexglue/${lang}/train.jsonl" || exit 1
  test -s "/home/user/disertasi_datasets/codexglue/${lang}/valid.jsonl" || exit 1
  test -s "/home/user/disertasi_datasets/codexglue/${lang}/test.jsonl" || exit 1
done
```

### 4.3 CodeXGLUE Code2Code Java--C#

Clone the official CodeXGLUE repository and copy the six files from its `Code-Code/code-to-code-trans/data` directory:

```bash
cd /tmp
git clone --depth 1 https://github.com/microsoft/CodeXGLUE.git codexglue
mkdir -p /home/user/disertasi_datasets/code2code
cp codexglue/Code-Code/code-to-code-trans/data/*java-cs.txt.* \
   /home/user/disertasi_datasets/code2code/
```

Expected filenames:

```text
train.java-cs.txt.java    train.java-cs.txt.cs
valid.java-cs.txt.java    valid.java-cs.txt.cs
test.java-cs.txt.java     test.java-cs.txt.cs
```

Check that each Java file and its C# counterpart have the same number of lines:

```bash
cd /home/user/disertasi_datasets/code2code
for split in train valid test; do
  wc -l "${split}.java-cs.txt.java" "${split}.java-cs.txt.cs"
done
```

### 4.4 HumanEval-X

The original HumanEval-X distribution stores compressed JSONL files under language-specific directories. Download it using Git LFS:

```bash
cd /tmp
git lfs install
git clone https://github.com/THUDM/CodeGeeX.git codegeex
mkdir -p /home/user/disertasi_datasets/humaneval-x
```

Copy and decompress the language files expected by this pipeline:

```bash
for lang in python java cpp javascript go; do
  mkdir -p "/home/user/disertasi_datasets/humaneval-x/${lang}"
  gunzip -c "/tmp/codegeex/codegeex/benchmark/humaneval-x/${lang}/data/humaneval_${lang}.jsonl.gz" \
    > "/home/user/disertasi_datasets/humaneval-x/${lang}/humaneval_${lang}.jsonl
done
```

The local experiment also uses Rust. If a Rust HumanEval-X JSONL file is available in the selected release, place it at:

```text
/home/user/disertasi_datasets/humaneval-x/rust/humaneval_rust.jsonl
```

Otherwise, remove `rust` from the language list in the HumanEval scripts before running them. Do not create an empty placeholder file: an empty file produces an apparently successful but incomplete experiment.

An alternative is to download the dataset from the [Hugging Face HumanEval-X repository](https://huggingface.co/datasets/zai-org/humaneval-x), convert each language split to JSONL, and use the filenames above.

Verify all available files:

```bash
find /home/user/disertasi_datasets/humaneval-x \
  -type f -name 'humaneval_*.jsonl' -size +0c -print
```

### 4.5 Dataset verification before import

Run these checks from `dataset_preparation`:

```bash
cd /home/user/dataset_preparation
python - <<'PY'
from pathlib import Path

root = Path('../disertasi_datasets')
required = [
    root/'codexglue'/'python'/'train.jsonl',
    root/'codexglue'/'java'/'valid.jsonl',
    root/'code2code'/'train.java-cs.txt.java',
    root/'code2code'/'train.java-cs.txt.cs',
    root/'humaneval-x'/'python'/'humaneval_python.jsonl',
]
missing = [str(p) for p in required if not p.is_file() or p.stat().st_size == 0]
if missing:
    raise SystemExit('Missing or empty dataset files:\n' + '\n'.join(missing))
print('Minimum dataset layout: OK')
PY
```

## 5. Install the Python environment

```bash
cd /home/user/dataset_preparation
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install \
  psycopg2-binary tqdm tree-sitter \
  tree-sitter-python tree-sitter-php tree-sitter-java \
  tree-sitter-javascript tree-sitter-go tree-sitter-ruby \
  tree-sitter-c-sharp tree-sitter-cpp tree-sitter-rust \
  nltk scikit-learn rouge-score torch transformers \
  fastapi pydantic uvicorn
```

The `torch` and `transformers` packages are required only for the CodeBERT baseline. The main retrieval, clone detection, summarization, and ablation experiments use the non-deep-learning implementations in this directory.

If the evaluation helper needs NLTK resources:

```bash
python -m nltk.downloader punkt wordnet
```

## 6. Configure PostgreSQL

The scripts use the following local configuration by default:

```text
Host:     localhost
Port:     5432
Database: codesearchnet
User:     postgres
Password: postgres
```

Create the database only if it does not already exist:

```bash
pg_isready -h localhost -p 5432
createdb -U postgres codesearchnet
```

Initialize the schema once. `create_table.sql` contains `DROP TABLE` and `DROP VIEW` operations, so back up the database before using it:

```bash
cd /home/user/dataset_preparation
psql -U postgres -d codesearchnet -f create_table.sql
```

## 7. Execution order

### 7.1 Import and parse the datasets

```bash
cd /home/user/dataset_preparation
source .venv/bin/activate

python 01_prepare_db.py
python 02_parsing_ast.py
python 03_code2code_insert.py
python 04_parsing_ast_c2c.py
python 05_humaneval_insert.py
python 06_humaneval_insert_1.py
python 07_humaneval_parsing.py
```

If only the PEC mapping has changed, recalculate PEC from stored AST/UAST data without reparsing source code:

```bash
python 09_recalculate_pec.py
```

### 7.2 Record metadata and audit measurements

```bash
python 11_record_experiment_metadata.py
python 12_build_raw_measurement_audit.py
python 20_dataset_artifact_hash.py
```

Metadata records the hardware, runtime, and experiment configuration. The raw measurement audit should be checked before copying values into paper tables. CO-time and CO-memory describe the feasibility of the complete pipeline; they are not automatically stage-wise ablation measurements.

### 7.3 Run downstream tasks

```bash
python 13_ast_uast_downstream_retrieval.py
python 14_clone_detection.py
python 15_code2code_downstream_retrieval.py
python 16_structural_retrieval.py
python 17_code2text_retrieval_summarization.py
```

The summarization script supports limits and language filters:

```bash
python 17_code2text_retrieval_summarization.py \
  --train-limit 5000 --test-limit 500 --k 1
```

The reported summarization metric is METEOR, with BLEU/ROUGE available when enabled by the evaluation configuration. Raw source code is not included in the AST/UAST downstream representation tables; it is read only during parsing or by a baseline that explicitly requires raw code.

### 7.4 Run intrinsic validation and baselines

```bash
python 10_humaneval_downstream_correlation.py
python 18_intrinsic_sensitivity.py
python 19_baseline_comparison.py
python 21_baseline_comparison_full.py
```

`18_intrinsic_sensitivity.py` applies deterministic, controlled corruption levels rather than uncontrolled random corruption. Spearman correlation is used to test whether poorer representations produce poorer downstream results. The CodeBERT raw-code cosine baseline is reported separately from lexical and structural retrieval baselines.

### 7.5 Run stage-wise UAST ablation

```bash
python 22_stagewise_ablation.py
```

The cumulative variants are:

| Variant | Components |
|---|---|
| Original AST | No UAST transformation |
| Tm | Node-type mapping/canonicalization |
| Tm+Tn | Tm + attribute/text normalization |
| Tm+Tn+Tc | Tm + Tn + structural compression |

The script computes PEC-core, PEC-all, CLSA, RESR, and average node count for the relevant datasets and writes the results to `stagewise_ablation_results`. CLSA is computed only where equivalent cross-language pairs exist.

## 8. Main metrics and result tables

| Metric/table | Purpose |
|---|---|
| PEC-core / PEC-all | Programming-element completeness |
| CLSA | Normalized tree-edit-based cross-language similarity |
| RESR | Ratio of retained structural information |
| CO-time / CO-memory | Time and memory overhead |
| `downstream_representation_results` | AST/UAST downstream comparison |
| `clone_detection_results` | Clone detection results |
| `code_summarization_results` | Code2Text summarization results |
| `downstream_correlation_results` | Intrinsic/downstream correlation |
| `intrinsic_sensitivity_results` | Response to controlled corruption |
| `baseline_comparison_results` | Lexical, structural, and CodeBERT baselines |
| `stagewise_ablation_results` | Tm/Tn/Tc ablation results |
| `raw_measurement_audit` | Measurements before aggregation |
| `experiment_run_metadata` | Hardware, runtime, and run configuration |

Useful PostgreSQL queries:

```sql
SELECT * FROM pec_result;
SELECT * FROM stagewise_ablation_results;
SELECT * FROM clone_detection_results;
SELECT * FROM code_summarization_results;
SELECT * FROM baseline_comparison_results;
```

## 9. FastAPI inspection service

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

| Endpoint | Method | Function |
|---|---|---|
| `/extract_ast` | POST | Extract original AST |
| `/extract_unified_ast` | POST | Extract canonical UAST |
| `/extract_both` | POST | Extract AST and UAST together |

Example request body:

```json
{
  "code": "def hello(): print('world')",
  "language": "python"
}
```

## 10. Reproducibility and safety notes

- Always use the database **`codesearchnet`**, not `codesearchnet_v3`.
- Run the schema before importing or parsing data.
- Do not run `create_table.sql` against a production database.
- Record experiment metadata before collecting the main measurements.
- Do not add sampling limits when reproducing the full-data ablation.
- Check `raw_measurement_audit` before reporting aggregate values.
- State explicitly whether a result uses flat UAST or structural UAST.
- Preserve the dataset version and run `20_dataset_artifact_hash.py` after downloading or modifying the local dataset.
- Respect the license and terms of each external dataset.

## 11. References

- [CodeXGLUE](https://github.com/microsoft/CodeXGLUE), Microsoft.
- [HumanEval-X / CodeGeeX](https://github.com/THUDM/CodeGeeX).
- Utomo, M. S., Utami, E., Kusrini, K., and Setyanto, A., “Enhancing CodeXGLUE Dataset with Unified Abstract Syntax Tree (AST) Representation for Cross-Language Code Analysis,” *Jurnal Teknologi Informasi dan Ilmu Komputer*, vol. 12, no. 5, pp. 1037–1046, Nov. 2025, doi: [10.25126/jtiik.2025125](https://doi.org/10.25126/jtiik.2025125).
- M. S. Utomo, E. Utami, and A. Setyanto, “[Evaluating Cross-Language Structural Generalization of the Unified Abstract Syntax Tree](https://ejournal.pnc.ac.id/index.php/jinita/article/view/3191),” *J. Innov. Inf. Technol. Appl.*, vol. 8, no. 1, pp. 225–235, Jun. 2026. doi: [10.35970/jinita.v8i1.3191](https://doi.org/10.35970/jinita.v8i1.3191).
