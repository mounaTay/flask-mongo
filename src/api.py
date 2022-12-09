from flask import Flask, request, jsonify, render_template
from utils import *
import codecs

app = Flask(__name__, template_folder='templates')


@app.route('/')
def index():
    return '<h1>Welcome</h1>' \
           '<ul>' \
           '<li><a href=/persons>list all persons</a></li>' \
           '<li><a href=/generate>generate a random person</a></li>' \
           '<li>use /persons?id=`id` to get a person by id</p></li>' \
           '</ul>'


@app.route('/persons', methods=['GET'])
def get_data():
    """
    read records from mongodb and construct a html template with images and jsons from mongo documents
    :return: renders html template or json string when having no records
    """
    objects = list(person_details.read("person", request.args.get('id')))
    documents = []
    if len(objects) == 0:
        return jsonify({'result': 'No persons found'}), 201
    for obj in objects:
        image = person_details.fs.get(obj['image'])
        base64_data = codecs.encode(image.read(), 'base64')
        image = base64_data.decode('utf-8')
        del obj["image"]
        documents.append((image, obj))
    return render_template('index.html', objects=documents)


@app.route('/generate')
def generate():
    """
    generates a random person
    :return: json string with success or failure
    """
    status = person_details()
    if status:
        return jsonify({'result': 'Person generated successfully'}), 201
    return jsonify({'result': 'Error occurred during generation'}), 500


# instantiate PersonDetails once to be used every time the get_data/generate functions are called
person_details = PersonDetails()
if __name__ == "__main__":
    app.run()
