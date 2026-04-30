import random
import csv
from datetime import datetime, timedelta

# Config
num_records = 50
base_time = datetime(2024, 4, 1, 8, 0, 0)

users = [f"user{i}" for i in range(1, num_records + 1)]

def random_ip():
    return f"192.168.1.{random.randint(1, 255)}"

def random_status():
    return random.choice(["success", "failed"])

def random_time(start_time, index):
    return start_time + timedelta(minutes=index * random.randint(1, 5))

# Generate data
data = []
for i in range(num_records):
    row = [
        users[i],
        random_ip(),
        random_time(base_time, i).strftime("%Y-%m-%d %H:%M:%S"),
        random_status()
    ]
    data.append(row)

# Write to CSV
with open("login_logs.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["username", "ip_address", "login_time", "status"])
    writer.writerows(data)

print("CSV file 'login_logs.csv' generated successfully.")