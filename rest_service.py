import itertools
from flask import Flask, url_for, request
import os
import json
import logging
from PIL import Image
from io import BytesIO
import classify_image
from collections import OrderedDict
from operator import itemgetter
import time

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('imageClassifyService.log', 'w', 'UTF-8')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s-%(levelname)s(%(module)s:%(lineno)d)  %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)

UPLOAD_FOLDER = '/opt/imageClassifier/temp'
application = Flask(__name__)
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# uncomment this to download and extract inception model
# classify_image.maybe_download_and_extract()
classify_image.create_graph()


# to check service is up..
# url: get request => http://ip:port/

# url: post request => http://ip:port/
# include image in form-data as the value and and key as 'file'
# include key value pair (variation => integer between 1-100) in form-data (optional)
# include key value pair (numPredictions => integer) in form-data (optional)
@application.route('/', methods=['GET', 'POST'])
def index():
    start_time = time.time()
    num_predictions = 5
    try:
        if request.method == 'POST':

            # logging.debug('Headers: %s', request.headers)
            # logging.debug('Body: %s', request.get_data())

            if 'file' in request.files:
                file = request.files['file']
                image = Image.open(BytesIO(file.read()))
                saving_path = os.path.join(application.config['UPLOAD_FOLDER'], "_" + file.filename)
                image.save(saving_path, "JPEG")
                image_size = str(os.stat(saving_path).st_size)
                logging.info(file.filename + ' is ' + image_size + 'bytes')

                if 'numPredictions' in request.form:
                    logging.debug('numPredictions: %s', request.form['numPredictions'])
                    try:
                        num_predictions = int(request.form['numPredictions'])
                    except ValueError:
                        return json.dumps({"error": "numPredictions parameter is not an integer."}), 400

                result = classify_image.classify(saving_path, num_predictions + 5)
                min_weight = 0

                if 'variation' in request.form:
                    logging.debug('variation: %s', request.form['variation'])
                    try:
                        variation = int(request.form['variation'])
                        if 100 >= variation > 0:
                            max_weight = max(result.values())
                            gap_ = max_weight * (variation/100)
                            min_weight = max_weight - gap_
                        temp = {k: result[k] for k in result if result[k] >= min_weight}
                        result = temp
                    except ValueError:
                        return json.dumps({"error": "weightGap parameter have to be an integer between 1-100."}), 400

                ordered_results = OrderedDict(sorted(result.items(), key=itemgetter(1), reverse=True))

                if len(ordered_results) > num_predictions:
                    temp = OrderedDict(itertools.islice(ordered_results.items(), num_predictions))
                    ordered_results = temp

                os.remove(saving_path)
                logging.info({'tags': ordered_results})
                process_time = (time.time() - start_time)*1000
                return json.dumps(
                    {'tags': ordered_results,
                     'time': process_time,
                     'size': image_size,
                     'image': file.filename}
                )
            else:
                return json.dumps({"error": "file parameter is not in the request."}), 400
        else:
            return json.dumps({"status": "ok"})

    except Exception as e:
        logging.error("error: " + str(e))
        return json.dumps({"error": str(e)}), 500


if __name__ == '__main__':
    application.run(threaded=True)
