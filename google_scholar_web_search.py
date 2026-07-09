import requests
from bs4 import BeautifulSoup
import time
from scholarly import scholarly

# 普通关键词搜索函数
def google_scholar_search(query, num_results=5):
    """
    Function to search Google Scholar using a simple keyword query.
    
    Parameters:
    query (str): The search query (e.g., paper title or author).
    num_results (int): The number of results to retrieve.
    
    Returns:
    list: A list of dictionaries containing search results.
    """
    # Prepare the search URL. Using requests' `params=` lets it handle
    # proper URL-encoding (spaces, accents, punctuation) automatically,
    # instead of manually replacing spaces with '+' and leaving everything
    # else unescaped.
    search_url = "https://scholar.google.com/scholar"
    search_params = {'q': query}

    # Set up headers to mimic a real browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Send the GET request to Google Scholar
    response = requests.get(search_url, params=search_params, headers=headers)
    
    # Check if the request was successful
    if response.status_code != 200:
        # NOTE: never print() here - this process's stdout is the MCP
        # JSON-RPC channel to Claude Desktop. Any stray text on stdout
        # corrupts that stream and can crash the whole connection.
        return [{"error": f"Failed to fetch data. HTTP Status code: {response.status_code}"}]

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all the articles in the search results
    results = []
    count = 0

    # Find the results on the page
    for item in soup.find_all('div', class_='gs_ri'):
        if count >= num_results:
            break

        title_tag = item.find('h3', class_='gs_rt')
        title = title_tag.get_text() if title_tag else 'No title available'

        link = title_tag.find('a')['href'] if title_tag and title_tag.find('a') else 'No link available'

        authors_tag = item.find('div', class_='gs_a')
        authors = authors_tag.get_text() if authors_tag else 'No authors available'

        abstract_tag = item.find('div', class_='gs_rs')
        abstract = abstract_tag.get_text() if abstract_tag else 'No abstract available'

        result_data = {
            'Title': title,
            'Authors': authors,
            'Abstract': abstract,
            'URL': link
        }
        results.append(result_data)
        count += 1

    return results

# 高级搜索函数
def advanced_google_scholar_search(query, author=None, year_range=None, num_results=5):
    """
    Function to search Google Scholar using advanced search filters (e.g., author, year range).
    
    Parameters:
    query (str): The search query (e.g., paper title or topic).
    author (str): The author's name to filter the results (default is None).
    year_range (tuple): A tuple (start_year, end_year) to filter the results by publication year (default is None).
    num_results (int): The number of results to retrieve.
    
    Returns:
    list: A list of dictionaries containing search results.
    """
    # Prepare the advanced search URL. Google Scholar's advanced-search
    # fields (as_q, as_sauthors, as_ylo, as_yhi, ...) only reliably combine
    # with each other when the main query also uses 'as_q' - mixing the
    # plain 'q' field with 'as_*' fields causes Google to silently ignore
    # the 'as_*' filters.
    search_url = "https://scholar.google.com/scholar"

    search_params = {'as_q': query}
    if author:
        # 'as_sauthors' is the correct Google Scholar parameter for
        # restricting to specific authors. The old 'as_auth' key is not
        # a real Google Scholar parameter, so it was silently ignored,
        # meaning the author filter never actually applied.
        search_params['as_sauthors'] = author
    if year_range:
        start_year, end_year = year_range
        search_params['as_ylo'] = start_year  # Start year
        search_params['as_yhi'] = end_year  # End year

    # Set up headers to mimic a real browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Send the GET request to Google Scholar. Passing search_params via
    # `params=` lets requests handle proper URL-encoding (spaces, accents,
    # commas, etc.) instead of the previous manual string concatenation,
    # which broke on anything but plain ASCII author names.
    response = requests.get(search_url, params=search_params, headers=headers)
    
    # Check if the request was successful
    if response.status_code != 200:
        # NOTE: never print() here - this process's stdout is the MCP
        # JSON-RPC channel to Claude Desktop. Any stray text on stdout
        # corrupts that stream and can crash the whole connection.
        return [{"error": f"Failed to fetch data. HTTP Status code: {response.status_code}"}]

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all the articles in the search results
    results = []
    count = 0

    # Find the results on the page
    for item in soup.find_all('div', class_='gs_ri'):
        if count >= num_results:
            break

        title_tag = item.find('h3', class_='gs_rt')
        title = title_tag.get_text() if title_tag else 'No title available'

        link = title_tag.find('a')['href'] if title_tag and title_tag.find('a') else 'No link available'

        authors_tag = item.find('div', class_='gs_a')
        authors = authors_tag.get_text() if authors_tag else 'No authors available'

        abstract_tag = item.find('div', class_='gs_rs')
        abstract = abstract_tag.get_text() if abstract_tag else 'No abstract available'

        result_data = {
            'Title': title,
            'Authors': authors,
            'Abstract': abstract,
            'URL': link
        }
        results.append(result_data)
        count += 1

    return results
