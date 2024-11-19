import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI

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
#print(link_system_prompt)

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
#anthropic = Webpage("https://anthropic.com")
#print(anthropic.links)  # Print the links extracted from the webpage
#print(get_links("https://anthropic.com"))  # Print the classified links

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

system_prompt = "You are an assistant that analyzes the contents of several relevant pages from a company website \
and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
Include details of company culture, customers and careers/jobs if you have the information."

# Or uncomment the lines below for a more humorous brochure - this demonstrates how easy it is to incorporate 'tone':

# system_prompt = "You are an assistant that analyzes the contents of several relevant pages from a company website \
# and creates a short humorous, entertaining, jokey brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
# Include details of company culture, customers and careers/jobs if you have the information."

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

def create_brochure(company_name, url):
    """
    Creates a brochure about a company using the OpenAI API.

    :param company_name: The name of the company.
    :param url: The URL of the company's website.
    :return: The generated brochure content.
    """
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
    )
    result = response.choices[0].message.content
    return print(result)

# Example usage of the create_brochure function
print(create_brochure("Tlantic", "https://tlantic.com"))



