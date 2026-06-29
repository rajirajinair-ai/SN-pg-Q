import re
import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def extract_questions(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    questions = []
    current_year = "Unknown"
    current_paper = "Unknown"

    # We will try to maintain context
    for line in lines:
        line = line.strip()
        if not line: continue

        # Detect year
        year_match = re.search(r'(20\d\d)', line)
        if year_match:
            current_year = year_match.group(1)

        # Detect paper
        paper_match = re.search(r'Paper\s*[-]*\s*([I1V234]+)', line, re.IGNORECASE)
        if paper_match:
            current_paper = paper_match.group(1).upper()
            if current_paper == 'I' or current_paper == '1': current_paper = '1'
            if current_paper == 'II' or current_paper == '2': current_paper = '2'
            if current_paper == 'III' or current_paper == '3': current_paper = '3'
            if current_paper == 'IV' or current_paper == '4': current_paper = '4'

        # Try to detect a question
        # Can start with number, bullet, Q1, etc.
        # Or just a standalone line that looks like a question (e.g. ends with ? or is long enough)

        q_text = line

        # Remove Q1, 1., 1), etc.
        match = re.match(r'^(?:Q\s*\d+|\d+)\s*[\.\)]\s*(.*)', q_text, re.IGNORECASE)
        if match:
            q_text = match.group(1)
        else:
            # Bullet point
            match = re.match(r'^[-•*]\s*(.*)', q_text)
            if match:
                q_text = match.group(1)

        # Look for marks like (10), (5+5), (10 Marks), [10]
        marks = ""
        mark_match = re.search(r'[\(\[]\s*(\d+(?:\+\d+)*)\s*(?:Marks|M)?\s*[\)\]]', q_text, re.IGNORECASE)
        if mark_match:
            marks = mark_match.group(1)
            q_text = q_text[:mark_match.start()].strip() + " " + q_text[mark_match.end():].strip()

        q_text = q_text.strip()

        # Filter out very short lines or garbage
        if len(q_text) > 15 and not re.match(r'^Attempt all questions', q_text, re.IGNORECASE) and not re.match(r'^Answer questions', q_text, re.IGNORECASE) and not re.match(r'^Draw diagrams', q_text, re.IGNORECASE):
            # Only add if it's a valid question and not just random text
            # Often questions have a verb or are long enough
            if re.search(r'[a-zA-Z]', q_text):
                questions.append({
                    "original_wording": line,
                    "question": q_text,
                    "year": current_year,
                    "paper": current_paper,
                    "marks": marks
                })

    return questions

questions = extract_questions('all_questions.txt')
print(f"Extracted {len(questions)} lines as potential questions.")

# Deduplication
# 1. Clean up texts for comparison
clean_texts = [re.sub(r'[^a-zA-Z0-9\s]', '', q['question'].lower()) for q in questions]

vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(clean_texts)
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

merged_questions = []
visited = set()

for i in range(len(questions)):
    if i in visited:
        continue

    similar_indices = np.where(cosine_sim[i] > 0.65)[0] # Threshold for similarity

    # Merge them
    group = []
    years = set()
    papers = set()
    marks = set()
    all_wordings = []

    for idx in similar_indices:
        if idx not in visited:
            visited.add(idx)
            q = questions[idx]
            group.append(q)
            if q['year'] != "Unknown": years.add(q['year'])
            if q['paper'] != "Unknown": papers.add("Paper " + q['paper'])
            if q['marks']: marks.add(q['marks'])
            all_wordings.append(q['question'])

    # Pick the longest/most descriptive wording as the main one, or just the first
    main_wording = sorted(all_wordings, key=len, reverse=True)[0]

    merged_questions.append({
        "question": main_wording,
        "all_wordings": list(set(all_wordings)),
        "years": sorted(list(years)),
        "papers": sorted(list(papers)),
        "marks": sorted(list(marks)),
        "frequency": len(group)
    })

print(f"Merged into {len(merged_questions)} unique questions.")
with open('merged_questions.json', 'w') as f:
    json.dump(merged_questions, f, indent=2)
