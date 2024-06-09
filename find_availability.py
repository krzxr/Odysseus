import subprocess
import json
from datetime import datetime, timedelta
import pytz

class Odysseus:
    def __init__(self, park_ids, stdout):
        self.park_ids = park_ids
        self.stdout = stdout

    def fetch_url_as_json(self, url):
        curl_command = ["curl", "-s", url]
        result = subprocess.run(curl_command, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                self.stdout("Failed to parse JSON response")
                return None
        else:
            self.stdout(f"Failed to fetch data. Return code: {result.returncode}")
            self.stdout(result.stderr)
            return None

    def fetch_availability(self, park_id, start_date, end_date):
        url = f"https://www.recreation.gov/api/permitinyo/{park_id}/availability?start_date={start_date}&end_date={end_date}"
        return self.fetch_url_as_json(url)

    def find_days_with_minimum_spots(self, data, trail_id, min_spots=2):
        pacific_tz = pytz.timezone('US/Pacific')
        today = datetime.now(pacific_tz).date()
        days_with_min_spots = {}
        for date, availability in data.get('payload', {}).items():
            trail_info = availability.get(str(trail_id))
            if trail_info and trail_info.get("remaining", 0) >= min_spots:
                day_date = datetime.strptime(date, "%Y-%m-%d").date()
                if day_date > today:
                    days_with_min_spots[date] = {
                        "remaining": trail_info.get("remaining", 0),
                        "day_of_week": day_date.strftime("%A")
                    }
        return days_with_min_spots

    def get_next_n_months(self, months_to_check):
        today = datetime.today()
        months = []
        for i in range(months_to_check):
            start_date = (today.replace(day=1) + timedelta(days=i*30)).strftime("%Y-%m-01")
            next_month = today.replace(day=28) + timedelta(days=(i+1)*30)
            end_date = (next_month - timedelta(days=next_month.day)).strftime("%Y-%m-%d")
            months.append((start_date, end_date))
        return months

    def check_trail_availability(self, park_name, months_to_check, min_spots=2):
        if park_name not in self.park_ids:
            self.stdout(f"Park name '{park_name}' not found in the map.")
            return

        park_info = self.park_ids[park_name]
        park_id = park_info["park_id"]

        for trail_name, trail_id in park_info["trails"].items():
            self.stdout(f"\nChecking trail '{trail_name}' (ID: {trail_id}) in park '{park_name}' (ID: {park_id})...")

            months = self.get_next_n_months(months_to_check)
            for start_date, end_date in months:
                self.stdout(f"Checking availability from {start_date} to {end_date}...")
                availability_data = self.fetch_availability(park_id, start_date, end_date)
                if availability_data:
                    days = self.find_days_with_minimum_spots(availability_data, trail_id, min_spots)
                    if days:
                        self.stdout(f"Days with at least {min_spots} remaining spots from {start_date} to {end_date}:")
                        for day, info in days.items():
                            self.stdout(f"{day} ({info['day_of_week']}): {info['remaining']} spots available")
                    else:
                        self.stdout(f"No days with at least {min_spots} remaining spots from {start_date} to {end_date}.")
                else:
                    self.stdout(f"Failed to fetch data for the period from {start_date} to {end_date}.")

# Example usage of the class
def custom_stdout(message):
    print(message)

park_ids = {
    "Mt. Whitney": {
        "park_id": 445860,
        "trails": {
            "Overnight": 166
        }
    },
    "Sequoia and Kings Canyon": {
        "park_id": 445857,
        "trails": {}
    },
    "Inyo": {
        "park_id": 233262,
        "trails": {
            "Kearsarge Pass": 465
        }
    }
}

odysseus = Odysseus(park_ids, custom_stdout)
odysseus.check_trail_availability("Mt. Whitney", 3, 2)

