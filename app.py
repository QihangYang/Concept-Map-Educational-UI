# -*- coding: utf-8 -*-
import os
import time
import hashlib
import requests

from flask import Flask, render_template, redirect, url_for, request, render_template_string
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

import numpy as np
import pandas as pd
from PIL import Image
import pytesseract as pt
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


### System

# Load concepts list
excel = pd.read_excel("data/linear_regression.xlsx")
Concepts_list = []

for col in excel.columns:
    for row in range(len(excel)):
        if str(excel[col][row]) != "nan":
            Concepts_list.append(excel[col][row]) 

Concepts_list = list(set(Concepts_list))


# Match question with concepts list
def match(ques, Concepts_list):
    tags = []
    for i in range(len(Concepts_list)):
        if (bool(re.search(Concepts_list[i], ques, re.IGNORECASE)) 
            | fuzz.partial_ratio(Concepts_list[i], ques) > 85):
            tags.append(Concepts_list[i])
    return(tags)




### Flask

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'I have a dream'
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir, 'uploads') # you'll need to create a folder named uploads

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB


class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, 'Image Only!'), FileRequired('Choose a file!')])
    submit = SubmitField('Upload')


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    files_list = os.listdir(app.config['UPLOADED_PHOTOS_DEST'])
    ques_name = "New_Question_" + str(len(files_list) + 1)
    if form.validate_on_submit():
        for filename in request.files.getlist('photo'):
            photos.save(filename, name=ques_name + '.')
        success = True
    else:
        success = False
    return render_template('index.html', form=form, success=success, ques_name=ques_name)




# @app.route('/', methods=['GET', 'POST'])
# def upload_file():
#     form = UploadForm()
#     if form.validate_on_submit():
#         for filename in request.files.getlist('photo'):
#             str_name='admin' + str(int(time.time()))
#             name = hashlib.md5(str_name.encode("utf-8")).hexdigest()[:15]
#             photos.save(filename, name=name + '.')
#         success = True
#     else:
#         success = False
#     return render_template('index.html', form=form, success=success)


@app.route('/manage')
def manage_file():
    files_list = os.listdir(app.config['UPLOADED_PHOTOS_DEST'])
    return render_template('manage.html', files_list=files_list)


@app.route('/open/<filename>')
def open_file(filename):
    file_url = photos.url(filename)
    quesID = str(filename)[:-4]
    img = photos.path(filename)
    ques_text = pt.image_to_string(img)
    tags = match(ques_text, Concepts_list)
    return render_template('browser.html', file_url = file_url, quesID = quesID, ques_text = ques_text, tags = tags)


@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = photos.path(filename)
    os.remove(file_path)
    return redirect(url_for('manage_file'))


if __name__ == '__main__':
    app.run(debug=True)