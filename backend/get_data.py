import csv
import requests
from bs4 import BeautifulSoup

# Define your list of links (if not reading from a file)
links = [
    {
        "Link": "https://bulletins.nyu.edu/class-search/",
        "Description": "nyu public course search (beta)",
        "Access": "you can configure the search query through URL query vars"
    },
    {
        "Link": "https://cas.nyu.edu/core.html",
        "Description": "nyu CAS core curriculum",
        "Access": "find core curriculum requirement and courses that are offered each year"
    },
    {
        "Link": "https://www.nyu.edu/students/student-information-and-resources/registration-records-and-graduation/academic-calendar.html",
        "Description": "nyu academic calendar",
        "Access": "academic calendar for course registration, breaks, finals, etc."
    },
    # ... add your additional links
]

# File name for the output CSV file
output_filename = "backend/nyu_data.csv"

# Open the CSV file for writing (creates file if not exists)
with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
    # Define the header fields
    fieldnames = ['Link', 'Description', 'Access', 'Content']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Iterate over your list of links
    for entry in links:
        url = entry['Link']
        print(f"Processing {url} ...")
        try:
            # Make an HTTP request to get the webpage (you can set a timeout or custom headers)
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raises an error on a bad status

            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract the text content; you can adjust to target specific page elements if needed
            content = soup.get_text(separator=' ', strip=True)
        except Exception as e:
            content = f"Error fetching page: {e}"
        
        # Add the page content to your entry
        entry['Content'] = content
        
        # Write the row to your CSV
        writer.writerow(entry)

print("Finished processing all links. Check the nyu_data.csv file.")