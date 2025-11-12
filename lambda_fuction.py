import os
import json
import boto3
import uuid
import time

# ---------- Environment variables ----------
FAQ_TABLE = os.environ.get("FAQ_TABLE", "FAQTable")
QUERIES_TABLE = os.environ.get("QUERIES_TABLE", "UserQueries")
HUMAN_EMAIL = os.environ.get("HUMAN_EMAIL")
FROM_EMAIL = os.environ.get("FROM_EMAIL")

# ---------- AWS resources ----------
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
faq_table = dynamodb.Table(FAQ_TABLE)
queries_table = dynamodb.Table(QUERIES_TABLE)
ses = boto3.client("ses", region_name="us-east-1")


# ---------- Helper functions ----------

def tokenize(text):
    if not text:
        return set()
    text = text.lower()
    tokens = set([t.strip(".,?!\"'()[]{}:;") for t in text.split()])
    return {t for t in tokens if t}


def find_best_faq(user_text):
    tokens = tokenize(user_text)
    resp = faq_table.scan()
    items = resp.get("Items", [])
    best, best_score = None, 0
    for item in items:
        keywords = set(item.get("keywords", []))
        score = len(tokens.intersection(keywords))
        if score > best_score:
            best_score = score
            best = item
    return best, best_score


def store_query(query_text, matched_faq_id=None, match_score=0,
                sent_to_human=False, location=None, user_email=None):
    qid = str(uuid.uuid4())
    item = {
        "query_id": qid,
        "query_text": query_text,
        "timestamp": int(time.time()),
        "matched_faq_id": matched_faq_id or "",
        "match_score": match_score,
        "sent_to_human": sent_to_human
    }
    if location:
        item["location"] = location
    if user_email:
        item["user_email"] = user_email

    queries_table.put_item(Item=item)
    return qid


def send_fallback_email(query_text, query_id, user_email=None):
    subject = f"[CHATBOT] Unanswered query {query_id}"
    body = f"User asked: {query_text}\n\nQuery ID: {query_id}"
    if user_email:
        body += f"\nUser email: {user_email}"
    body += "\n\nPlease respond."

    try:
        print(f"Sending SES email from {FROM_EMAIL} to {HUMAN_EMAIL}")
        response = ses.send_email(
            Source=FROM_EMAIL,
            Destination={"ToAddresses": [HUMAN_EMAIL]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body}},
            },
        )
        print("SES response:", response)
    except Exception as e:
        print("SES send failed:", e)


# ---------- Main handler ----------

def lambda_handler(event, context):
    print("Event received:", json.dumps(event))

    # Extract user message
    user_text = event.get("inputTranscript") or event.get("message") or ""
    session_state = event.get("sessionState", {})
    intent = session_state.get("intent", {})
    slots = intent.get("slots", {}) or {}
    session_attrs = session_state.get("sessionAttributes", {}) or {}

    intent_name = intent.get("name", "FallbackIntent")

    location = None
    user_email = None

    # Get slot values if present
    if slots:
        if "LocationType" in slots and slots["LocationType"]:
            location = slots["LocationType"].get("value", {}).get("interpretedValue")
        if "UserEmail" in slots and slots["UserEmail"]:
            user_email = slots["UserEmail"].get("value", {}).get("interpretedValue")

    print("Slots received:", json.dumps(slots))
    print("Location interpreted:", location)
    print("User email extracted:", user_email)
    print("Intent name:", intent_name)

    # ---------- GreetingAndEmail Intent ----------
    # Capture user email and store it in session attributes
    if intent_name == "GreetingAndEmail" and user_email:
        session_attrs["UserEmail"] = user_email
        print("Stored user email in session attributes:", user_email)
        return {
            "sessionState": {
                "sessionAttributes": session_attrs,
                "dialogAction": {"type": "Close"},
                "intent": {"name": intent_name, "state": "Fulfilled"},
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": f"Thanks, {user_email}! How can I help you today?",
                }
            ],
        }

    # ---------- For all other intents (PasswordReset, WiFiIssue, Fallback, etc.) ----------

    # Retrieve stored email from session attributes if not in slot
    if not user_email:
        user_email = session_attrs.get("UserEmail")
        print("Retrieved user email from session attributes:", user_email)

    # Handle normal FAQ flow
    if location:
        best, score = find_best_faq(f"wifi {location}")
    else:
        best, score = find_best_faq(user_text)

    if best and score >= 1:
        store_query(
            user_text,
            matched_faq_id=best["faq_id"],
            match_score=score,
            location=location,
            user_email=user_email
        )
        response_text = best["answer"]
    else:
        qid = store_query(
            user_text,
            match_score=score,
            sent_to_human=True,
            location=location,
            user_email=user_email
        )
        try:
            send_fallback_email(user_text, qid, user_email)
        except Exception as e:
            print("SES send failed:", e)
        response_text = (
            "I'm sorry, I don't have an answer. "
            "I've forwarded this to our IT team."
        )

    # ---------- Return Lex-compatible JSON ----------
    return {
        "sessionState": {
            "sessionAttributes": session_attrs,
            "dialogAction": {"type": "Close"},
            "intent": {"name": intent_name, "state": "Fulfilled"},
        },
        "messages": [
            {"contentType": "PlainText", "content": response_text}
        ],
    }
