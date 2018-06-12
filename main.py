#!/usr/bin/python
# written by Danny Wagstaff 2/2018

from flask import Flask, render_template, request
#from . import contractBasketBeta # works with development server (127.0.0.1:5000)
import contractBasket # works in production (dwagstaff.com/bondapp2)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/', methods = ['POST'])
def index_post():
    # Can we rename these variables to follow Python conventions?
    FC = request.form['futCon'] # futures contract chosen
    FE = request.form['expiration'] # expiration month
    # Can we use an f-string here to improve readability?
    print('FC, FE=', FC, FE)
    listTsyData = contractBasket.Basket() # class Basket will hold UST securities list
    #listTsyData.getBasket(FC, FE)
    listTsyData.getBasket(FC, FE)
    return render_template('CTDList.html', listData=listTsyData.value, FC = FC,
        FE = FE, mat = listTsyData.getConAbbr(FC, FE))

if __name__ == "__main__":
    # Turn debugger on so the app automatically reloads when you edit a file
    app.run(debug=True)