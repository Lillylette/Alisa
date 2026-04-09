from flask import Flask, request, jsonify
import logging
import re

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
sessionStorage = {}

@app.route("/", methods=["GET"])
def health_check():
    return "OK", 200

@app.route("/post", methods=["POST"])
def main():
    logging.info(f"Request: {request.json!r}")
    response = {
        "session": request.json["session"],
        "version": request.json["version"],
        "response": {"end_session": False},
    }

    handle_dialog(request.json, response)

    logging.info(f"Response:  {response!r}")

    return jsonify(response)

def is_agreement(text):
    text_lower = text.lower()
    
    exact_matches = [
        "ладно",
        "куплю",
        "покупаю",
        "хорошо",
        "да",
        "согласен",
        "ok",
    ]
    
    if text_lower in exact_matches:
        return True
    
    if re.match(r'^я\s+(куплю|покупаю)$', text_lower):
        return True
    
    return False

def handle_dialog(req, res):
    user_id = req["session"]["user_id"]

    if req["session"]["new"]:
        sessionStorage[user_id] = {
            "suggests": [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ],
            "animal": "слона"
        }
        res["response"]["text"] = "Привет! Купи слона!"
        res["response"]["buttons"] = get_suggests(user_id)
        return

    if is_agreement(req["request"]["original_utterance"]):
        current_animal = sessionStorage[user_id].get("animal", "слона")
        
        if current_animal == "слона":
            sessionStorage[user_id]["animal"] = "кролика"
            sessionStorage[user_id]["suggests"] = [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ]
            res["response"]["text"] = "Отлично! А теперь купи кролика!"
            res["response"]["buttons"] = get_suggests(user_id)
        else:
            res["response"]["text"] = "Спасибо за покупки! Заходите ещё!"
            res["response"]["end_session"] = True
        return

    res["response"]["text"] = f"Все говорят '{req['request']['original_utterance']}', а ты купи {sessionStorage[user_id].get('animal', 'слона')}!"
    res["response"]["buttons"] = get_suggests(user_id)

def get_suggests(user_id):
    session = sessionStorage[user_id]

    suggests = [{"title": suggest, "hide": True} for suggest in session["suggests"][:2]]

    session["suggests"] = session["suggests"][1:]
    sessionStorage[user_id] = session

    if len(suggests) < 2:
        suggests.append(
            {
                "title": "Ладно",
                "url": "https://market.yandex.ru/search?text=слон",
                "hide": True,
            }
        )

    return suggests

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
