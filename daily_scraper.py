import os
import re
import csv
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
padel_login = os.environ.get("PADEL_LOGIN")
padel_pass = os.environ.get("PADEL_PASSWORD")
if not padel_pass or not padel_login:
    raise ValueError("Login or password were not found in environment variables.")

def save_to_csv(scraped_data, output_folder="output"):
    """
    Saves the scraped data to a CSV file in the specified output folder.
    The filename includes the current timestamp.
    """
    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_folder, f"scraped_data_{timestamp}.csv")

    # Write data to CSV
    with open(output_file, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["section_name", "date_scraped", "start_hour", "end_hour", "reserved"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

        # Write rows
        for section in scraped_data:
            section_name = section["section_name"]
            date = section["date_scraped"]
            for slot in section["hour_slots"]:
                writer.writerow({
                    "section_name": section_name,
                    "date_scraped": date,
                    "start_hour": slot["start_hour"],
                    "end_hour": slot["end_hour"],
                    "reserved": slot["reserved"]
                })

    print(f"Data saved to {output_file}")

def extract_hours(hour_string):
    """
    Extracts the hour from the given string.
    """
    match = re.match(r"(\d{1,2}:\d{2}) > (\d{1,2}:\d{2})", hour_string)
    if match:
        start_time, end_time = match.groups()
        return start_time, end_time
    return None, None

def scrape_website(date, reserve_duration=60):
    assert reserve_duration in (60, 120), "reserve_duration must be either 60 or 120 minutes"

    login_data ={
        'client': 'scdescription',
        'task': 'dologin',
        'url': 'CasaPadel.html?iframe=iframe',
        'scid': 'CasaPadel',
        'username': padel_login,
        'password': padel_pass
    }

    with requests.Session() as session:
        url = "https://reservadeportes.com/index.php?client=scdescription&scid=CasaPadel"
        response = session.post(url, data=login_data)     
        if response.status_code != 200:
            raise Exception("Login failed")
        print("Login successful")

        # Scrape the page
        url = f"https://reservadeportes.com/calendario/CasaPadel/9/{date}/{reserve_duration}/"
        response = session.get(url)
        print(f"Scrape response status: {response.status_code}")

        reservation_data = []
        soup = BeautifulSoup(response.content, 'html.parser')
        for item in soup.find_all("div", class_="shadow rounded p-3"):
            section_name = item.find("h4", class_="txt-c-primary").text

            hour_slot_data = []
            for hour_slot in item.find_all('a'):
                start_hour, end_hour = extract_hours(hour_slot.find("span").text)
                if 'btn-success' in hour_slot["class"]:
                    reserverd = False
                else:
                    reserverd = True

                hour_slot_data.append({
                    "start_hour": start_hour,
                    "end_hour": end_hour,
                    "reserved": reserverd
                })
            
            reservation_data.append({
                "section_name": section_name,
                "date_scraped": date,
                "hour_slots": hour_slot_data
            })
        print("Data scraped successfully")

        return reservation_data


# Main function
if __name__ == "__main__":
    try:
        collected_data = []
        for i in range(0,15+1): # Data can be scraped for tomorrow and up to 15 days in advance
            date = datetime.now().date() + timedelta(days=i)
            print(f"Scraping data for {date}...")
            scraped_data = scrape_website(date=date)
            print("Scraping completed.")
            collected_data.extend(scraped_data)
        print("All data collected.")
        print("Saving data to CSV...")
        save_to_csv(collected_data)
        print("Data saved successfully.")

    except Exception as e:
        print(f"An error occurred: {e}") 