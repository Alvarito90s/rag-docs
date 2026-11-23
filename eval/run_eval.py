"""Evalúa DocuChat con eval/questions.jsonl y escribe eval/results.md."""

import sys

from docuchat.evaluation.run import main

if __name__ == "__main__":
    sys.exit(main())
