import argparse
from nltk.translate.bleu_score import corpus_bleu, SmoothingFunction
from nltk.translate.meteor_score import single_meteor_score
from rouge_score import rouge_scorer
import nltk
import csv
import os
# nltk.download('wordnet')



def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def evaluate_bleu(reference_file, generated_file):
    references = []
    hypotheses = []

    with open(reference_file, "r", encoding="utf-8") as ref_f, \
         open(generated_file, "r", encoding="utf-8") as gen_f:
        for ref_line, gen_line in zip(ref_f, gen_f):
    #     ref_lines = list(ref_f)[:1000]
    #     gen_lines = list(gen_f)[:1000]
    #     for ref_line, gen_line in zip(ref_lines, gen_lines):
            ref = ref_line.strip()
            hyp = gen_line.strip()
            if not ref or not hyp:
                continue
            references.append([ref.split()])  # reference harus list of list
            hypotheses.append(hyp.split())    # hypothesis adalah list

    smoothie = SmoothingFunction().method4
    # Gunakan BLEU-4 saja (4-gram), dengan smoothing
    score = corpus_bleu(
        references, 
        hypotheses, 
        weights=(0.25, 0.25, 0.25, 0.25), 
        smoothing_function=smoothie
    )
    return score * 100

def evaluate_meteor(reference_file, generated_file):
    meteor_scores = []
    with open(reference_file, "r", encoding="utf-8") as ref_f, \
         open(generated_file, "r", encoding="utf-8") as gen_f:
        for ref_line, gen_line in zip(ref_f, gen_f):
            ref = ref_line.strip()
            hyp = gen_line.strip()
            if not ref or not hyp:
                continue
            score = single_meteor_score(ref.split(), hyp.split())
            meteor_scores.append(score)
    return sum(meteor_scores) / len(meteor_scores) * 100


def evaluate_rouge(reference_file, generated_file):
    rouge = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
    rouge1_scores = []
    rougeL_scores = []
    with open(reference_file, "r", encoding="utf-8") as ref_f, \
         open(generated_file, "r", encoding="utf-8") as gen_f:
        for ref_line, gen_line in zip(ref_f, gen_f):
            ref = ref_line.strip()
            hyp = gen_line.strip()
            if not ref or not hyp:
                continue
            scores = rouge.score(ref, hyp)
            rouge1_scores.append(scores["rouge1"].fmeasure)
            rougeL_scores.append(scores["rougeL"].fmeasure)
    avg_rouge1 = sum(rouge1_scores) / len(rouge1_scores) * 100
    avg_rougeL = sum(rougeL_scores) / len(rougeL_scores) * 100
    return avg_rouge1, avg_rougeL

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", type=str, required=True, help="e.g., python, java, php, etc.")
    parser.add_argument("--id", type=str, default="ast-unified")
    # parser.add_argument("--type", type=str, default="ast-unified", choices=["ast-unified", "code.original"], help="Tipe input (AST unified atau original code)")
    args = parser.parse_args()

    base_path = f"../../disertasi_datasets/codexglue/{args.lang}"
    reference_file = f"{base_path}/test.docstring"
    generated_file = f"{base_path}/test.generated.{args.id}"

    bleu_score = evaluate_bleu(reference_file, generated_file)
    meteor_score = evaluate_meteor(reference_file, generated_file)
    rouge1_score, rougeL_score = evaluate_rouge(reference_file, generated_file)
    # File output
    output_file = "hasil.csv"
    # Cek apakah file sudah ada
    file_exists = os.path.isfile(output_file)
    # Header dan data
    header = ["Language", "ID", "BLEU", "METEOR", "ROUGE-1", "ROUGE-L"]
    data = [args.lang, args.id, f"{bleu_score:.2f}", f"{meteor_score:.2f}", f"{rouge1_score:.2f}", f"{rougeL_score:.2f}"]
    # Simpan atau tambahkan ke CSV
    with open(output_file, mode="a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)  # Tulis header kalau file baru
        writer.writerow(data)

    print(f"✅ Hasil evaluasi disimpan ke '{output_file}'")
    # Cek apakah file sudah ada
    file_exists = os.path.isfile(output_file)
    print(f"🚀 BLEU Score for {args.lang} ({args.id}): {bleu_score:.2f}")
    print(f"🌟 METEOR Score for {args.lang} ({args.id}): {meteor_score:.2f}")
    print(f"📕 ROUGE-1 F1 Score for {args.lang} ({args.id}): {rouge1_score:.2f}")
    print(f"📘 ROUGE-L F1 Score for {args.lang} ({args.id}): {rougeL_score:.2f}")


# 🚀 BLEU Score for ruby (ast-unified): 2.56
# 🌟 METEOR Score for ruby (ast-unified): 15.43
# 📕 ROUGE-1 F1 Score for ruby (ast-unified): 27.03
# 📘 ROUGE-L F1 Score for ruby (ast-unified): 22.85

# 🚀 BLEU Score for ruby (ast-original): 2.49
# 🌟 METEOR Score for ruby (ast-original): 15.34
# 📕 ROUGE-1 F1 Score for ruby (ast-original): 26.71
# 📘 ROUGE-L F1 Score for ruby (ast-original): 22.67

# 🚀 BLEU Score for ruby (original): 1.58
# 🌟 METEOR Score for ruby (original): 11.71
# 📕 ROUGE-1 F1 Score for ruby (original): 20.58
# 📘 ROUGE-L F1 Score for ruby (original): 17.55

# 🚀 BLEU Score for javascript (ast-unified): 1.36
# 🌟 METEOR Score for javascript (ast-unified): 14.71
# 📕 ROUGE-1 F1 Score for javascript (ast-unified): 29.79
# 📘 ROUGE-L F1 Score for javascript (ast-unified): 26.34

# 🚀 BLEU Score for javascript (ast-original): 1.25
# 🌟 METEOR Score for javascript (ast-original): 14.65
# 📕 ROUGE-1 F1 Score for javascript (ast-original): 29.73
# 📘 ROUGE-L F1 Score for javascript (ast-original): 26.40