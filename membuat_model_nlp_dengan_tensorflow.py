# -*- coding: utf-8 -*-
"""Membuat Model NLP dengan TensorFlow

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WH9NMSIpqL-cnE8r1YIe6sHHVj2HBDyV
"""

# install kaggle package
!pip install -q kaggle

# upload kaggle.json
from google.colab import files
files.upload()

# create directory and change file permissions
!mkdir -p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json
!ls ~/.kaggle

# download dataset
!kaggle datasets download -d hgultekin/bbcnewsarchive

# unzip and see the list of datasets
!mkdir bbcnewsarchive
!unzip bbcnewsarchive.zip -d bbcnewsarchive
!ls bbcnewsarchive

"""##Load dataset"""

#import library
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize,sent_tokenize
from bs4 import BeautifulSoup
import re,string,unicodedata
from sklearn.metrics import classification_report,confusion_matrix,accuracy_score
from sklearn.model_selection import train_test_split
from string import punctuation
from nltk import pos_tag
from nltk.corpus import wordnet
import keras
from keras.preprocessing import text, sequence
import nltk
nltk.download('stopwords')

#import data to variables for reading
news_data = pd.read_csv('bbcnewsarchive/bbc-news-data.csv', sep='\t')
news_data.head(10)

# total data
news_data.shape

# Check if there is a Null value
news_data.isnull().sum()

news_data.info()

# categories
news_data.category.value_counts()

# delete unused columns
news_data = news_data.drop(columns=['filename'])
news_data

#count the number of titles
news_data.title.count()

# combine column title and content
news_data['text'] = news_data['title'] + " " + news_data['content']
news_data

"""## Data Cleaning"""

stwd = set(stopwords.words('english'))
punctuation = list(string.punctuation)
stwd.update(punctuation)

nltk.download('stopwords')
stwd = set(stopwords.words("english"))

def strip_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()

def remove_between_square_brackets(text):
    return re.sub(r'\[[^]]*\]', '', text)

def remove_url(text):
    return re.sub(r'http\S+', '', text)

def remove_stopwords(text):
    words = text.split()
    filtered_words = [word for word in words if word.strip().lower() not in stwd]
    return " ".join(filtered_words)

def denoise_text(text):
    text = strip_html(text)
    text = remove_between_square_brackets(text)
    text = remove_url(text)
    text = remove_stopwords(text)
    return text

news_data['text'] = news_data['text'].apply(denoise_text)

"""## Jumlah kata"""

def get_corpus(text):
    words = [word.strip() for i in text for word in i.split()]
    return words
corpus = get_corpus(news_data['text'])
corpus[:10]

from collections import Counter
counter = Counter(corpus)
most_common = dict(counter.most_common(10))
most_common

from sklearn.feature_extraction.text import CountVectorizer
def get_top_text_ngrams(corpus, n, g):
    vectorizer = CountVectorizer(ngram_range=(g, g))
    vectorizer.fit(corpus)
    bag_of_words = vectorizer.transform(corpus)
    word_sum = bag_of_words.sum(axis=0)
    word_freq = [(word, word_sum[0, idx]) for word, idx in vectorizer.vocabulary_.items()]
    word_freq = sorted(word_freq, key=lambda x: x[1], reverse=True)
    return word_freq[:n]
top_ngrams = get_top_text_ngrams(corpus, n=10, g=2)
top_ngrams

plt.figure(figsize = (16,9))
most_common = get_top_text_ngrams(news_data.text,10,1)
most_common = dict(most_common)
sns.barplot(x=list(most_common.values()),y=list(most_common.keys()))

"""## Encoding & Splitting Data"""

# data category one-hot-encoding
category = pd.get_dummies(news_data.category)
new_cat = pd.concat([news_data, category], axis=1)
new_cat = new_cat.drop(columns='category')
new_cat.head(10)

# change dataframe value to numpy array
news = new_cat['text'].values
label = new_cat[['business', 'entertainment', 'politics', 'sport', 'tech']].values
news

#cek label
label

x_train,x_test,y_train,y_test = train_test_split(news, label,test_size = 0.2,shuffle=True)

"""##Tokenizer dan Pemodelan Sequential dengan Embedding dan LSTM"""

import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.layers import LSTM,Dense,Embedding,Dropout
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam

vocab_size = 10000
max_len = 200
trunc_type = "post"
oov_tok = "<OOV>"

tokenizer = Tokenizer(num_words=vocab_size, oov_token=oov_tok)
tokenizer.fit_on_texts(x_train)

word_index = tokenizer.word_index

sequences_train = tokenizer.texts_to_sequences(x_train)
sequences_test = tokenizer.texts_to_sequences(x_test)

pad_train = pad_sequences(sequences_train, maxlen=max_len, truncating=trunc_type)
pad_test = pad_sequences(sequences_test, maxlen=max_len, truncating=trunc_type)

print("Shape of pad_test:", pad_test.shape)
print ("Pad Train :", pad_train)
print ("Pad Test :", pad_test)

model = tf.keras.Sequential([
    tf.keras.layers.Embedding(input_dim=vocab_size, output_dim=64, input_length=max_len),
    tf.keras.layers.LSTM(128),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(5, activation='softmax')
])

model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
model.summary()

# callback
class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('accuracy')>0.93 and logs.get('val_accuracy')>0.93):
      self.model.stop_training = True
      print("\n akurasi dari training set and the validation set telah terpenuhi > 93%!")
callbacks = myCallback()

num_epochs = 50
history = model.fit(pad_train, y_train, epochs=num_epochs,
                    validation_data=(pad_test, y_test), verbose=2, callbacks=[callbacks])

# plot of accuracy
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Model Accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

# plot of loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()