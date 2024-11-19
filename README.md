# AI-website-brochure-summarizer

1. Project description and purpose
2. Installation requirements
3. Setup instructions
4. Usage examples
5. Functions documentation
6. Dependencies
7. Examples

# AI Website Brochure Generator

A Python tool that automatically generates company brochures by scraping website content using OpenAI's GPT models.

## Installation

```bash
# Clone the repository
git clone <repository-url>

# Install required packages
pip install requests beautifulsoup4 python-dotenv openai
```

## Setup

1. Create a 

.env

 file in the project root:
```bash
OPENAI_API_KEY=your-api-key-here
```

2. Ensure you have Python 3.6+ installed

## Usage

```python
from ai_website_brochure import create_brochure

# Generate a brochure for a company
brochure = create_brochure("Company Name", "https://company-website.com")
```

## Features

- Web scraping of company websites
- Intelligent link classification
- Content extraction and cleaning
- Automated brochure generation using GPT models
- Streaming support for real-time brochure creation

## Core Functions

- `Webpage`: Class for handling webpage content extraction
- `get_links()`: Extracts and classifies relevant links
- `get_all_details()`: Compiles information from main page and relevant links
- `create_brochure()`: Generates the final brochure using OpenAI
- `stream_brochure()`: Streams the brochure generation process

## Dependencies

- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `python-dotenv`: Environment variable management
- `openai`: OpenAI API interaction

## Examples

```python
# Generate a standard brochure
brochure = create_brochure("Anthropic", "https://anthropic.com")

# Generate a humorous brochure (uncomment alternative system_prompt)
# brochure = create_brochure("Anthropic", "https://anthropic.com")
```

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request