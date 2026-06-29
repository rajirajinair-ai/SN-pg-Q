import re
import json

def parse_questions(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"Total chars: {len(text)}")
    print(f"First 1000 chars: {text[:1000]}")

parse_questions('all_questions.txt')
