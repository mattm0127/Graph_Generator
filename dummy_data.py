import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Configuration
num_rows = 500
start_date = datetime(2025, 1, 1)

# 1. Generate Dates
# We create a list of dates, some repeating (multiple samples per day)
date_list = [start_date + timedelta(days=random.randint(0, 180)) for _ in range(num_rows)]
date_list.sort() # Sort them to look realistic

# 2. Generate Rooms (Categorical Data)
rooms = ['Filling Room', 'Gowning Room', 'Prep Area', 'Corridor A']
room_data = [random.choice(rooms) for _ in range(num_rows)]

# 3. Generate Values (Numerical Data)
# Random values between 0.0 and 100.0
high_data = np.round(np.random.uniform(80.0, 100.0, size=num_rows-400), 2)
low_data = np.round(np.random.uniform(0.0, 20.0, size=num_rows-100), 2)
value_data = low_data.tolist() + high_data.tolist()
final_data = []
for _  in range(500):
    final_data.append(random.choice(value_data))

# 4. Generate Status (Logic-based)
# Let's say anything over 80.0 is an "Action Level" (Fail), otherwise "Pass"
status_data = ['Fail' if v > 80 else 'Pass' for v in final_data]

# 5. Create DataFrame
df = pd.DataFrame({
    'Date': date_list,
    'Room': room_data,
    'Value': final_data,
    'Status': status_data
})

# 6. Save to Excel
output_file = "dummy_data.xlsx"
df.to_excel(output_file, index=False)

print(f"Success! '{output_file}' has been created with {num_rows} rows of data.")