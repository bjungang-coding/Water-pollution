import sqlite3
from datetime import datetime

import pytz, shutil
from flask import Flask, jsonify, request
from flask_cors import CORS
from jsonly.client import UseJsonly
from jsonly.convert import Convert

app = Flask("app")
app.config["JSON_AS_ASCII"] = False
cors = CORS(app)


@app.route("/")
def home():
    return "Made as KimSuyun"


@app.route("/update/<tag>", methods=["GET", "POST"])
def update(tag):
    if tag == "webhook":
        url = request.args.get("url")
        jsonly = UseJsonly("webhook.json")
        print(request.headers)
        jsonly.update({"url" : url})
        res = jsonify({"result": "OK"})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res
        
    korea_tz = pytz.timezone("Asia/Seoul")
    now = datetime.now(korea_tz)
    hour = now.hour
    if hour < 12:
        meridian = "오전"
    else:
        meridian = "오후"
        if hour > 12:
            hour -= 12

    formatted_time = (
        f"{now.year}년 {now.month}월 {now.day}일 {meridian} {hour}:{now.minute}"
    )

    connect = sqlite3.connect("data.db")
    c = connect.cursor()
    c.execute(
        f"INSERT into '{tag}' values (?, ?)", (formatted_time, request.args.get("ppb"))
    )
    connect.commit()
    connect.close()
    res = jsonify({"result": "OK"})
    res.headers.add("Access-Control-Allow-Origin", "*")
    return res


@app.route("/get", methods=["GET"])
def get():
    table_name = request.args.get("table")

    jsonly = UseJsonly("webhook.json")
    cvt = Convert(jsonly, "data.db")
    data = cvt.to_dict(table_name=table_name)

    key = {"Fe": "철", "Pb": "납", "Cd": "카드뮴"}
    try:
        res = jsonify({
            "result": "OK", "data": {
              'title' : f'{key[table_name]}({table_name})',
              'liveConcentration' : data[-1]["ppb"],
              'lastupdate' : data[-1]["date"],
              'record' : data
            }
        })
    except IndexError:
        res = jsonify({
            "result": "OK", "data": {
              'title' : f'{key[table_name]}({table_name})',
              'liveConcentration' : 0,
              'lastupdate' : "없음",
              'record' : data
            }
        })
        
    res.headers.add("Access-Control-Allow-Origin", "*")
    return res


@app.route("/reset", methods=["GET"])
def reset():
    shutil.copy('data.db', 'backup.db')
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Fe")
    cursor.execute("DELETE FROM Pb")
    cursor.execute("DELETE FROM Cd")
    conn.commit()
    conn.close()
    res = jsonify({"result": "OK"})
    res.headers.add("Access-Control-Allow-Origin", "*")
    return res
    
    
app.run(host="0.0.0.0", port=80, debug=True)
