import os
import requests
import secrets
from flask import Flask, redirect, request, jsonify, session
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.secret_key = os.getenv("SECRET_KEY") 
CORS(app)

FIGMA_CLIENT_ID = os.getenv("FIGMA_CLIENT_ID")
FIGMA_CLIENT_SECRET = os.getenv("FIGMA_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

@app.route("/")
def home():
    return "Welcome to Figma Comment Exporter!"

# Step 1: Redirect to Figma OAuth
@app.route("/login")
def login():
    state = secrets.token_hex(16)
    session["oauth_state"] = state  

    print(f"Generated state: {state}")  # Debug print
    print(f"Session state set: {session.get('oauth_state')}") 

    figma_auth_url = (
        "https://www.figma.com/oauth?"
        f"client_id={FIGMA_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        "scope=file_read&"
        f"state={state}&"
        "response_type=code"
    )
    return redirect(figma_auth_url)

# Step 2: Callback to get Access Token
@app.route("/callback")
def callback():
    state = request.args.get("state")
    session_state = session.get("oauth_state")
    print(f"State from query: {state}")  # Debug print
    print(f"State in session: {session.get('oauth_state')}")  # Debug print

    if state != session_state:
        return "State mismatch. Possible CSRF attack.", 400
    
    code = request.args.get("code")
    token_url = "https://www.figma.com/api/oauth/token"

    data = {
        "client_id": FIGMA_CLIENT_ID,
        "client_secret": FIGMA_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "grant_type": "authorization_code",
    }

    response = requests.post(token_url, data=data)
    access_token = response.json().get("access_token")

    if access_token:
        session.pop("oauth_state", None)
        session["access_token"] = access_token
        return jsonify({"message": "Logged in successfully", "token": access_token})
    else:
        return jsonify({"error": "Failed to authenticate"}), 400

@app.route("/set-session")
def set_session():
    session['test'] = 'Hello, sessions!'
    return "Session 'test' set!"

@app.route("/get-session")
def get_session():
    return f"Session value: {session.get('test', 'No session value set')}"

if __name__ == "__main__":
    app.run(debug=True)
    

