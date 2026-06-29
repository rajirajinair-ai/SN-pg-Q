import re
import json

def read_text():
    with open('all_questions.txt', 'r', encoding='utf-8') as f:
        text = f.read()
    return text

def parse_questions(text):
    # This is a very complex parsing task. We will extract anything that looks like a question or topic.
    # The output format we want is basically: question text, year, paper, marks, topic.
    lines = text.split('\n')
    questions = []

    current_year = "Unknown"
    current_paper = "Unknown"

    for line in lines:
        line = line.strip()
        if not line: continue

        # Look for paper/year info
        if re.search(r'20[0-2][0-9]', line):
            m = re.search(r'(20[0-2][0-9])', line)
            current_year = m.group(1)
        if re.search(r'Paper\s*\d', line, re.IGNORECASE):
            m = re.search(r'(Paper\s*\d)', line, re.IGNORECASE)
            current_paper = m.group(1).title()

        # Very basic heuristic for a question: Starts with a number or bullet
        if re.match(r'^Q?\d+[\.\)]\s*(.*)', line, re.IGNORECASE):
            q_text = re.sub(r'^Q?\d+[\.\)]\s*', '', line, flags=re.IGNORECASE)
            questions.append({
                "question": q_text,
                "year": current_year,
                "paper": current_paper
            })
        elif re.match(r'^[-•]\s*(.*)', line):
            q_text = re.sub(r'^[-•]\s*', '', line)
            questions.append({
                "question": q_text,
                "year": current_year,
                "paper": current_paper
            })

    return questions

text = read_text()
qs = parse_questions(text)
print(f"Parsed {len(qs)} initial potential questions.")

with open('parsed_questions.json', 'w', encoding='utf-8') as f:
    json.dump(qs, f, indent=2)
