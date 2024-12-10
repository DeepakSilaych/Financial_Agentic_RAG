# This script is an agent designed to download 10-K financial reports when not directly available.
# It extracts the company name and year from a user prompt, searches for the report online,
# and saves it as a PDF in a designated folder.

# HOW TO USE THIS SCRIPT:
# 1. Prepare a text file `company_list.txt` containing a list of company names, one per line.
# 2. Ensure you have the required Python packages installed:
#    - spacy (for NER-based company extraction)
#    - pdfkit (for converting online reports to PDFs)
#    - requests, bs4 (for web scraping)
# 3. Run the script by providing a prompt containing the company name and year.

# INPUT:
# - A user prompt in natural language, e.g.,
#   "Download the 10-K financial report for Tesla for the year 2023".

# OUTPUT:
# - The script identifies:
#   - The company name (e.g., "Tesla")
#   - The year (e.g., "2023")
# - It downloads the corresponding SEC 10-K report as a PDF.
# - The PDF is saved in the `financial_reports` folder with the filename format:
#   "<CompanyName>_<Year>_10K.pdf", e.g., "Tesla_2023_10K.pdf".

# KEY FEATURES:
# 1. Extracts company names using spaCy's Named Entity Recognition (NER).
# 2. Falls back to a predefined company list (`company_list.txt`) if NER fails.
# 3. Searches Google for the SEC 10-K report link.
# 4. Converts the online report to a PDF and saves it locally.

# ERROR HANDLING:
# - If the company name or year is not extracted, the process terminates with an error message.
# - If no valid SEC link is found during the search, the process terminates.
# - Handles issues with PDF generation or folder creation gracefully.

# NOTE:
# - Ensure the `company_list.txt` file is comprehensive to improve fallback accuracy.
# - Configure the `pdfkit` installation for your operating system to ensure successful PDF conversion.

import os
import requests
from bs4 import BeautifulSoup
import spacy
import pdfkit

from utils import log_message

# Load spaCy's NLP model
nlp = spacy.load("en_core_web_sm")


# Load the list of companies from a file
def load_company_list(file_path="company_list.txt"):
    if not os.path.exists(file_path):
        log_message(f"Company list file not found: {file_path}")
        return []
    with open(file_path, "r") as f:
        companies = [line.strip() for line in f]
    return companies


# Extract company names from file and convert to lowercase for easy comparison
COMPANY_LIST = [company.lower() for company in load_company_list()]


# Function to extract company name and year using NER
def extract_company_and_year(prompt):
    # Normalize the case for spaCy processing
    normalized_prompt = " ".join(
        word.capitalize() if word.isalpha() else word for word in prompt.split()
    )

    # Process the prompt with spaCy
    doc = nlp(normalized_prompt)

    # Extract year (first 4-digit number in the text)
    year = next(
        (word.text for word in doc if word.is_digit and len(word.text) == 4), None
    )

    # Extract company name (first entity labeled as "ORG")
    company_name = None
    for ent in doc.ents:
        if ent.label_ == "ORG":  # "ORG" corresponds to organization names
            company_name = ent.text
            break

    # Fallback: Use COMPANY_LIST if NER fails
    if not company_name:
        log_message(
            "NER failed to detect the company name. Checking against the company list..."
        )
        # Convert prompt to lowercase for comparison
        lowercase_prompt = prompt.lower()
        for company in COMPANY_LIST:
            # Match only whole words in the prompt
            if f" {company} " in f" {lowercase_prompt} ":
                company_name = company.capitalize()
                log_message(f"Company detected using fallback: {company_name}")
                break

    return company_name, year


# Function to scrape search results and filter valid SEC links
def google_search(query, num_results=5):
    # Google Search URL with the query
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"

    # Set a User-Agent to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }

    # Send the HTTP request to Google
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        log_message("Failed to fetch search results.")
        return None

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract the first valid SEC link ending with `.htm`
    for link in soup.find_all("a", href=True):
        href = link.get("href")
        if "sec.gov/Archives/edgar/data" in href and href.endswith(".htm"):
            if href.startswith("/url?q="):
                href = href.split("/url?q=")[1].split("&")[0]
            log_message(f"Found SEC link: {href}")
            return href

    log_message("No valid SEC link found.")
    return None


# Function to directly convert an online HTML page to a PDF using pdfkit
def convert_url_to_pdf(url, company, year):
    # Folder to save reports
    save_folder = os.path.join(os.getcwd(), "financial_reports")
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    try:
        # File name for the PDF
        filename = f"{company}_{year}_10K.pdf".replace(" ", "_")
        filepath = os.path.join(save_folder, filename)

        # Convert URL directly to PDF
        pdfkit.from_url(url, filepath)

        log_message(f"Document saved at: {filepath}")
        return filepath
    except Exception as e:
        log_message(f"Error converting URL to PDF: {e}")
        return None


# Main agent function to handle the process
def financial_report_agent(prompt):
    # Extract company and year from the prompt
    company, year = extract_company_and_year(prompt)

    if not company or not year:
        log_message("Error: Could not extract company name or year from the prompt.")
        return

    # Search for SEC 10-K reports
    query = f"{company} 10k {year} site:sec.gov/Archives/edgar/data"
    url = google_search(query)

    if not url:
        log_message("No valid links found in search results.")
        return

    # Attempt to convert the first valid document to PDF
    file_path = convert_url_to_pdf(url, company, year)
    if file_path:
        log_message(f"Successfully completed the process. File saved at {file_path}.")
    else:
        log_message("Failed to complete the process. No document downloaded.")


# Example usage
if __name__ == "__main__":
    # User prompt
    prompt = "Download the 10-K financial report for tesla for the year 2023"

    # Run the agent
    financial_report_agent(prompt)
