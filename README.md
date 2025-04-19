# Fully Automatic Gemini Book Generator

This project uses the Google Gemini API to automatically generate a draft manuscript for a book based on user-defined configuration settings. It generates a title, a two-level table of contents (Chapters and Sections), and the content for each section. The output includes a PDF suitable for KDP print (6x9 format with front matter and accurate ToC page numbers) and a DOCX file suitable for reflowable ebooks (with heading structure for manual ToC generation in Word).

## Features

* **Configuration Driven:** Define book topic, style, audience, structure, and more in `config.py`.
* **Gemini API Integration:** Leverages Google's generative AI for content creation.
* **Fiction & Non-Fiction Modes:** Supports generating standard non-fiction or fiction written in a textbook/in-universe style.
* **Section-by-Section Generation:** Creates content in manageable section chunks for potentially longer chapters.
* **PDF Output:** Generates a 6x9 PDF including Title Page, Copyright Page, and a Table of Contents with accurate page numbers (via multi-pass generation). Body text is left-aligned.
* **DOCX Output:** Generates a reflowable DOCX file with Chapter titles styled as Heading 1 and Section titles as Heading 2, allowing for easy ToC generation within Word.
* **API Call Caching:** Caches responses from the Gemini API locally (`api_cache/`) to speed up subsequent runs during output formatting experiments and reduce API costs.
* **Automatic Font Handling:** Includes a script (`setup_fonts.py`) to download and install necessary DejaVu fonts for PDF generation if they are missing.
* **Basic Markdown Handling:** Parses and renders basic Markdown (`**bold**`, `*italic*`) found in the generated content in both PDF and DOCX outputs.

## Project Structure

    fully-automatic-gemini-book-generator/
    ├── .env                  # Stores your API key (MUST be gitignored)
    ├── .git/                 # Git repository data
    ├── .gitignore            # Specifies intentionally untracked files by Git
    ├── api_cache/            # Stores cached API responses (MUST be gitignored)
    ├── config.py             # User configuration for the book generation
    ├── fonts/                # Stores downloaded DejaVu TTF fonts
    ├── output/               # Default directory for generated PDF and DOCX files
    ├── venv/                 # Python virtual environment files (Should be gitignored)
    ├── main.py               # Main script to run the book generation
    ├── setup_fonts.py        # Script to download necessary fonts (run automatically by main.py)
    ├── requirements.txt      # Lists Python package dependencies
    └── README.md             # This file


## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd fully-automatic-gemini-book-generator
    ```
    (Replace `<repository_url>` if you host this on GitHub/GitLab etc.)

2.  **Create Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate.bat` or `venv\Scripts\Activate.ps1`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    This installs: `google-generativeai`, `fpdf2`, `python-docx`, `python-dotenv`, `pypdf`, `markdown-it-py`.

4.  **Get Gemini API Key:**
    * Obtain an API key from Google AI Studio ([https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)) or Google Cloud Console.

5.  **Configure API Key:**
    * Create a file named `.env` in the project root directory.
    * Add your API key to the `.env` file like this:
        ```
        GEMINI_API_KEY=YOUR_API_KEY_HERE
        ```
        (Replace `YOUR_API_KEY_HERE` with your actual key).

6.  **Configure `.gitignore`:**
    * Ensure your `.gitignore` file exists and contains at least the following lines to prevent committing secrets and cache data:
        ```gitignore
        venv/
        .env
        api_cache/
        __pycache__/
        *.pyc
        output/*.pdf
        output/*.docx
        fonts/*.zip
        fonts/extracted_fonts/
        ```

7.  **Font Setup:** The necessary fonts (DejaVu Sans variants) will be checked and downloaded automatically by `main.py` (using `setup_fonts.py`) if they are not found in the `fonts/` directory during the first run.

## Configuration

Edit the `config.py` file to define the book you want to generate:

* `BOOK_TOPIC`: The main subject (can be real or fictional).
* `GEMINI_MODEL`: Which Gemini model to use (e.g., `gemini-1.5-flash`).
* `BOOK_TYPE`: Set to `'Non-Fiction'` or `'Fiction->Textbook Style'`.
* `WORLD_SETTING`: Describe the fictional world (required if `BOOK_TYPE` is fiction).
* `BOOK_STYLE`: Specify the book's style (e.g., `In-universe academic textbook`).
* `WRITING_STYLE`: Describe the desired tone and style (e.g., `Formal and slightly archaic`).
* `TARGET_AUDIENCE`: Define who the book is for.
* `COPYRIGHT_HOLDER`: Your name, pseudonym, or institution for the copyright page.
* `APPROX_CHAPTERS`: Guideline for the total number of chapters.
* `APPROX_SECTIONS_PER_CHAPTER`: Guideline for sections within each chapter.
* `TARGET_SECTION_WORDS_RANGE`: Tuple `(min, max)` words desired *per section*.

## Usage

1.  **Edit `config.py`** with your desired settings for the book.
2.  **Activate** your virtual environment (`source venv/bin/activate`).
3.  **Run the script:**
    ```bash
    python main.py
    ```
4.  The script will:
    * Validate the configuration.
    * Check/download fonts if needed.
    * Generate Title, ToC, and Section Content (using API calls or cache).
    * Generate the final PDF and DOCX files in the `output/` directory.
5.  **For the DOCX file:** Open it in Microsoft Word (or a compatible editor) and update the Table of Contents field (usually by right-clicking the placeholder text and selecting "Update Field" -> "Update entire table").

## Caching

* To speed up development and reduce API usage, successful responses from the Gemini API are cached locally in the `api_cache/` directory.
* Cache files are named based on a hash of the prompt text.
* If you run the script again with the *exact same configuration* leading to the *exact same prompts*, the cached results will be used instead of calling the API.
* To force regeneration of content for a specific part (e.g., a section), you can delete the corresponding `.pkl` file from the `api_cache/` directory, or simply delete the entire directory to clear the cache. Remember to add `api_cache/` to your `.gitignore`.

## Important Notes

* **Content Quality:** AI-generated content requires careful review, editing, and fact-checking (especially for non-fiction) before publishing. Treat the output as a first draft.
* **API Costs:** Be aware of potential costs associated with using the Gemini API, especially when generating large amounts of text. Caching helps mitigate this during development.
* **PDF ToC:** The generated PDF includes a Table of Contents with accurate page numbers achieved through multi-pass generation. However, the ToC entries themselves are *not* currently implemented as clickable hyperlinks due to complexities in single-pass PDF generation libraries.
* **DOCX ToC:** The DOCX file relies on standard Word heading styles (Heading 1 for chapters, Heading 2 for sections). The user *must* manually update the ToC field within Word to generate the final Table of Contents with page numbers and links.
* **Long Content:** Generating very long sections might still encounter API limits or timeouts, potentially resulting in incomplete content for that section.

## License
    Fully Automatic Gemini Book Generator
    Copyright (C) 2025  Fufu Fang

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.