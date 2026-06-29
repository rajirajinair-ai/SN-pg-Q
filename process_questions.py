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

    for line in lines:
        line = line.strip()
        if not line: continue

        year_match = re.search(r'(20\d\d)', line)
        if year_match:
            current_year = year_match.group(1)

        paper_match = re.search(r'Paper\s*[-]*\s*([I1V234]+)', line, re.IGNORECASE)
        if paper_match:
            current_paper = paper_match.group(1).upper()
            if current_paper == 'I' or current_paper == '1': current_paper = '1'
            if current_paper == 'II' or current_paper == '2': current_paper = '2'
            if current_paper == 'III' or current_paper == '3': current_paper = '3'
            if current_paper == 'IV' or current_paper == '4': current_paper = '4'

        q_text = line
        match = re.match(r'^(?:Q\s*\d+|\d+)\s*[\.\)]\s*(.*)', q_text, re.IGNORECASE)
        if match:
            q_text = match.group(1)
        else:
            match = re.match(r'^[-•*]\s*(.*)', q_text)
            if match:
                q_text = match.group(1)

        marks = ""
        mark_match = re.search(r'[\(\[]\s*(\d+(?:\+\d+)*)\s*(?:Marks|M)?\s*[\)\]]', q_text, re.IGNORECASE)
        if mark_match:
            marks = mark_match.group(1)
            q_text = q_text[:mark_match.start()].strip() + " " + q_text[mark_match.end():].strip()

        q_text = q_text.strip()

        if len(q_text) > 15 and not re.match(r'^Attempt all questions', q_text, re.IGNORECASE) and not re.match(r'^Answer questions', q_text, re.IGNORECASE) and not re.match(r'^Draw diagrams', q_text, re.IGNORECASE) and not re.search(r'^Long Answer Question', q_text, re.IGNORECASE) and not re.search(r'^Short Answer Question', q_text, re.IGNORECASE):
            if re.search(r'[a-zA-Z]', q_text):
                questions.append({
                    "original_wording": line,
                    "question": q_text,
                    "year": current_year,
                    "paper": current_paper,
                    "marks": marks
                })

    return questions

def assign_topic(text):
    text_lower = text.lower()

    topics = {
        "COVID": ["covid", "coronavirus"],
        "Airway": ["airway", "intubation", "laryngospasm", "vocal cord", "trachea"],
        "Respiratory System": ["ards", "copd", "pulmonary", "ventilation", "hypoxia", "lung", "thoracotomy", "asthma", "bronchus", "respiratory", "flail chest", "pneumothorax"],
        "Cardiovascular System": ["cardiac", "heart", "mitral", "hypertension", "cpr", "arrhythmia", "pacemaker", "ischemic", "coronary", "hypotension", "shock"],
        "CNS & Neuroanaesthesia": ["intracranial", "icp", "craniotomy", "neuro", "brain", "spinal", "csf", "head", "mri", "hydrocephalus"],
        "Renal": ["renal", "kidney", "turp", "hyponatremia"],
        "Hepatic": ["hepatic", "liver", "jaundice"],
        "Obstetric Anaesthesia": ["pregnancy", "lscs", "labour", "obstetric", "preeclampsia", "eclampsia", "hellp", "amniotic", "ectopic"],
        "Paediatric Anaesthesia": ["paediatric", "pediatric", "child", "neonate", "newborn", "infant", "tof", "cleft"],
        "Trauma": ["trauma", "burns", "injury"],
        "Monitoring": ["monitoring", "oximetry", "capnometry", "bis", "nmj", "neuromuscular monitoring"],
        "Anaesthesia Machine": ["machine", "circuit", "vaporizer", "mapleson"],
        "Regional Anaesthesia": ["epidural", "spinal", "block", "neuraxial", "caudal", "tap", "regional", "plexus", "bupivacaine", "local anaesthetic", "last"],
        "Pharmacology": ["propofol", "isoflurane", "dexmedetomidine", "sugammadex", "rocuronium", "remifentanil", "muscle relaxant", "mac", "pharmacology", "clonidine", "esmolol"],
        "Pain": ["pain", "analgesia", "chronic pain"],
        "Blood & Transfusion": ["blood", "transfusion", "coagulopathy", "haemostasis", "bleeding", "massive transfusion", "dic"],
        "Ethics & Consent": ["consent", "ethics", "record keeping", "awareness"],
        "Equipment": ["equipment", "supraglottic", "laryngoscope", "oxygen therapy"],
        "Critical Care": ["icu", "sepsis", "ards", "mechanical ventilation", "weaning", "critical", "shock"],
        "ICU": ["icu", "intensive care"] # Keep if they match
    }

    for topic, keywords in topics.items():
        for kw in keywords:
            if kw in text_lower:
                return topic

    return "Miscellaneous"

def process():
    questions = extract_questions('all_questions.txt')

    clean_texts = [re.sub(r'[^a-zA-Z0-9\s]', '', q['question'].lower()) for q in questions]
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(clean_texts)
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

    merged_questions = []
    visited = set()

    for i in range(len(questions)):
        if i in visited:
            continue

        similar_indices = np.where(cosine_sim[i] > 0.65)[0]

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

        main_wording = sorted(all_wordings, key=len, reverse=True)[0]

        merged_questions.append({
            "question": main_wording,
            "all_wordings": list(set(all_wordings)),
            "years": sorted(list(years)),
            "papers": sorted(list(papers)),
            "marks": sorted(list(marks)),
            "frequency": len(group),
            "topic": assign_topic(main_wording)
        })

    with open('processed_data.json', 'w') as f:
        json.dump(merged_questions, f, indent=2)

if __name__ == "__main__":
    process()

def generate_predictions(questions):
    # Sort by frequency
    sorted_q = sorted(questions, key=lambda x: x['frequency'], reverse=True)

    # We want a mix of high-yield questions across topics
    predictions = []
    topics_covered = set()

    for q in sorted_q:
        if len(predictions) < 20: # Predict 20 questions
            if q['topic'] not in topics_covered or len(predictions) > 10:
                predictions.append(q)
                topics_covered.add(q['topic'])

    return predictions

if __name__ == "__main__":
    with open('processed_data.json', 'r') as f:
        data = json.load(f)
    preds = generate_predictions(data)
    with open('predictions.json', 'w') as f:
        json.dump(preds, f, indent=2)


def export_data(questions, predictions):
    # Excel
    df_data = []
    for q in questions:
        df_data.append({
            "Topic": q['topic'],
            "Question": q['question'],
            "Frequency": q['frequency'],
            "Years": ", ".join(q['years']),
            "Papers": ", ".join(q['papers']),
            "Marks": ", ".join(q['marks']),
            "All Wordings": " | ".join(q['all_wordings'])
        })
    df = pd.DataFrame(df_data)
    df = df.sort_values(by=['Topic', 'Frequency'], ascending=[True, False])
    df.to_excel('Master_Question_Bank.xlsx', index=False)

    # Markdown
    with open('Master_Question_Bank.md', 'w') as f:
        f.write("# Master Question Bank\n\n")

        f.write("## Frequency Analysis\n")
        freq_counts = { "Asked once": 0, "Asked twice": 0, "Asked 3+ times": 0 }
        for q in questions:
            if q['frequency'] == 1: freq_counts["Asked once"] += 1
            elif q['frequency'] == 2: freq_counts["Asked twice"] += 1
            else: freq_counts["Asked 3+ times"] += 1

        f.write(f"- Asked once: {freq_counts['Asked once']}\n")
        f.write(f"- Asked twice: {freq_counts['Asked twice']}\n")
        f.write(f"- Asked 3+ times: {freq_counts['Asked 3+ times']}\n\n")

        f.write("## Predicted Questions for Next Exam\n")
        for i, p in enumerate(predictions):
            f.write(f"{i+1}. **{p['topic']}**: {p['question']} (Asked {p['frequency']} times)\n")
        f.write("\n")

        f.write("## Topic-wise Organization\n\n")

        topics = df['Topic'].unique()
        for t in topics:
            f.write(f"### {t}\n")
            topic_qs = df[df['Topic'] == t]
            for _, row in topic_qs.iterrows():
                f.write(f"- **{row['Question']}**\n")
                f.write(f"  - *Frequency*: {row['Frequency']}\n")
                f.write(f"  - *Years*: {row['Years'] if row['Years'] else 'N/A'}\n")
                f.write(f"  - *Papers*: {row['Papers'] if row['Papers'] else 'N/A'}\n")
                f.write(f"  - *Marks*: {row['Marks'] if row['Marks'] else 'N/A'}\n")
                f.write(f"  - *Variations*:\n")
                for w in row['All Wordings'].split(' | '):
                    f.write(f"    - {w}\n")
            f.write("\n")

    # PDF
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Master Question Bank", ln=True, align='C')
    pdf.ln(10)

    # We will just write a summary to PDF because of length issues.
    pdf.cell(200, 10, txt="Predicted Questions for Next Exam:", ln=True)
    for i, p in enumerate(predictions):
        pdf.multi_cell(0, 10, txt=f"{i+1}. [{p['topic']}] {p['question']} (Freq: {p['frequency']})")

    pdf.output("Master_Question_Bank.pdf")

if __name__ == "__main__":
    with open('processed_data.json', 'r') as f:
        data = json.load(f)
    with open('predictions.json', 'r') as f:
        preds = json.load(f)

    export_data(data, preds)
