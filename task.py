import json
from urllib import parse, request
from langdetect import detect
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QFileDialog
)

from PySide6.QtCore import QByteArray, QBuffer
from PySide6.QtGui import QMovie
import sys

f = open("./config.json", "r")
config = json.loads(f.read())
f.close()

API_KEY = config["API_KEY"]


url_search = "http://api.giphy.com/v1/gifs/search"
url_trend = "http://api.giphy.com/v1/gifs/trending"

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle("Gif search engines")

        page_layout = QVBoxLayout()
        gifs_layout = QHBoxLayout()
        search_button_layout = QHBoxLayout()
        control_button_layout = QHBoxLayout()
        search_layout = QHBoxLayout()
        save_layout = QHBoxLayout()

        page_layout.addLayout(search_layout)
        page_layout.addLayout(search_button_layout)
        page_layout.addLayout(control_button_layout)
        page_layout.addLayout(gifs_layout)
        page_layout.addLayout(save_layout)

        button_search = QPushButton("search!")
        button_search.pressed.connect(self.make_search)
        search_button_layout.addWidget(button_search)

        button_prev = QPushButton("previous")
        button_prev.pressed.connect(self.prev)
        control_button_layout.addWidget(button_prev)

        button_next = QPushButton("next")
        button_next.pressed.connect(self.next)
        control_button_layout.addWidget(button_next)

        button_save_first = QPushButton("save")
        button_save_first.pressed.connect(lambda: self.save(0))
        save_layout.addWidget(button_save_first)

        button_save_second = QPushButton("save")
        button_save_second.pressed.connect(lambda: self.save(1))
        save_layout.addWidget(button_save_second)


        search_input = QLineEdit()
        search_input.setPlaceholderText('input gif description')
        search_layout.addWidget(search_input)

        self.labels = [QLabel(), QLabel()]

        for i in range(2):
            self.labels[i].setFixedSize(480, 480)
            gifs_layout.addWidget(self.labels[i])

        self.stores = [[], []]
        self.previous_stores = [[], []]
        self.offset = 0
        self.limit = 1000
        self.isSearch = False

        self.trend_and_set()

        self.search_input = search_input
        self.button_prev = button_prev
        self.button_next = button_next

        widget = QWidget()
        widget.setLayout(page_layout)
        self.setCentralWidget(widget)

    def search(self):
        search_string = self.search_input.text()
        lang = detect(search_string)
        return self.make_request(parse.urlencode({
            "q": search_string,
            "api_key": API_KEY,
            "limit": "2",
            "offset": str(self.offset),
            "lang": lang
        }), url_search)
    

    def save(self, index):
        if(self.stores[index] == []):
            return
        file_name = QFileDialog.getSaveFileName(self, "Save file", "", "Gif (*.gif)")[0]
        if(file_name == ""):
            return
        with open(file_name, "wb") as file:
            file.write(self.stores[index][0].data())
    

    def prev(self):
        if(self.offset == 0):
            return
        self.button_prev.setEnabled(False)
        self.offset -= 2
        if(self.isSearch):
            self.make_search()
        else:
            self.trend_and_set()
        self.button_prev.setEnabled(True)

    def next(self):
        self.button_next.setEnabled(False)
        self.offset += 2
        if(self.offset >= self.limit):
            self.offset = 0
        if(self.isSearch):
            self.make_search()
        else:
            self.trend_and_set()
        self.button_next.setEnabled(True)

    
    def make_search(self):
        self.isSearch = True
        try:
            searchRes = self.search()
        except Exception as e:
            self.labels[0].setText("Error")
            self.labels[1].setText("Error")
            print(e)
            return
        self.limit = searchRes["pagination"]["total_count"]
        if(self.limit == 0):
            self.labels[0].setText("No results")
            self.labels[1].setText("No results")
            return
        for i in range(2):
            url = searchRes["data"][i]["images"]["downsized_medium"]["url"]
            self.download_movie(url, i)
            self.launch_movie(i)

    def trend(self):
        return self.make_request(parse.urlencode({
            "api_key": API_KEY,
            "limit": "2",
            "offset": str(self.offset)
        }), url_trend)
    
    def make_request(self, params, url):
        with request.urlopen("".join((url, "?", params))) as response:
            data = json.loads(response.read())
        return data
    
    def download_movie(self, url, index):
        with request.urlopen(url) as response:
            responseData = response.read()
        b_array = QByteArray(responseData)
        buffer = QBuffer(b_array)
        buffer.open(QBuffer.ReadOnly)
        if(self.stores[index] != []):
            self.previous_stores[index] = [self.stores[index][0], self.stores[index][1]]
        self.stores[index] = [b_array, buffer]

    def launch_movie(self, index):
        movie = QMovie()
        movie.setScaledSize(self.labels[index].size())
        movie.setDevice(self.stores[index][1])
        movie.setCacheMode(QMovie.CacheAll)
        self.labels[index].setMovie(movie)
        movie.start()

    def trend_and_set(self):
        try:
            trends = self.trend()
        except Exception as e:
            self.labels[0].setText("Error")
            self.labels[1].setText("Error")
            print(e)
            return
        self.limit = trends["pagination"]["total_count"]
        for i in range(2):
            url = trends["data"][i]["images"]["downsized_medium"]["url"]
            self.download_movie(url, i)
            self.launch_movie(i)

try:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
except Exception as e:
    print(e)
