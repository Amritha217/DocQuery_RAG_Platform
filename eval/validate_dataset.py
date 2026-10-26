# Purpose - checks if the golden_dataset.json is correctly structured

import json
from pathlib import Path

DATASET_PATH = (
    Path(__file__).parent
    / "data"
    / "golden_dataset.json"
)


def validate_dataset():

    # Load the golden_dataset.json file

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        dataset = json.load(file)

    # Check that the golden_dataset is a non-empty list
    # This checks two things - if it is a list and if it is non-empty

    if not isinstance(dataset, list) or not dataset:
        raise ValueError("Dataset must be a non-empty JSON list.")

    # Reguired fields that every test case must have.
    # later using this we check if every test case contains all fields

    required_fields = {
        "id",
        "question",
        "reference_answer",
        "relevant_passages",
        "answerable",
    }

    # Used to track if 2 or any test cases have the same id

    seen_ids = set()

    # Validator begins checking each test-case entry from here
    # From here on we itterates over each test case

    for index, item in enumerate(dataset):
        location = f"Dataset item {index + 1}"

        # Finds if any required fields are missing and prints which field is missing for a particular test case

        missing = required_fields - item.keys()
        if missing:
            raise ValueError(
                f"{location} is missing fields: {sorted(missing)}"
            )

        
        # Validate the ID
        # This checks if every id is a string and if there is any spaces within a the string ID removes it also.

        if not isinstance(item["id"], str) or not item["id"].strip():
            raise ValueError(f"{location}: id must be a non-empty string.")

        # Reject duplicate IDs
        # If any ID repeats raise error

        if item["id"] in seen_ids:
            raise ValueError(f"Duplicate ID: {item['id']}")

        seen_ids.add(item["id"])


        # Validate the question
        # The question must be a string, and it must contain something other than whitespace.

        if not isinstance(item["question"], str) or not item["question"].strip():
            raise ValueError(f"{location}: question must not be empty.")

        # Validate the answerable field
        # Ensures the field answerable is boolean else raise error

        if not isinstance(item["answerable"], bool):
            raise ValueError(f"{location}: answerable must be true or false.")


        # Validate the relevant passages
        # First we assign the list of relevant_passages to a local variable, then check if it is a list , if it is string , and non-empty. if anything fails reject.

        passages = item["relevant_passages"]

        if not isinstance(passages, list):
            raise ValueError(f"{location}: relevant_passages must be a list.")

        if any(not isinstance(p, str) or not p.strip() for p in passages):
            raise ValueError(f"{location}: passages must be non-empty strings.")

        # Enforce the rules for answerable questions

        # First we retrieve the expected answer for each query , then checks if the question is answerable.
        # If answerable a refernece answer must exist, and there should be at least one relevant passage.

        # For unanswerable questions, reference_answer must be null and relevant_passages must be an empty list,
        
        answer = item["reference_answer"]

        if item["answerable"]:
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError(
                    f"{location}: answerable cases need a reference answer."
                )
            if not passages:
                raise ValueError(
                    f"{location}: answerable cases need relevant passages."
                )
        else:
            if answer is not None:
                raise ValueError(
                    f"{location}: unanswerable cases must use null answer."
                )
            if passages:
                raise ValueError(
                    f"{location}: unanswerable cases must use an empty list."
                )

    print(f"Dataset validation passed: {len(dataset)} test cases.")


if __name__ == "__main__":
    validate_dataset()
