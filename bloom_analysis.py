import re
import streamlit as st
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
import fitz  # PyMuPDF for PDF files
from docx import Document  # for Word files

# Bloom's Taxonomy keywords for cognitive analysis
taxonomy_keywords = {
    "Remember": ["define", "list", "state", "identify", "recall", "recognize", "describe", "name", "locate", "find", "label", "select", "choose", "match", "outline", "restate", "duplicate", "memorize", "highlight", "indicate"],
    "Understand": ["explain", "summarize", "interpret", "classify", "compare", "exemplify", "illustrate", "rephrase", "translate", "estimate", "predict", "infer", "conclude", "generalize", "expand", "discuss", "review", "give an example"],
    "Apply": ["apply", "demonstrate", "use", "implement", "solve", "operate", "execute", "show", "illustrate", "practice", "calculate", "modify", "construct", "produce", "experiment", "make", "change", "complete", "discover"],
    "Analyze": ["differentiate", "organize", "attribute", "examine", "compare", "contrast", "investigate", "categorize", "separate", "distinguish", "analyze", "inspect", "probe", "deconstruct", "correlate", "test", "relate", "study", "trace"],
    "Evaluate": ["judge", "recommend", "criticize", "assess", "justify", "support", "defend", "argue", "evaluate", "appraise", "conclude", "prioritize", "rank", "score", "choose", "weigh", "estimate", "validate", "interpret"],
    "Create": ["design", "construct", "develop", "formulate", "generate", "produce", "invent", "compose", "assemble", "plan", "create", "originate", "initiate", "propose", "write", "prepare", "devise", "build", "model"]
}

# Ideal cognitive distribution
default_ideal_distribution = {"Remember": 10, "Understand": 15, "Apply": 20, "Analyze": 20, "Evaluate": 20, "Create": 15}

# Function to extract text from various file types
def extract_text_from_file(uploaded_file):
    file_type = uploaded_file.type
    
    if file_type == "application/pdf":
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
    
    elif file_type == "text/plain":
        text = StringIO(uploaded_file.getvalue().decode("utf-8")).read()
    
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(uploaded_file)
        text = "\n".join([para.text for para in doc.paragraphs])
    
    else:
        text = ""
    
    return text.strip()

# Function to extract questions, sub-questions, and marks
def extract_questions_and_marks(text):
    # Extended regex pattern to capture numbers with a period (e.g., 1.)
    pattern_main = (
        r"(?i)(?:Question|Q|Que|Qn|Qu|question|Que no|Q no|^[0-9]+[\.\)])[\s)*.:,-]*\d*"  
        r"[\s)*.-]*"
        r".*?(?:\[(\d+)\]|\((\d+)\)|(\d+)\s*marks?)"  
    )
    
    # Pattern for sub-questions (e.g., a), b), etc.)
    pattern_sub = r"(?i)^[\s]*[a-z]\)"  
    
    questions = []
    question_counter = 1
    
    # Split text by lines to handle each question and sub-question separately
    lines = text.split('\n')
    for line in lines:
        line = line.strip()  # Clean up leading/trailing whitespace

        # Match main questions with marks
        match_main = re.search(pattern_main, line)
        if match_main:
            marks = match_main.group(1) or match_main.group(2) or match_main.group(3)
            questions.append({
                "Question Number": f"Q{question_counter}",
                "Marks": int(marks) if marks else None,
                "Question Text": line
            })
            question_counter += 1
        
        # Match sub-questions and treat them as separate questions
        elif re.match(pattern_sub, line):
            questions.append({
                "Question Number": f"Q{question_counter}",
                "Marks": None,
                "Question Text": line
            })
            question_counter += 1
    
    return questions

# Function to analyze cognitive levels
def analyze_cognitive_levels(question_text):
    keyword_counts = {level: 0 for level in taxonomy_keywords}
    for level, keywords in taxonomy_keywords.items():
        for keyword in keywords:
            keyword_counts[level] += len(re.findall(rf'\b{keyword}\b', question_text, re.IGNORECASE))

    dominant_level = max(keyword_counts, key=keyword_counts.get)
    actual_percentage = (keyword_counts[dominant_level] / sum(keyword_counts.values())) * 100 if sum(keyword_counts.values()) > 0 else 0
    deviation = actual_percentage - default_ideal_distribution[dominant_level]
    
    suggested_keywords = ", ".join(taxonomy_keywords[dominant_level][:3])  # Suggest top 3 keywords

    return {
        "Dominant Cognitive Level": dominant_level,
        "Ideal %": default_ideal_distribution[dominant_level],
        "Actual %": round(actual_percentage, 2),
        "Deviation %": round(deviation, 2),
        "Suggested Changes": f"Consider adding '{suggested_keywords}' for better alignment."
    }

# Generate downloadable CSV
def generate_csv(data):
    output = StringIO()
    pd.DataFrame(data).to_csv(output)
    return output.getvalue()

# Streamlit setup
st.title("Analyze your Question Paper According to Bloom's Taxonomy Analysis")
st.write("Author: Dr. Mukesh Mann (IIIT Sonepat) | All Rights Reserved")

# Faculty name input
faculty_name = st.text_input("Enter Faculty Name:")

# File upload
uploaded_file = st.file_uploader("Upload a file (PDF, TXT, DOCX) containing the paper content", type=["pdf", "txt", "docx"])

if uploaded_file and faculty_name:
    paper_text = extract_text_from_file(uploaded_file)
    if st.button("Analyze"):
        # Extract questions and marks
        questions_data = extract_questions_and_marks(paper_text)
        question_results = []

        # Analyze each question for cognitive levels
        for question in questions_data:
            analysis = analyze_cognitive_levels(question["Question Text"])
            question_analysis = {
                "Question Number": question["Question Number"],
                "Marks": question["Marks"],
                "Question Text": question["Question Text"],
                "Dominant Cognitive Level": analysis["Dominant Cognitive Level"],
                "Ideal %": analysis["Ideal %"],
                "Actual %": analysis["Actual %"],
                "Deviation %": analysis["Deviation %"],
                "Suggested Changes": analysis["Suggested Changes"]
            }
            question_results.append(question_analysis)

        # Convert question results to DataFrame
        question_df = pd.DataFrame(question_results)

        # Apply color-coded bars for Deviation %
        def format_status_bar(deviation):
            color = "#DFF2BF" if 5 <= abs(deviation) <= 8 else "#FFBABA"
            return f'<div style="background-color: {color}; width: {abs(deviation) * 2}px; height: 15px;"></div>'

        if "Deviation %" in question_df.columns:
            question_df["Status Bar"] = question_df["Deviation %"].apply(format_status_bar)
            st.write(question_df.to_html(escape=False), unsafe_allow_html=True)
        else:
            st.write("Error: 'Deviation %' column not found.")

        # Overall cognitive level analysis
        cognitive_levels = question_df["Dominant Cognitive Level"].value_counts(normalize=True) * 100
        ideal_levels = pd.Series(default_ideal_distribution)

        # Plot pie charts
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        ax1.pie(cognitive_levels, labels=cognitive_levels.index, autopct='%1.1f%%', startangle=140)
        ax1.set_title("Actual Cognitive Level Distribution")
        ax2.pie(ideal_levels, labels=ideal_levels.index, autopct='%1.1f%%', startangle=140)
        ax2.set_title("Ideal Cognitive Level Distribution")
        st.pyplot(fig)

        # Plot bar chart for comparison
        fig, ax = plt.subplots()
        width = 0.35
        labels = cognitive_levels.index.union(ideal_levels.index)
        actual_values = [cognitive_levels.get(label, 0) for label in labels]
        ideal_values = [ideal_levels.get(label, 0) for label in labels]
        ax.bar(labels, actual_values, width, label='Actual')
        ax.bar(labels, ideal_values, width, bottom=actual_values, label='Ideal')
        ax.set_ylabel('Percentage')
        ax.set_title('Cognitive Level Comparison')
        ax.legend()
        st.pyplot(fig)

        # Downloadable CSV
        csv_data = generate_csv(question_results)
        st.download_button(label="Download Question-wise Results as CSV", data=csv_data, file_name="question_wise_taxonomy_analysis.csv", mime="text/csv")
