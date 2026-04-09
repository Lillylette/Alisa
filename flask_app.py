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
            "stage": "elephant"
        }
        res["response"]["text"] = "Привет! Купи слона!"
        res["response"]["buttons"] = get_suggests(user_id)
        return

    if is_agreement(req["request"]["original_utterance"]):
        stage = sessionStorage[user_id].get("stage", "elephant")
        
        if stage == "elephant":
            sessionStorage[user_id]["stage"] = "rabbit"
            sessionStorage[user_id]["suggests"] = [
                "Не хочу.",
                "Не буду.",
                "Отстань!",
            ]
            res["response"]["text"] = "Отлично! А теперь купи кролика!"
            res["response"]["buttons"] = get_suggests(user_id)
            return
        elif stage == "rabbit":
            res["response"]["text"] = "Кролика можно купить на Яндекс маркете!"
            res["response"]["end_session"] = True
            return

    animal = "слона" if sessionStorage[user_id].get("stage", "elephant") == "elephant" else "кролика"
    res["response"]["text"] = f"Все говорят '{req['request']['original_utterance']}', а ты купи {animal}!"
    res["response"]["buttons"] = get_suggests(user_id)

def get_suggests(user_id):
    session = sessionStorage[user_id]
    stage = session.get("stage", "elephant")
    search_text = "слон" if stage == "elephant" else "кролик"

    suggests = [{"title": suggest, "hide": True} for suggest in session["suggests"][:2]]

    session["suggests"] = session["suggests"][1:]
    sessionStorage[user_id] = session

    if len(suggests) < 2:
        suggests.append(
            {
                "title": "Ладно",
                "url": f"https://market.yandex.ru/search?text={search_text}",
                "hide": True,
            }
        )

    return suggests

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
