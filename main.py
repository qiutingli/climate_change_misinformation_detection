import json
import pandas as pd
import numpy as np
import nltk
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
from nltk.corpus import wordnet
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import defaultdict
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GridSearchCV
from sklearn import svm
from sklearn.neighbors import NearestNeighbors
from sklearn.neighbors import KNeighborsClassifier
import keras
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout, Conv1D, MaxPooling1D, Flatten
from keras.optimizers import Adam, SGD, rmsprop
from keras.preprocessing.text import Tokenizer
from keras.layers import Embedding
from keras.preprocessing.sequence import pad_sequences


class dataLoader():

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=50000)

    def view_dataset(self, file_name):
        with open('{}.json'.format(file_name)) as file:
            data_json = json.load(file)
            for key in data_json.keys():
                print('Key in json: ', key)
                print('Value:', data_json[key]['label'])
                break
            print('File length:', len(data_json.keys()))

    def create_corpus(self):
        corpus = []
        with open('train.json') as file:
            data_json = json.load(file)
            for key in data_json.keys():
                corpus.append(data_json[key]['text'])
        with open('train-external.json') as file:
            data_json = json.load(file)
            for key in data_json.keys():
                corpus.append(data_json[key]['text'])
        return corpus

    def vectorize_text_glove(self, tokenized_text):
        preprocessed_tokens = tokenized_text
        word_vectors = []
        for token in preprocessed_tokens:
            try:
                word_vectors.append(vec_dict[token])
            except:
                word_vectors.append([0]*200)  # TODO: 300
        return word_vectors

    def get_X_train_glove(self):
        train_docs = self.create_corpus()
        preprocessor = DataPreprocessor()
        tokenized_texts = preprocessor.preprocess_data(train_docs)
        X_train = []
        for tokenized_text in tokenized_texts:
            word_vectors = self.vectorize_text_glove(tokenized_text)
            text_vector = np.sum(word_vectors, 0)
            X_train.append(text_vector)
        return np.array(X_train)

    def get_X_train(self):
        corpus = self.create_corpus()
        X_train = self.vectorizer.fit_transform(corpus)
        print('X_train shape: ', X_train.shape)
        return X_train

    def get_y_train(self):
        y_train = []
        with open('train.json') as file:
            data_json = json.load(file)
            for key in data_json.keys():
                y_train.append(data_json[key]['label'])
        with open('train-external.json') as file:
            data_json = json.load(file)
            for key in data_json.keys():
                y_train.append(data_json[key]['label'])
        return y_train

    def get_X_dev(self):
        dev_docs = []
        with open('dev.json') as file:
            data_json = json.load(file)
            for key in data_json.keys():
                dev_docs.append(data_json[key]['text'])
        return self.vectorizer.transform(dev_docs)

    def get_y_dev(self):
        y_dev = []
        with open('dev.json') as file:
            data_json = json.load(file)
            for key in data_json.keys():
                y_dev.append(data_json[key]['label'])
        return y_dev

    def get_X_test_glove(self):
        test_docs = []
        with open('test-unlabelled.json') as file:
            data_json = json.load(file)
            for key in data_json.keys():
                test_docs.append(data_json[key]['text'])
        preprocessor = DataPreprocessor()
        tokenized_texts = preprocessor.preprocess_data(test_docs)
        X_test = []
        for tokenized_text in tokenized_texts:
            word_vectors = self.vectorize_text_glove(tokenized_text)
            text_vector = np.sum(word_vectors, 0)
            X_test.append(text_vector)
        return np.array(X_test)

    def get_X_test(self):
        test_docs = []
        with open('test-unlabelled.json') as file:
            data_json = json.load(file)
            for key in data_json.keys():
                test_docs.append(data_json[key]['text'])
        return self.vectorizer.transform(test_docs)


class DataPreprocessor():

    def __init__(self):
        pass

    def get_wordnet_pos(self, word):
        # POS tag the word
        tag = nltk.pos_tag([word])[0][1][0].upper()
        tag_dict = {"J": wordnet.ADJ,
                    "N": wordnet.NOUN,
                    "V": wordnet.VERB,
                    "R": wordnet.ADV}
        return tag_dict.get(tag, wordnet.NOUN)

    def lemmatize(self, word):
        lemmatizer = nltk.stem.wordnet.WordNetLemmatizer()
        lemma = lemmatizer.lemmatize(word, self.get_wordnet_pos(word))
        return lemma

    def preprocess_data(self, corpus):
        preprocessed_data = []
        english_stopwords = set(stopwords.words('english'))
        for doc in corpus:
            tokenized_doc = TweetTokenizer().tokenize(doc)
            filtered_doc = [word for word in tokenized_doc if not word in english_stopwords]
            # lemmatized_doc = [lemmatize(word) for word in filtered_doc]
            preprocessed_data.append(filtered_doc)
        return preprocessed_data


class ClassicModelBuilder():

    def __init__(self):
        pass

    def process_naive_bayes(self, X_train, y_train, X_test):
        nb = MultinomialNB()
        nb.fit(X_train, y_train)
        y_pred = nb.predict(X_test)
        # nb_param_grid = {'alpha': np.arange(0.1, 1.1, 0.1)}
        # nb_search = GridSearchCV(nb, param_grid=nb_param_grid, scoring='recall')
        # nb_search.fit(X_train, y_train)
        # y_pred = nb_search.predict(X_test)
        return y_pred

    def process_kmeans(self):
        X = []
        kmeans = KMeans(n_clusters=1)
        kmeans.fit(X)
        distances = kmeans.transform(X)
        sorted_idx = np.argsort(distances.ravel())[::-1][:5]

    def process_one_class_svm(self, X_train, y_train, X_test):
        clf = svm.OneClassSVM()
        clf.fit(X_train)
        y_test_pred = clf.predict(X_test)
        return y_test_pred

    def process_knn(self, X_train, y_train, X_test):
        # nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(X_train)
        knn_clf = KNeighborsClassifier(n_neighbors=3)
        knn_clf.fit(X_train, y_train)
        return knn_clf.predict(X_test)


class textCNN():

    def __init__(self):
        pass

    def process_CNN_embedding_layer(self):
        pass

    def process_CNN_vector_mean(self, X_train, y_train, X_test):
        num_classes = 1
        verbose, epochs, batch_size = 0, 30, 32
        print('Building model...')
        model = Sequential()
        model.add(Conv1D(filters=64, kernel_size=3, padding='causal', activation='relu', input_shape=(None, 200)))
        model.add(Dropout(0.5))
        model.add(MaxPooling1D(pool_size=2))
        # model.add(Flatten())
        model.add(Dense(256, activation='relu', input_dim=200))
        model.add(Dense(num_classes, activation='softmax'))
        model.compile(optimizer='adam',
                      loss='binary_crossentropy',
                      metrics=['accuracy'])
        print("Fitting model... ")
        model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size)
        score = model.evaluate(X_train, y_train, batch_size=32)
        print(score)
        y_test_pred = model.predict_classes(X_test)
        print('prediction: ', y_test_pred)
        return y_test_pred


def generate_dev_output(y_dev):
    with open('dev-baseline-r.json') as file:
        data_json = json.load(file)
        for index, key in enumerate(data_json.keys()):
            data_json[key]['label'] = int(y_dev[index])
    with open('dev-baseline-r.json', 'w') as file:
        json.dump(data_json, file)
    print('Development output generated')


def generate_output(y_test):
    with open('test-output.json') as file:
        data_json = json.load(file)
        for index, key in enumerate(data_json.keys()):
            data_json[key]['label'] = int(y_test[index])
    with open('test-output.json', 'w') as file:
        json.dump(data_json, file)
    print('Output generated')


def load_glove_vec_dict():
    print('Loading Glove pre-trained word vectors ...')
    vec_dict = {}
    with open('glove.twitter.27B.200d.txt', 'r', encoding='UTF-8') as glove_file:
        for line in glove_file:
            try:
                split_line = line.split()
                word = split_line[0]
                embedding = np.array([float(val) for val in split_line[1:]])
                vec_dict[word] = embedding
            except:
                pass
    print('{} Glove word vectors loaded.'.format(len(vec_dict)))
    return vec_dict


if __name__ == '__main__':
    data_loader = dataLoader()
    dev_docs = []
    with open('dev.json') as file:
        data_json = json.load(file)
        for key in data_json.keys():
            dev_docs.append(data_json[key]['text'])
    docs = dev_docs  # TODO: Change back
    # docs = data_loader.create_corpus()
    # define class labels

    y_train = data_loader.get_y_dev()  # TODO: Change back
    # y_train = data_loader.get_y_train()
    print(y_train)
    # IMPORTANT
    y_train = keras.utils.to_categorical(y_train, num_classes=2)
    print(y_train)
    # prepare tokenizer
    t = Tokenizer()
    t.fit_on_texts(docs)
    vocab_size = len(t.word_index) + 1
    # integer encode the documents
    encoded_docs = t.texts_to_sequences(docs)
    print(encoded_docs)
    # pad documents to a max length of 100 words
    max_length = 100
    X_train = pad_sequences(encoded_docs, maxlen=max_length, padding='post')
    print(X_train)

    vec_dict = load_glove_vec_dict()
    glove_vec_dim = 200
    # create a weight matrix for words in training docs
    embedding_matrix = np.zeros((vocab_size, glove_vec_dim))
    for word, i in t.word_index.items():
        embedding_vector = vec_dict.get(word)
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector
    print('Building model...')
    model = Sequential()
    e = Embedding(vocab_size, glove_vec_dim, weights=[embedding_matrix], input_length=max_length, trainable=False)
    model.add(e)
    model.add(Conv1D(filters=64, kernel_size=2, padding='valid', activation='relu'))
    model.add(Dropout(0.2))
    model.add(MaxPooling1D(pool_size=2))
    model.add(Flatten())
    model.add(Dense(256, activation='relu'))
    model.add(Dense(2, activation='softmax'))
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    print(model.summary())
    # fit the model
    print("Fitting model... ")
    model.fit(X_train, y_train, epochs=10, batch_size=32)
    # evaluate the model
    loss, accuracy = model.evaluate(X_train, y_train, verbose=0)
    print('Accuracy: %f' % (accuracy * 100))
    test_docs = []
    with open('test-unlabelled.json') as file:
        data_json = json.load(file)
        for key in data_json.keys():
            test_docs.append(data_json[key]['text'])
    encoded_test_docs = t.texts_to_sequences(test_docs)
    X_test = pad_sequences(encoded_test_docs, maxlen=max_length, padding='post')
    y_test_pred = model.predict_classes(X_test)
    print('predictions: ', y_test_pred)
    generate_output(y_test_pred)

    dev_docs = []
    with open('dev.json') as file:
        data_json = json.load(file)
        for key in data_json.keys():
            dev_docs.append(data_json[key]['text'])
    encoded_dev_docs = t.texts_to_sequences(test_docs)
    X_dev = pad_sequences(encoded_dev_docs, maxlen=max_length, padding='post')
    y_dev_pred = model.predict_classes(X_dev)
    generate_dev_output(y_dev_pred)


    # X_train = data_loader.get_X_train_glove()
    # y_train = data_loader.get_y_train()
    # # X_dev = data_loader.get_X_dev()
    # # y_dev = data_loader.get_y_dev()
    # X_test = data_loader.get_X_test_glove()
    # print(X_train.shape, y_train.shape, X_test.shape)
    # text_cnn = textCNN()
    # y_test_pred = text_cnn.process_CNN_vector_mean(X_train, y_train, X_test)
    # generate_output(y_test_pred)

    # model_builder = classicModelBuilder()
    # y_dev_pred = model_builder.process_naive_bayes(X_train, y_train, X_dev)
    # print('Naive Bayes accuracy on development set: ', accuracy_score(y_dev, y_dev_pred))
    # X_test = data_loader.get_X_test()
    # y_test_pred = model_builder.process_naive_bayes(X_train, y_train, X_test)
    # count = 0
    # for y in y_test_pred:
    #     if y == 0:
    #         count += 1
    # print(count)
    # generate_output(y_test_pred)

    # preprocessed_data = preprocess_data(corpus)
    # print(preprocessed_data[0])
    # vectorized_data = vectorize_docs(preprocessed_data, 1)
    # print(vectorized_data)
    # vectorizer = CountVectorizer()
    # X = vectorizer.fit_transform(corpus)