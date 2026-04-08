import os, json
from datetime import datetime
from agent.common import pdf_reader

pdf_path = 'C:/Users/Admin/Downloads/Browcher/Gulfood Brochures'
list_dir = os.listdir(pdf_path)
a = 0
for each in list_dir:
    # Use os.path.join() to properly combine paths
    full_path = os.path.join(pdf_path, each)

    if '.pdf' in each:
        print(f"Processing PDF: {full_path}")
        pdf_to_json = pdf_reader.pdf_to_json(full_path)  # Pass the full path
        print(pdf_to_json)
        #print(json.dumps(pdf_to_json, indent=4))

    if a == 10:
        break
    a+=1
