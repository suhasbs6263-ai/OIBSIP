from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret-key"
socketio = SocketIO(app)

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("chat_message")
def handle_chat_message(data):
    """
    data = { "username": "...", "message": "..." }
    Broadcast to everyone.
    """
    print(f"{data['username']}: {data['message']}")
    emit("chat_message", data, broadcast=True)

if __name__ == "__main__":
    # Use eventlet for better realtime performance
    socketio.run(app, host="0.0.0.0", port=5001, debug=True)
