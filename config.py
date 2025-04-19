# config.py - Configuration for the Gemini Book Generator

# === Essential Settings ===

# The main topic or subject of the book.
BOOK_TOPIC = "The influence of reptilians on the development of humanity"

# Specify the Gemini model to use for content generation.
#GEMINI_MODEL = 'gemma-3-27b-it'
GEMINI_MODEL = 'gemini-2.5-flash-preview-04-17'

# === Book Type and Style Settings ===

# Specify the type of book: 'Non-Fiction' or 'Fiction->Textbook Style'
BOOK_TYPE = 'Fiction->Textbook Style'

# Briefly describe the fictional world/universe setting if using 'Fiction->Textbook Style'.
WORLD_SETTING = "Real world with the added fantasy that reptilians are hidden in plainsight and they are secretly controlling us"

# Define the specific style of the book.
BOOK_STYLE = "In-universe academic textbook"

# Define the target audience.
TARGET_AUDIENCE = "Highly intelligent and capable employees of secret governmental, research and resistance organisations"

# Describe the desired writing style.
WRITING_STYLE = "Formal"


# === Copyright Settings ===

# Enter the name of the copyright holder.
COPYRIGHT_HOLDER = "Fufu Fang"

# Optional: Add ISBN if you have one (leave blank if not)
# ISBN = ""

# === Content Generation Settings ===

# --- Chapter and Section Structure ---
# Approximate number of chapters desired (including Intro/Conclusion).
APPROX_CHAPTERS = 15 # Adjusted example

# Approximate number of sections desired per chapter.
# The AI will try to create a ToC with roughly this many sections under each chapter.
APPROX_SECTIONS_PER_CHAPTER = 5 # Adjusted example

# --- Section Content ---
# Target word count range for each SECTION. (min, max).
# This allows for more manageable AI generation requests.
# Total chapter length will be approx. sections_per_chapter * section_length.
TARGET_SECTION_WORDS_RANGE = (1700, 2300) # Example range per section


# === Optional Settings (for potential future enhancements) ===
# PDF_FONT_SIZE = 11
# DOCX_FONT_SIZE = 11