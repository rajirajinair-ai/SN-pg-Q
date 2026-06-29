import json
import pandas as pd
from fpdf import FPDF

def export_data(questions, predictions):
    # Sort questions by frequency
    sorted_q = sorted(questions, key=lambda x: x['frequency'], reverse=True)

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

        f.write("## High-Yield Revision List\n\n")
        f.write("### Top 25\n")
        for i, q in enumerate(sorted_q[:25]):
            f.write(f"{i+1}. **{q['topic']}**: {q['question']} (Freq: {q['frequency']})\n")

        f.write("\n### Top 50\n")
        for i, q in enumerate(sorted_q[:50]):
            f.write(f"{i+1}. **{q['topic']}**: {q['question']} (Freq: {q['frequency']})\n")

        f.write("\n### Top 100\n")
        for i, q in enumerate(sorted_q[:100]):
            f.write(f"{i+1}. **{q['topic']}**: {q['question']} (Freq: {q['frequency']})\n")

        f.write("\n## Topic-wise Organization\n\n")

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
    try:
        # Avoid FPDF unicode errors by replacing non-latin1 characters
        def clean_pdf_text(t):
            return t.encode('latin-1', 'replace').decode('latin-1')

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Master Question Bank", ln=True, align='C')
        pdf.ln(5)

        pdf.set_font("Arial", 'B', size=12)
        pdf.cell(200, 10, txt="Predicted Questions for Next Exam:", ln=True)
        pdf.set_font("Arial", size=10)
        for i, p in enumerate(predictions):
            pdf.multi_cell(0, 8, txt=clean_pdf_text(f"{i+1}. [{p['topic']}] {p['question']} (Freq: {p['frequency']})"))

        pdf.ln(5)
        pdf.set_font("Arial", 'B', size=12)
        pdf.cell(200, 10, txt="Top 25 High-Yield Questions:", ln=True)
        pdf.set_font("Arial", size=10)
        for i, q in enumerate(sorted_q[:25]):
            pdf.multi_cell(0, 8, txt=clean_pdf_text(f"{i+1}. [{q['topic']}] {q['question']} (Freq: {q['frequency']})"))

        # Add full topic-wise bank (simplified to fit without memory/time issues)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', size=14)
        pdf.cell(200, 10, txt="Topic-wise Master Bank:", ln=True)

        for t in df['Topic'].unique():
            pdf.ln(3)
            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(200, 8, txt=clean_pdf_text(t), ln=True)
            pdf.set_font("Arial", size=10)
            topic_qs = df[df['Topic'] == t]
            for _, row in topic_qs.iterrows():
                pdf.multi_cell(0, 6, txt=clean_pdf_text(f"- {row['Question']} (Freq: {row['Frequency']}, Years: {row['Years'] if row['Years'] else 'N/A'})"))

        pdf.output("Master_Question_Bank.pdf")
    except Exception as e:
        print("PDF generation error:", e)

if __name__ == "__main__":
    with open('processed_data.json', 'r') as f:
        data = json.load(f)
    with open('predictions.json', 'r') as f:
        preds = json.load(f)

    export_data(data, preds)
