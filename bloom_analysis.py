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

# Extract questions and marks from text
def extract_questions_and_marks(text):
    pattern = r"(Q\d+)[\s\S]*?(\(\d+\)|\[\d+\]|\d+)\s*marks?"
    matches = re.findall(pattern, text, re.IGNORECASE)
    questions = [{"Question": q, "Marks": int(m.strip("()[]"))} for q, m in matches]
    return questions

# Analyze text by Bloom's Taxonomy
def analyze_text_by_taxonomy(text, keywords):
    sentences = tokenize_sentences(text)
    taxonomy_analysis = {level: 0 for level in keywords}
    for sentence in sentences:
        for level, level_keywords in keywords.items():
            if any(re.search(rf'\b{word}\b', sentence, re.IGNORECASE) for word in level_keywords):
                taxonomy_analysis[level] += 1
                break
    return taxonomy_analysis, len(sentences)

# Deviation and recommendation
def compare_with_ideal(analysis, total_sentences, ideal_distribution):
    results = {}
    recommendations = []
    for level, count in analysis.items():
        actual_percentage = (count / total_sentences) * 100 if total_sentences > 0 else 0
        deviation = actual_percentage - ideal_distribution[level]
        results[level] = {"Actual %": round(actual_percentage, 2), "Ideal %": ideal_distribution[level], "Deviation %": round(deviation, 2)}
        color = "lightgreen" if 5 <= abs(deviation) <= 8 else "red" if abs(deviation) > 8 else "none"
        recommendations.append({"level": level, "text": f"Consider adjusting content for '{level}'. Deviation: {deviation:.2f}%", "color": color})
    return results, recommendations

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
def generate_csv(results):
    output = StringIO()
    pd.DataFrame(results).T.to_csv(output)
    return output.getvalue()

# UI setup
st.title("Enhanced Bloom's Taxonomy Analysis")
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
        if questions_data:
            st.write("### Questions and Marks Allocation")
            st.table(pd.DataFrame(questions_data))
        else:
            st.write("No questions and marks found in the document.")

        # Perform Bloom's taxonomy analysis
        taxonomy_analysis, total_sentences = analyze_text_by_taxonomy(paper_text, taxonomy_keywords)
        results, recommendations = compare_with_ideal(taxonomy_analysis, total_sentences, ideal_distribution)
        
        # Display personalized greeting
        st.write(f"{faculty_name}, following is the analysis of your paper. You can refer to the recommendations for further enhancements.")

        # Display results in a table
        st.write("### Cognitive Level Analysis")
        results_df = pd.DataFrame(results).T
        results_df.index.name = "Bloom's Level"
        st.table(results_df)

        # Show recommendations with color-coded feedback
        st.write("### Recommendations")
        for recommendation in recommendations:
            if recommendation["color"] == "lightgreen":
                st.markdown(f"<span style='color:green'>✔️ {recommendation['text']}</span>", unsafe_allow_html=True)
            elif recommendation["color"] == "red":
                st.markdown(f"<span style='color:red'>❗ {recommendation['text']}</span>", unsafe_allow_html=True)

        # Plot results as a bar chart
        st.write("### Analysis Chart")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(results_df.index, results_df['Actual %'], label="Actual %", color="skyblue")
        ax.bar(results_df.index, results_df['Ideal %'], width=0.4, alpha=0.7, label="Ideal %", color="orange")
        ax.set_xlabel("Bloom's Taxonomy Level")
        ax.set_ylabel("Percentage")
        ax.legend()
        st.pyplot(fig)

        # Download results as CSV
        csv_data = generate_csv(results)
        st.download_button(label="Download Results as CSV", data=csv_data, file_name="taxonomy_analysis.csv", mime="text/csv")
