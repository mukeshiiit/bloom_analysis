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
    "Understand": ["explain", "summarize", "interpret", "classify", "compare", "exemplify", "illustrate", "rephrase", "translate", "estimate", "predict", "infer", "conclude", "generalize", "expand", "discuss", "review", "give an example"],
    "Apply": ["apply", "demonstrate", "use", "implement", "solve", "operate", "execute", "show", "illustrate", "practice", "calculate", "modify", "construct", "produce", "experiment", "make", "change", "complete", "discover"],
    "Analyze": ["differentiate", "organize", "attribute", "examine", "compare", "contrast", "investigate", "categorize", "separate", "distinguish", "analyze", "inspect", "probe", "deconstruct", "correlate", "test", "relate", "study", "trace"],
    "Evaluate": ["judge", "recommend", "criticize", "assess", "justify", "support", "defend", "argue", "evaluate", "appraise", "conclude", "prioritize", "rank", "score", "choose", "weigh", "estimate", "validate", "interpret"],
    "Create": ["design", "construct", "develop", "formulate", "generate", "produce", "invent", "compose", "assemble", "plan", "create", "originate", "initiate", "propose", "write", "prepare", "devise", "build", "model"]
}

default_ideal_distribution = {"Remember": 10, "Understand": 15, "Apply": 20, "Analyze": 20, "Evaluate": 20, "Create": 15}

# Improved function to extract questions and marks
def extract_questions_and_marks(text):
    pattern = r"(Q[\s]*[\(\[]?\d+[\)\]]?)[\s\S]*?(\(\d+\)|\[\d+\]|\{\d+\}|\d+)\s*(marks?)?"
    matches = re.findall(pattern, text, re.IGNORECASE)
    questions = []
    for q, m, _ in matches:
        question_number = re.sub(r"[\(\)\[\]{}]", "", q)
        marks = int(re.sub(r"[^\d]", "", m))
        questions.append({"Question": question_number, "Marks": marks})
    return questions

# Function to determine the cognitive level with the most keyword matches for each question
def analyze_dominant_cognitive_level(question_text, keywords, ideal_distribution):
    keyword_counts = {level: 0 for level in keywords}

    # Count occurrences of each keyword for each cognitive level
    for level, level_keywords in keywords.items():
        for keyword in level_keywords:
            keyword_counts[level] += len(re.findall(rf'\b{keyword}\b', question_text, re.IGNORECASE))

    # Determine the dominant cognitive level
    dominant_level = max(keyword_counts, key=keyword_counts.get)
    actual_percentage = (keyword_counts[dominant_level] / sum(keyword_counts.values())) * 100 if sum(keyword_counts.values()) > 0 else 0
    deviation = actual_percentage - ideal_distribution[dominant_level]
    color = "green" if 5 <= abs(deviation) <= 8 else "red" if abs(deviation) > 8 else "none"
    recommendation = f"Consider {'reducing' if deviation > 0 else 'increasing'} focus on '{dominant_level}'." if deviation != 0 else "On target."
    suggested_keywords = ", ".join(keywords[dominant_level][:5])  # Show top 5 keywords for the dominant level

    return {
        "Cognitive Level": dominant_level,
        "Ideal %": ideal_distribution[dominant_level],
        "Actual %": round(actual_percentage, 2),
        "Deviation %": round(deviation, 2),
        "Status": deviation,  # For bar visualization
        "Suggested Keywords": suggested_keywords,
        "Recommendation": recommendation
    }

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

        # Perform Bloom's taxonomy analysis to identify the dominant cognitive level for each question
        for question in questions_data:
            dominant_level_analysis = analyze_dominant_cognitive_level(question["Question"], taxonomy_keywords, ideal_distribution)
            question_results.append({
                "Question": question["Question"],
                "Marks": question["Marks"],
                **dominant_level_analysis
            })

        # Display question-wise results in a table with Status Bars
        st.write("### Question-wise Cognitive Level Analysis")
        question_df = pd.DataFrame(question_results)
        question_df["Status"] = question_df["Deviation %"].apply(lambda x: f'<div style="background-color: {"#DFF2BF" if abs(x) <= 8 else "#FFBABA"}; width: {abs(x) * 2}px; height: 15px;"></div>',)
        st.write(question_df.to_html(escape=False), unsafe_allow_html=True)

        # General analysis for entire document
        general_analysis = analyze_text_by_taxonomy(paper_text, taxonomy_keywords, ideal_distribution)
        st.write("### General Cognitive Level Analysis")
        general_df = pd.DataFrame(general_analysis)
        st.table(general_df)

        # Show pie charts for actual vs ideal distribution
        fig, axs = plt.subplots(1, 2, figsize=(10, 5))
        axs[0].pie([x["Actual %"] for x in general_analysis], labels=[x["Cognitive Level"] for x in general_analysis], autopct='%1.1f%%')
        axs[0].set_title("Actual Cognitive Level Distribution")
        axs[1].pie([ideal_distribution[x] for x in ideal_distribution], labels=ideal_distribution.keys(), autopct='%1.1f%%')
        axs[1].set_title("Ideal Cognitive Level Distribution")
        st.pyplot(fig)

        # Downloadable CSV
        csv_data = generate_csv(question_results)
        st.download_button(label="Download Question-wise Results as CSV", data=csv_data, file_name="question_wise_taxonomy_analysis.csv", mime="text/csv")
        
        csv_data_general = generate_csv(general_analysis)
        st.download_button(label="Download General Analysis Results as CSV", data=csv_data_general, file_name="general_taxonomy_analysis.csv", mime="text/csv")
