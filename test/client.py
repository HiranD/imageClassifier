import requests
import json
import os
from operator import itemgetter

directory_path = os.path.dirname(__file__)
image_loc = os.path.abspath(os.path.join(directory_path, "resources/"))
log_file = os.path.abspath(os.path.join(directory_path, "results.csv"))

url = 'http://localhost:8081/'
file = open(os.path.join(os.getcwd(), log_file), "w")

for filename in sorted(os.listdir(image_loc)):
    image_ = os.path.join(image_loc, filename)
    data = {
        'numPredictions': '5',
        'forBookCovers': 'True'
    }
    files = {
        'json': (None, json.dumps(data), 'application/json'),
        'file': (os.path.basename(image_), open(image_, 'rb'), 'application/octet-stream')
    }
    r = requests.post(url, files=files)

    json_data = json.loads(r.text)
    print(json_data['image'])
    file.write(json_data['image']+"\n")
    json_data = sorted(json_data['tags'].items(), key=itemgetter(1), reverse=True)
    i = 1
    for s in json_data:
        if i <= 5:
            n = s[0] + ';' + str(s[1])
            file.write(n + "\n")
            i += 1
    file.write("\n")

file.close()



