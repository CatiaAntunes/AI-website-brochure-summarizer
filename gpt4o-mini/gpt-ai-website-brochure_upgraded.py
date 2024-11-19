import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI

EXAMPLE_BROCHURES = [
    {
        "company": "TechCorp",
        "brochure": """
                    # TechCorp - Innovating Tomorrow

                    ## Our Mission
                    Building revolutionary software solutions.

                    ## Products & Services
                    - Cloud Computing Platform
                    - AI Solutions
                    - Enterprise Software

                    ## Why Choose Us
                    - 20 years of excellence
                    - Global presence
                    - Industry leaders

                    ## Career Opportunities
                    Join our dynamic team of innovators.

                    ## Contact
                    www.techcorp.com
                    """
    },
    # Add more examples as needed
]

# Initialize API and constants
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if api_key and api_key[:8] == 'sk-proj-':
    print("API key is valid")
else:
    print("There was an issue with the API key")

MODEL = 'gpt-4o-mini'
openai = OpenAI()

# Class to represent the WebPage
class Webpage:
    """
    Class to represent a webpage that we'll scrape for content and links to other pages.
    """

    def __init__(self, url):
        """
        Initializes the Webpage object by fetching the content of the URL, parsing it with BeautifulSoup,
        and extracting the title and links.

        :param url: The URL of the webpage to scrape.
        """
        self.url = url
        
        # Send a GET request to the URL and store the response content
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.body = response.content
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the URL: {e}")
            self.body = ""
            self.title = "No title found"
            self.links = []
            return
        
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(self.body, 'html.parser')
        
        # Extract the title of the webpage, if available
        self.title = soup.title.string if soup.title else "No title found"
        
        # Remove irrelevant tags (script, style, img, input) from the body to clean up the text
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n").strip()
        else:
            self.text = ""
        
        # Get the href attribute for each link in the page found with soup.find_all('a')
        links = [link.get('href') for link in soup.find_all('a')]
        
        # Keep the links that are not None (if link assures that the link is not None)
        self.links = [link for link in links if link]

    def get_contents(self):
        """
        Returns a formatted string containing the title and text content of the webpage.

        :return: A string with the webpage title and its cleaned text content.
        """
        return f"Webpage Title: \n{self.title}\nWebpage Contents:\n{self.text}\n\n"

# Define a system prompt for link classification
link_system_prompt = (
    "You are provided with a list of links found on a webpage. You are able to decide which of the links would be most relevant to include in a brochure about the company, such as links to an About Page, or a Company page, or Careers/Jobs page. \n"
    "You should respond in JSON as in this example:"
    """
    {
        "links": [
            {"type": "about page", "url": "https://full.url/goes/here/about"},
            {"type": "careers page", "url": "https://another.full.url/careers"}
        ]
    }
    """
)
# Display the prompt
print(link_system_prompt)

# Function to generate a user prompt for link classification
def get_links_user_prompt(website):
    """
    Generates a user prompt for classifying links found on a webpage.

    :param website: An instance of the Webpage class.
    :return: A formatted string prompting the user to classify the links.
    """
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += "please decide which of these are relevant web links for a brochure about the company, respond with the full https URL in JSON format. \
Do not include Terms of Service, Privacy, email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt

def get_links(url):
    """
    Fetches and classifies links from a given URL using the OpenAI API.

    :param url: The URL of the webpage to scrape and classify links from.
    :return: A JSON object containing the classified links.
    """
    # Create an instance of the Webpage class
    website = Webpage(url)
    
    # Generate a response from the OpenAI API
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(website)}
        ],
        response_format={"type": "json_object"}
    )
    
    # Extract and parse the JSON content from the response
    result = response.choices[0].message.content
    return json.loads(result)

# Example usage of the get_links function
anthropic = Webpage("https://anthropic.com")
print(anthropic.links)  # Print the links extracted from the webpage
print(get_links("https://anthropic.com"))  # Print the classified links

def get_all_details(url):
    """
    Fetches and compiles details from the landing page and relevant links of a given URL.

    :param url: The URL of the webpage to scrape and compile details from.
    :return: A formatted string containing the compiled details of the webpage and its relevant links.
    """
    result = "Landing page:\n"
    result += Webpage(url).get_contents()
    links = get_links(url)
    print("Found links:", links)
    for link in links["links"]:
        result += f"\n\n{link['type']}\n"
        result += Webpage(link["url"]).get_contents()
    return result

# Example usage of the get_all_details function
print(get_all_details("https://anthropic.com"))

BROCHURE_FORMAT = """
                    # {company_name}

                    ## Company Overview
                    [Brief description of the company]

                    ## Products & Services
                    - [Key offerings]
                    - [Main products]
                    - [Service categories]

                    ## Innovation & Technology
                    [Company's technological achievements and focus]

                    ## Culture & Values
                    [Company culture and core values]

                    ## Career Opportunities
                    [Available positions and growth prospects]

                    ## Client Success Stories
                    [Brief case studies or testimonials]

                    ## Contact Information
                    [How to reach the company]
                    """

system_prompt = f"""You are an assistant that analyzes company websites and creates professional brochures.
                Follow this exact format:

                {BROCHURE_FORMAT}

                Ensure each section is comprehensive yet concise.
                Use bullet points for lists.
                Include specific examples and data when available.
                """                                 

def get_brochure_user_prompt(company_name, url):
    """
    Generates a user prompt for creating a brochure about a company.

    :param company_name: The name of the company.
    :param url: The URL of the company's website.
    :return: A formatted string prompting the user to create a brochure.
    """
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short brochure of the company in markdown.\n"
    user_prompt += get_all_details(url)
    user_prompt = user_prompt[:20_000]  # Truncate if more than 20,000 characters
    return user_prompt

# Example usage of the get_brochure_user_prompt function
#print(get_brochure_user_prompt("Anthropic", "https://anthropic.com"))

def create_brochure_with_examples(company_name, url):
    """
    Creates a brochure using few-shot learning with examples.
    
    :param company_name: The name of the company
    :param url: The URL of the company's website
    :return: Formatted brochure content
    """
    messages = [
        {"role": "system", "content": f"{system_prompt}\n\nUse this format:\n{BROCHURE_FORMAT}"}
    ]
    
    # Add examples as few-shot learning
    for example in EXAMPLE_BROCHURES:
        messages.extend([
            {"role": "user", "content": f"Create a brochure for {example['company']}"},
            {"role": "assistant", "content": example['brochure']}
        ])
    
    messages.append({
        "role": "user", 
        "content": get_brochure_user_prompt(company_name, url)
    })
    
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7  # Add control over creativity
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating brochure: {e}")
        return None

def translate_to_german(text):
    """
    Translates the brochure to German.
    """
    translation_prompt = "Translate the following company brochure to German, maintaining the markdown formatting:"
    
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a professional translator specializing in business documents."},
            {"role": "user", "content": f"{translation_prompt}\n\n{text}"}
        ]
    )
    return response.choices[0].message.content

def generate_complete_brochure(company_name, url):
    """
    Generates a complete brochure with English and German versions.
    """
    # Generate English brochure
    english_brochure = create_brochure_with_examples(company_name, url)
    
    # Translate to German
    german_brochure = translate_to_german(english_brochure)
    
    return {
        "english": english_brochure,
        "german": german_brochure
    }

# Example usage
if __name__ == "__main__":
    company_name = "Tlantic"
    url = "https://www.tlantic.com/en"
    
    brochures = generate_complete_brochure(company_name, url)
    
    print("=== English Version ===")
    print(brochures["english"])
    print("\n=== German Version ===")
    print(brochures["german"])



