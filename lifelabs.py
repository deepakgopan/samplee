import requests
import smtplib
import os
import sys
from datetime import datetime, timedelta, time as dt_time
from email.mime.text import MIMEText
import pytz 

# ==========================================
#      CONFIGURATION (LOADED FROM SECRETS)
# ==========================================
try:
    SENDER_EMAIL = os.environ["SENDER_EMAIL"]
    SENDER_PASSWORD = os.environ["SENDER_PASSWORD"]
    RECEIVER_EMAIL = os.environ["RECEIVER_EMAIL"]
except KeyError:
    print("Error: Secrets not found. Make sure they are set in GitHub Settings.")
    sys.exit(1)

API_URL = "https://pwt-api.lifelabs.com/api/earliestAppt"
SITE_IDS = [
    "64d48c73-1592-ef11-8a69-7c1e5206227f",
    "2aa31b73-1592-ef11-8a6a-7c1e5240b167",
    "ced98c73-1592-ef11-8a69-7c1e5206227f",
    "6ee7066d-1592-ef11-8a6a-000d3af49e43",
    "3a50b270-1592-ef11-8a69-000d3af44d51",
    "7ad98c73-1592-ef11-8a69-7c1e5206227f",
    "720c9c70-1592-ef11-8a69-000d3af4c63f"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Origin": "https://www.lifelabs.com",
    "Referer": "https://www.lifelabs.com/"
}

def send_alert(message_body):
    msg = MIMEText(message_body)
    msg['Subject'] = "LifeLabs Alert"
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print(">> SMS Alert Sent Successfully")
    except Exception as e:
        print(f">> Failed to send SMS: {e}")

def check_for_appointments():
    # 1. Setup Timezone
    est = pytz.timezone('US/Eastern')
    now_est = datetime.now(est)
    
    # 2. Define Limits (Next 3 Days, After 10:30 AM)
    api_date_str = now_est.strftime("%Y-%m-%d")
    limit_date = now_est + timedelta(days=3)
    cutoff_time = dt_time(8, 30)
    
    print(f"Checking for slots between {api_date_str} and {limit_date.strftime('%Y-%m-%d')} (After 10:30 AM)")

    payload = {"site_id": SITE_IDS, "date": [api_date_str]}

    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            return

        data = response.json()
        matching_slots = []

        if not data.get('appointmentSlots'):
            print("No slots returned from API.")
            return

        for location_group in data['appointmentSlots']:
            site_id = location_group.get('siteId')
            
            for slot in location_group.get('slots', []):
                # Parse Time
                slot_dt = datetime.fromisoformat(slot['time'])
                
                # LOGIC FILTERS
                if now_est.date() <= slot_dt.date() <= limit_date.date():
                    if slot_dt.time() > cutoff_time:
                        
                        nice_format = slot_dt.strftime('%b-%d %I:%M %p')
                        matching_slots.append(f"Site {site_id}: {nice_format}")

        if matching_slots:
            # Send Alert (Limit to first 3 to save space)
            msg_body = "Slots Found:\n" + "\n".join(matching_slots[:3])
            send_alert(msg_body)
        else:
            print("No matching slots found.")

    except Exception as e:
        print(f"Script Error: {e}")

if __name__ == "__main__":
    check_for_appointments()
