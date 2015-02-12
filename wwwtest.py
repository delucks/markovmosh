from flask import Flask
from markovmosh import Markov
app = Flask(__name__)

@app.route("/")
def main():
    m = Markov(10,100)
    return m.go("random")

if __name__=="__main__":
    app.run()
