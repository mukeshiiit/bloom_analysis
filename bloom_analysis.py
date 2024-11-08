import re
import streamlit as st
import pandas as pd
from io import StringIO
import matplotlib.pyplot as plt
import fitz  # PyMuPDF for PDF files
from docx import Document  # for Word files
from collections import defaultdict

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

# Function to extract questions and marks
def extract_questions_and_marks(text):
    pattern = r"(Q[\s]*[\(\[]?\d+[\)\]]?)[\s\S]*?(\(\d+\)|\[\d+\]|\{\d+\}|\d+)\s*(marks?)?"
    matches = re.findall(pattern, text, re.IGNORECASE)
    questions = []
    for q, m, _ in matches:
        question_number = re.sub(r"[\(\)\[\]{}]", "", q)
        marks = int(re.sub(r"[^\d]", "", m))
        questions.append({"Question": question_number, "Marks": marks})
    return questions

# Enhanced function to determine the cognitive level with priority keyword matching
def analyze_dominant_cognitive_level(question_text, keywords, ideal_distribution):
    # Initialize frequency dictionary to store occurrences of keywords per cognitive level
    level_scores = defaultdict(int)

    # Count occurrences of each keyword for each cognitive level
    for level, level_keywords in keywords.items():
        for keyword in level_keywords:
            occurrences = len(re.findall(rf'\b{keyword}\b', question_text, re.IGNORECASE))
            level_scores[level] += occurrences

    # Debugging print to see the counts for each level
    print(f"Question: {question_text}")
    print(f"Level Scores: {dict(level_scores)}")

    # Determine the level with the highest score
    dominant_level = max(level_scores, key=level_scores.get)
    actual_percentage = (level_scores[dominant_level] / sum(level_scores.values())) * 100 if sum(level_scores.values()) > 0 else 0
    deviation = actual_percentage - ideal_distribution[dominant_level]
    recommendation = f"Consider {'reducing' if deviation > 0 else 'increasing'} focus on '{dominant_level}'." if deviation != 0 else "On target."
    suggested_keywords = ", ".join(keywords[dominant_level][:5])  # Show top 5 keywords for the dominant level

    # Print the chosen level for debugging
    print(f"Chosen Cognitive Level: {dominant_level}\n")

    return {
        "Cognitive Level": dominant_level,
        "Ideal %": ideal_distribution[dominant_level],
        "Actual %": round(actual_percentage, 2),
        "Deviation %": round(deviation, 2),
        "Suggested Keywords": suggested_keywords,
        "Recommendation": recommendation
    }

# Dummy questions to test the function
questions = [
    {"Question": "Q1) what is man [3]"},
    {"Question": "Q2) Apply a topo [5]"},
    {"Question": "Q3) Create meaning (10)"}
]

# Ideal distribution settings for testing
ideal_distribution = default_ideal_distribution

# Test each question using the function and print the output
for question in questions:
    result = analyze_dominant_cognitive_level(question["Question"], taxonomy_keywords, ideal_distribution)
    print(result)
