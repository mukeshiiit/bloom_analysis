import re
import streamlit as st
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
import fitz  # PyMuPDF for PDF files
from docx import Document  # for Word files

# Expanded keywords for each level of Bloom's Taxonomy
taxonomy_keywords = {
    "Remember": ["define", "list", "state", "identify", "recall", "recognize", "describe", "name", "locate", "find", "label", "select", "choose", "match", "outline", "restate", "duplicate", "memorize", "highlight", "indicate"],
    "Understand": ["explain", "summarize", "interpret", "classify", "compare", "exemplify", "illustrate", "explain", "rephrase", "translate", "estimate", "predict", "infer", "conclude", "generalize", "expand", "define in own words", "discuss", "review", "give an example"],
    "Apply": ["apply", "demonstrate", "use", "implement", "solve", "operate", "execute", "show", "illustrate", "practice", "calculate", "modify", "construct", "produce", "experiment", "make", "change", "complete", "discover", "use in a new way"],
    "Analyze": ["differentiate", "organize", "attribute", "examine", "compare", "contrast", "investigate", "categorize", "separate", "distinguish", "analyze", "inspect", "probe", "deconstruct", "correlate", "test", "relate", "break down", "study", "trace"],
    "Evaluate": ["judge", "recommend", "criticize", "assess", "justify", "support", "defend", "argue", "evaluate", "appraise", "conclude", "prioritize", "rank", "score", "choose", "weigh", "estimate", "validate", "interpret", "reflect"],
    "Create": ["design", "construct", "develop", "formulate", "generate", "produce", "invent", "compose", "assemble", "plan", "create", "originate", "initiate", "propose", "write", "prepare", "devise", "build", "model", "adapt"]
}

default_ideal_distribution = {"Remember": 10, "Understand": 15, "Apply": 20, "Analyze": 20, "Evaluate": 20, "Create": 15}

# Function to tokenize text into sentences
def tokenize_sentences(text):
    return re.split(r'[.!?]', text)

# Improved function to extract questions and marks
def extract_questions_and_marks(text):
    # Improved regex pattern to capture question numbers and marks in various formats
    pattern = r"(Q[\s]*[\(\[]?\d+[\)\]]?)[\s\S]*?(\(\d+\)|\[\d+\]|\{\d+\}|\d+)\s*(marks?)?"
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    # Parsing the matches to remove brackets and convert marks to integers
    questions = []
    for q, m, _ in matches:
        question_number = re.sub(r"[\(\)\[\]{}]", "", q)  # Remove any brackets around question number
        marks = int(re.sub(r"[^\d]", "", m))  # Extract numeric part of marks
        questions.append({"Question": question_number, "Marks": marks})
    
    return questions

# Analyze text by Bloom's Taxonomy for each question
def analyze_question_by_taxonomy(question_text, keywords, ideal_distribution):
    analysis = {level: 0 for level in keywords}
    total_terms = 0

    for level, level_keywords in keywords.items():
        for keyword in level_keywords:
            count = len(re.findall(rf'\b{keyword}\b', question_text, re.IGNORECASE))
            analysis[level] += count
            total_terms += count

    # Calculate percentages and deviations
    results = []
    for level, count in analysis.items():
        actual_percentage = (count / total_terms) * 100 if total_terms > 0 else 0
        deviation = actual_percentage - ideal_distribution[level]
        results.append({
            "Cognitive Level": level,
            "Ideal %": ideal_distribution[level],
            "Actual %": round(actual_percentage, 2),
            "Deviation %": round(deviation, 2)
        })

    return results

# Extract text from uploaded files
def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    elif uploaded_file.type == "text/plain":
        return StringIO(uploaded_file.getvalue().decode("utf-8")).read()
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        return "\n".join([para.text for para in doc.paragraphs])

# Generate downloadable CSV
def generate_csv(data):
    output = StringIO()
    pd.DataFrame(data).to_csv(output)
    return output.getvalue()

# UI setup
st.title("Analyze your Question Paper According to Bloom's Taxonomy Analysis")
st.write("Author: Dr. Mukesh Mann (IIIT Sonepat) | All Rights Reserved")

# Faculty name input
faculty_name = st.text_input("Enter Faculty Name:")

# File upload
uploaded_file = st.file_uploader("Upload a file (PDF, TXT, DOCX) containing the paper content", type=["pdf", "txt", "docx"])

# Ideal Distribution Settings with Sliders
st.subheader("Set Ideal Distribution (%)")
level_descriptions = {
    "Remember": "Recall facts and basic concepts",
    "Understand": "Explain ideas or concepts",
    "Apply": "Use information in new situations",
    "Analyze": "Draw connections among ideas",
    "Evaluate": "Justify a stance or decision",
    "Create": "Produce original work or ideas"
}
ideal_distribution = {}
for level, description in level_descriptions.items():
    ideal_distribution[level] = st.slider(
        f"Ideal % for {level}",
        min_value=0,
        max_value=100,
        value=default_ideal_distribution[level],
        help=f"{description}. Adjust the desired percentage for Bloom's '{level}' level analysis."
    )

if uploaded_file and faculty_name:
    paper_text = extract_text_from_file(uploaded_file)
    if st.button("Analyze"):
        # Extract questions and marks
        questions_data = extract_questions_and_marks(paper_text)
        question_results = []

        # Perform Bloom's taxonomy analysis for each question
        for question in questions_data:
            question_analysis = analyze_question_by_taxonomy(question["Question"], taxonomy_keywords, ideal_distribution)
            for result in question_analysis:
                question_results.append({
                    "Question": question["Question"],
                    "Marks": question["Marks"],
                    "Cognitive Level": result["Cognitive Level"],
                    "Ideal %": result["Ideal %"],
                    "Actual %": result["Actual %"],
                    "Deviation %": result["Deviation %"]
                })

        # Display personalized greeting
        st.write(f"{faculty_name}, following is the analysis of your paper. You can refer to the recommendations for further enhancements.")

        # Display question-wise results in a table
        st.write("### Question-wise Cognitive Level Analysis")
        question_df = pd.DataFrame(question_results)
        st.table(question_df)

        # Generate CSV data for download
        csv_data = generate_csv(question_results)
        st.download_button(label="Download Results as CSV", data=csv_data, file_name="question_wise_taxonomy_analysis.csv", mime="text/csv")
