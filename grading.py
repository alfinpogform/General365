import json
import os
import datasets
from tqdm import tqdm
import argparse

from utils import grading_text, grading_math, pred_cut


API_KEY = "xxx"
BASE_URL = "xxx"

def grading(pred_extract, info, grading_model="gpt-4.1-mini"):
    if info['answer_type'] in ["text", "single_choice", "multiple_choice"]:
        return grading_text(pred_extract, info, 
                            grading_model=grading_model, API_KEY=API_KEY, BASE_URL=BASE_URL)
    else:
        result = grading_math(pred_extract, info)
        if result is True:
            return result
        else:
            pred_extract_cut = pred_cut(pred_extract)
            try:
                result_cut = grading_math(pred_extract_cut, info)
            except Exception as e:
                print("Error in grading for cut result.")
                print(e)
                result_cut = False
            return result_cut


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--response_file", type=str, required=True, help="Input file name.")
    parser.add_argument("--grading_model", type=str, default="gpt-4.1-mini", help="Model name for grading.")
    args = parser.parse_args()

    dataset = datasets.load_dataset("meituan-longcat/General365_Public")
    question_id_to_info = {}
    for item in dataset["test"]:
        question_id_to_info[item["id"]] = item
    
    with open(os.path.join("model_responses", args.response_file), "r", encoding="utf-8") as f_read:
        model_responses = [json.loads(line) for line in f_read.readlines()]
    
    question_id2acc = {}
    for model_response in tqdm(model_responses):
        question_id = model_response["question_id"]
        pred = model_response["model_response"]
        gold_info = question_id_to_info[question_id]

        acc = grading(pred, gold_info, grading_model=args.grading_model)
        question_id2acc[question_id] = acc
    
    avg_acc = sum(question_id2acc[qid] for qid in question_id2acc) / len(question_id2acc)
    print(f"Average Accuracy: {avg_acc}")
    grading_result = {
        "average_accuracy": avg_acc,
        "per_question_accuracy": question_id2acc,
    }

    if not os.path.exists("grading_results"):
        os.makedirs("grading_results")

    write_file = os.path.join("grading_results", f"result_{args.response_file}.log")

    with open(write_file, "w", encoding="utf-8") as f_write:
        json.dump(grading_result, f_write, indent=4, ensure_ascii=False)

