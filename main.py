import google.generativeai as genai
import os
import re
import time
from dotenv import load_dotenv
from fpdf import FPDF
from docx import Document
from docx.shared import Inches, Pt
# from docx.enum.text import WD_PARAGRAPH_ALIGNMENT # Alignment not strictly needed for basic reflowable
import string # For cleaning filenames

# --- Configuration ---
print("Loading configuration...")
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env file.")
    print("Please create a .env file in the project root with GEMINI_API_KEY=YOUR_API_KEY")
    exit()

OUTPUT_DIR = "output"
# PDF Settings (6x9 inches in mm)
PDF_WIDTH_MM = 152.4
PDF_HEIGHT_MM = 228.6
PDF_MARGIN_MM = 19.05 # 0.75 inches common for KDP
# DOCX Settings (for basic structure, KDP reflowable ignores most page setup)
DOCX_WIDTH_INCHES = 6
DOCX_HEIGHT_INCHES = 9
DOCX_MARGIN_INCHES = 0.75

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"Output directory is: {os.path.abspath(OUTPUT_DIR)}")

# Ensure fonts directory and files exist for PDF
FONT_DIR = 'fonts'
REGULAR_FONT_PATH = os.path.join(FONT_DIR, 'DejaVuSans.ttf')
BOLD_FONT_PATH = os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf')

if not (os.path.exists(REGULAR_FONT_PATH) and os.path.exists(BOLD_FONT_PATH)):
     print("\nERROR: DejaVu Sans fonts not found!")
     print(f"Please download DejaVuSans.ttf and DejaVuSans-Bold.ttf from https://dejavu-fonts.github.io/")
     print(f"and place them inside the '{FONT_DIR}' directory in your project root.")
     # Optionally exit if fonts are critical and not found
     # exit()
     print("WARN: Proceeding without guaranteed fonts. PDF output may fail or look incorrect.")


# --- Gemini Setup ---
print("Configuring Gemini API...")
try:
    genai.configure(api_key=API_KEY)
    # Using 1.5 Flash - balances speed and capability. Consider 'gemini-pro' if needed.
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Gemini API configured successfully.")
except Exception as e:
    print(f"ERROR configuring Gemini: {e}")
    print("Please ensure your API key is correct and network connection is stable.")
    exit()

# --- Helper Functions ---
def clean_filename(name):
    """Removes invalid characters for filenames and replaces spaces."""
    print(f"Cleaning filename for: '{name}'")
    # Allow letters, numbers, underscore, hyphen, period, parentheses
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_name = ''.join(c for c in name if c in valid_chars)
    # Replace spaces with underscores for better compatibility
    cleaned_name = cleaned_name.replace(' ', '_')
    # Limit length to avoid issues
    cleaned_name = cleaned_name[:100]
    print(f"Cleaned filename: '{cleaned_name}'")
    # Handle case where cleaning results in empty string
    return cleaned_name if cleaned_name else "untitled_book"

# --- Gemini Generation Functions ---
def generate_with_gemini(prompt_text, retries=3, delay=5):
    """
    Calls the Gemini API with retries, delay, and enhanced error checking.
    Explicitly asks for text generation.
    """
    print(f"\n--- Calling Gemini (prompt length: {len(prompt_text)} chars)...")
    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1}/{retries}...")
            # Generate content using the configured model
            response = model.generate_content(prompt_text)

            # 1. Check for Prompt Feedback (Immediate block)
            if response.prompt_feedback.block_reason:
                reason = response.prompt_feedback.block_reason
                print(f"WARN: Prompt blocked by API. Reason: {reason}. Attempt {attempt + 1}/{retries}")
                if attempt == retries - 1:
                    print("ERROR: Prompt blocked after max retries. Cannot proceed.")
                    return None
                print(f"Waiting for {delay} seconds before retrying...")
                time.sleep(delay)
                continue # Retry

            # 2. Check if Candidates exist and have content parts
            if not response.candidates or not hasattr(response.candidates[0], 'content') or not response.candidates[0].content.parts:
                 print(f"WARN: Gemini returned no valid content structure. Attempt {attempt + 1}/{retries}")
                 if attempt == retries - 1:
                     print("ERROR: Gemini returned no content after max retries.")
                     return None
                 print(f"Waiting for {delay} seconds before retrying...")
                 time.sleep(delay)
                 continue # Retry

            # 3. Check Candidate Finish Reason
            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason
            if finish_reason != 'STOP':
                # Other reasons: MAX_TOKENS, SAFETY, RECITATION, OTHER
                print(f"WARN: Generation finished unexpectedly. Reason: {finish_reason}. Content might be incomplete. Attempt {attempt+1}/{retries}")
                # Decide if retry is useful based on reason (e.g., maybe not for MAX_TOKENS)
                # For now, we'll proceed but warn the user. Can add retry logic here too.

            # 4. Check Candidate Safety Ratings
            if candidate.safety_ratings:
                 problematic_ratings = [r for r in candidate.safety_ratings if r.probability not in ['NEGLIGIBLE', 'LOW']]
                 if problematic_ratings:
                     print(f"WARN: Potentially harmful content detected by API: {problematic_ratings}. Attempt {attempt+1}/{retries}")
                     if attempt == retries - 1:
                         print("ERROR: Harmful content detected after max retries. Cannot proceed.")
                         return None
                     print(f"Waiting for {delay} seconds before retrying...")
                     time.sleep(delay)
                     continue # Retry

            # 5. Extract Text (if all checks passed)
            # Accessing response.text directly is simpler if available and checks passed
            result_text = response.text.strip()
            print(f"--- Gemini call successful (response length: {len(result_text)} chars)")
            return result_text

        except Exception as e:
            print(f"ERROR during Gemini API call (Attempt {attempt + 1}/{retries}): {e}")
            if "API key not valid" in str(e):
                 print("Please check your GEMINI_API_KEY in the .env file.")
                 return None # No point retrying if key is invalid
            if attempt == retries - 1:
                print("ERROR: Max retries reached after API exception.")
                return None
            print(f"Waiting for {delay} seconds before retrying...")
            time.sleep(delay)

    print(f"ERROR: Failed to get valid response from Gemini after {retries} attempts.")
    return None # Failed after all retries

def generate_title(topic):
    """Generates a book title using Gemini."""
    print("\n--- Generating Title ---")
    # Prompt asking for a list of titles, focusing on non-fiction style
    prompt = f"""Generate 5 potential book titles for a non-fiction book exploring the topic: '{topic}'.
The tone should be informative and engaging.
Present the titles as a simple list, with each title on a new line. Do not use numbers, bullets, or quotation marks around the titles.

Example format:
Title One Here
Another Title Example
A Third Option for a Title"""
    titles_text = generate_with_gemini(prompt)
    if not titles_text:
        print("WARN: Failed to generate titles text. Using fallback.")
        return "Untitled Book"

    # Split into lines and filter out empty ones
    possible_titles = [t.strip() for t in titles_text.split('\n') if t.strip()]

    if not possible_titles:
        print("WARN: No titles found in Gemini response. Using fallback.")
        return "Untitled Book"

    # Simple approach: return the first valid title found
    print(f"Generated Titles Choices:\n{titles_text}")
    selected_title = possible_titles[0]
    print(f"Selected Title: {selected_title}")
    return selected_title

def generate_toc(title, topic):
    """Generates a Table of Contents using Gemini."""
    print("\n--- Generating Table of Contents ---")
    # Prompt specifying exact format for easier parsing
    prompt = f"""Generate a detailed Table of Contents for a non-fiction book titled '{title}' about '{topic}'.
The book should logically progress through the topic. Include an Introduction and a Conclusion chapter.
List *only* the chapter titles, one per line, formatted *exactly* like this example:
1. Introduction: Setting the Stage
2. History of the Topic
3. Key Concepts Explained
4. Current State and Challenges
5. Future Trends and Innovations
6. Conclusion: Summary and Final Thoughts

Do not add any other text before or after the list."""
    toc_text = generate_with_gemini(prompt)
    return toc_text

def parse_toc(toc_text):
    """Parses the ToC text generated by Gemini into a list of chapter titles."""
    print("\n--- Parsing Table of Contents ---")
    if not toc_text:
        print("ERROR: Cannot parse empty ToC text.")
        return []

    print("--- Raw ToC Text ---")
    print(toc_text)
    print("--------------------")

    chapters = []
    # Try precise regex first (matches number, period, space, then captures the title)
    pattern_strict = re.compile(r"^\s*\d+\.\s+(.+)", re.MULTILINE)
    matches = pattern_strict.findall(toc_text)

    if matches:
        print("Parsing ToC using strict numbered list format.")
        chapters = [match.strip() for match in matches]
    else:
        # Fallback: Try splitting by newline and basic filtering
        print("WARN: Strict parsing failed. Falling back to line splitting.")
        potential_chapters = [line.strip() for line in toc_text.split('\n') if line.strip()]
        # Filter out lines that likely aren't chapters (e.g., too short, don't seem like titles)
        chapters = [ch for ch in potential_chapters if len(ch) > 5 and (ch[0].isdigit() or ch[0].isupper())]
        # Attempt to remove numbering if fallback included it
        chapters = [re.sub(r"^\s*\d+\.?\s*", "", ch) for ch in chapters]

    if not chapters:
        print("ERROR: Failed to parse any chapters from the ToC text.")
        return []

    print("Parsed Chapters:")
    for i, ch in enumerate(chapters, 1):
        print(f"{i}. {ch}")
    return chapters

def generate_chapter_content(chapter_title, book_title, topic):
    """Generates content for a single chapter using Gemini."""
    print(f"\n--- Generating Content for Chapter: '{chapter_title}' ---")
    # Prompt asking for substantial chapter content
    prompt = f"""You are an author writing a non-fiction book titled '{book_title}' about '{topic}'.
Write the full text content for the chapter titled: '{chapter_title}'.
Aim for a word count between 800 and 1500 words.
The writing style should be informative, clear, well-structured, and engaging for a general audience interested in '{topic}'.
Ensure the content directly addresses the theme indicated by the chapter title.
Structure the chapter logically with paragraphs. Do not use subheadings within the chapter text itself unless absolutely necessary for clarity.
**Important:** Output *only* the body text of the chapter. Do not include the chapter title (e.g., "Chapter X: Title") or any introductory/concluding remarks about the chapter itself (like "In this chapter, we will discuss..." or "This concludes the chapter on..."). Just provide the main content.
"""
    content = generate_with_gemini(prompt, retries=3, delay=10) # Longer delay for potentially longer generation
    if not content:
         print(f"WARN: Failed to generate content for chapter '{chapter_title}'. Returning placeholder.")
         return f"(Content generation failed for chapter: {chapter_title})"
    # Basic check for very short content which might indicate an issue
    if len(content.split()) < 100:
        print(f"WARN: Generated content for '{chapter_title}' seems very short ({len(content.split())} words). It might be incomplete or low quality.")
    return content

# --- Output Generation Functions ---

class PDF(FPDF):
    def header(self):
        # No automatic header needed for KDP content pages
        pass

    def footer(self):
        # Simple page number footer for content pages
        if self.page_no() > 2: # Start page numbering after title and ToC
            self.set_y(-15) # Position 1.5 cm from bottom
            self.set_font('DejaVu', '', 8)
            self.cell(0, 10, f'Page {self.page_no() - 2}', 0, 0, 'C') # Adjust page number display

def create_pdf(title, toc_list, chapters_content, filename):
    """Creates a 6x9 PDF book suitable for KDP paperback/hardcover."""
    print(f"\n--- Creating PDF: {filename} ---")

    # Check for fonts before proceeding
    if not (os.path.exists(REGULAR_FONT_PATH) and os.path.exists(BOLD_FONT_PATH)):
         print(f"ERROR: Cannot create PDF. Required fonts not found in '{FONT_DIR}'.")
         return False

    try:
        pdf = PDF(orientation='P', unit='mm', format=(PDF_WIDTH_MM, PDF_HEIGHT_MM))
        pdf.set_auto_page_break(auto=True, margin=PDF_MARGIN_MM)
        pdf.set_margins(left=PDF_MARGIN_MM, top=PDF_MARGIN_MM, right=PDF_MARGIN_MM)

        # Add Unicode fonts
        pdf.add_font('DejaVu', '', REGULAR_FONT_PATH, uni=True)
        pdf.add_font('DejaVu', 'B', BOLD_FONT_PATH, uni=True)

        # --- Title Page ---
        pdf.add_page()
        pdf.set_font('DejaVu', 'B', 24)
        pdf.ln(PDF_HEIGHT_MM / 4) # Move down about 1/4 of the page
        pdf.multi_cell(0, 15, title, align='C') # Use multi_cell for centering longer titles

        # --- Table of Contents Page ---
        pdf.add_page()
        pdf.set_font('DejaVu', 'B', 16)
        pdf.cell(0, 10, "Table of Contents", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font('DejaVu', '', 12)
        for i, chapter_title in enumerate(toc_list, 1):
            # Simple ToC - page numbers are harder without multi-pass processing
            pdf.multi_cell(0, 8, f"{i}. {chapter_title}", ln=True)

        # --- Chapters ---
        print("Adding chapter content to PDF...")
        for i, chapter_title in enumerate(toc_list, 1):
            content = chapters_content.get(chapter_title, f"Error: Content not found for {chapter_title}.")
            pdf.add_page()
            pdf.set_font('DejaVu', 'B', 14) # Chapter Title Font
            pdf.multi_cell(0, 10, f"Chapter {i}: {chapter_title}", ln=True, align='L')
            pdf.ln(5)
            pdf.set_font('DejaVu', '', 11) # Body Text Font
            # Split content by paragraphs and add them
            for paragraph in content.split('\n'):
                if paragraph.strip(): # Avoid empty lines creating extra space
                    pdf.multi_cell(0, 7, paragraph.strip(), ln=True) # 7mm line height approx 11pt font
                    pdf.ln(2) # Small space between paragraphs
                else:
                    pdf.ln(2) # Keep intentional line breaks if needed, adjust spacing

        pdf.output(filename)
        print(f"--- PDF successfully created: {filename} ---")
        return True
    except Exception as e:
        print(f"ERROR creating PDF: {e}")
        # Provide more context if possible, e.g., font issues
        if "Could not find font" in str(e):
             print(f"      Ensure fonts '{REGULAR_FONT_PATH}' and '{BOLD_FONT_PATH}' exist and are valid.")
        return False

def create_docx(title, toc_list, chapters_content, filename):
    """Creates a reflowable DOCX ebook suitable for KDP."""
    print(f"\n--- Creating DOCX: {filename} ---")
    try:
        doc = Document()

        # Optional: Set basic section properties (mostly ignored by KDP reflowable)
        section = doc.sections[0]
        section.page_width = Inches(DOCX_WIDTH_INCHES)
        section.page_height = Inches(DOCX_HEIGHT_INCHES)
        # Margins are less important here, but can set reasonable defaults
        for M in ['left_margin', 'right_margin', 'top_margin', 'bottom_margin']:
            setattr(section, M, Inches(DOCX_MARGIN_INCHES))

        # --- Title ---
        # Use built-in Title style or a prominent Heading 0
        doc.add_heading(title, level=0) # Level 0 is often interpreted as Title

        # --- Table of Contents ---
        doc.add_page_break()
        doc.add_heading("Table of Contents", level=1) # Use Heading 1 for ToC title
        for i, chapter_title in enumerate(toc_list, 1):
            # Add ToC entries as paragraphs. Could potentially add hyperlinks later if needed.
            doc.add_paragraph(f"{i}. {chapter_title}", style='List Paragraph') # Basic list style

        # --- Chapters ---
        print("Adding chapter content to DOCX...")
        for i, chapter_title in enumerate(toc_list, 1):
            content = chapters_content.get(chapter_title, f"Error: Content not found for {chapter_title}.")
            doc.add_page_break()
            doc.add_heading(f"Chapter {i}: {chapter_title}", level=1) # Use Heading 1 for chapter titles

            # Add content paragraph by paragraph for better reflowable structure
            for paragraph_text in content.split('\n'):
                if paragraph_text.strip(): # Add non-empty paragraphs
                    para = doc.add_paragraph(paragraph_text.strip())
                    # Optional: Add spacing after paragraphs for readability
                    # para_format = para.paragraph_format
                    # para_format.space_after = Pt(6) # e.g., 6 points after

        doc.save(filename)
        print(f"--- DOCX successfully created: {filename} ---")
        return True
    except Exception as e:
        print(f"ERROR creating DOCX: {e}")
        return False

# --- Main Execution ---
if __name__ == "__main__":
    print("\n========= Fully Automatic Gemini Book Generator =========")
    start_time = time.time()

    # 1. Get User Input
    book_topic = input("Enter the topic or main subject for your book: ")
    if not book_topic.strip():
        print("ERROR: Book topic cannot be empty.")
        exit()
    book_topic = book_topic.strip() # Clean input

    # 2. Generate Title
    book_title = generate_title(book_topic)
    if book_title == "Untitled Book": # Check for fallback/failure
        print("WARN: Proceeding with fallback title 'Untitled Book'.")
    # Clean title immediately for filenames
    safe_title = clean_filename(book_title)
    pdf_filename = os.path.join(OUTPUT_DIR, f"{safe_title}_6x9_print.pdf")
    docx_filename = os.path.join(OUTPUT_DIR, f"{safe_title}_ebook.docx")

    # 3. Generate Table of Contents (ToC)
    toc_raw_text = generate_toc(book_title, book_topic)
    if not toc_raw_text:
         print("ERROR: Failed to generate Table of Contents. Exiting.")
         exit()

    # 4. Parse ToC
    toc_list = parse_toc(toc_raw_text)
    if not toc_list:
        print("ERROR: Failed to parse Table of Contents. Cannot proceed with chapter generation. Exiting.")
        exit()

    # 5. Generate Content for Each Chapter
    print(f"\n--- Generating Content for {len(toc_list)} Chapters ---")
    all_chapters_content = {}
    total_chapters = len(toc_list)
    for i, chapter_title in enumerate(toc_list, 1):
        print(f"\n>>> Processing Chapter {i}/{total_chapters}: '{chapter_title}'")
        # Introduce a small delay between chapter generations to avoid hitting rate limits if any
        # time.sleep(2) # Optional delay (e.g., 2 seconds)
        content = generate_chapter_content(chapter_title, book_title, book_topic)
        all_chapters_content[chapter_title] = content # Store content even if it's a failure message

    # 6. Create Output Files
    print("\n--- Generating Final Output Files ---")
    pdf_success = create_pdf(book_title, toc_list, all_chapters_content, pdf_filename)
    docx_success = create_docx(book_title, toc_list, all_chapters_content, docx_filename)

    end_time = time.time()
    duration = end_time - start_time

    print("\n========= Generation Summary =========")
    print(f"Book Title: {book_title}")
    print(f"Topic: {book_topic}")
    print(f"Chapters Generated: {len(toc_list)}")
    if pdf_success:
        print(f"PDF (Print 6x9) saved to: {pdf_filename}")
    else:
        print("PDF generation failed.")
    if docx_success:
        print(f"DOCX (Ebook) saved to: {docx_filename}")
    else:
        print("DOCX generation failed.")
    print(f"Total execution time: {duration:.2f} seconds")
    print("====================================")