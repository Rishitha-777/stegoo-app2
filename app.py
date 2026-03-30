from flask import Flask, render_template, request, redirect, url_for
import uuid

app = Flask(__name__, template_folder="templates")

data_store = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/encode", methods=["POST"])
def encode():
    message = request.form["message"]
    key = request.form["key"]

    unique_id = str(uuid.uuid4())[:8]

    data_store[unique_id] = {
        "message": message,
        "key": key
    }

    return redirect(url_for("share", id=unique_id))


@app.route("/share/<id>")
def share(id):
    link = url_for("view", id=id, _external=True)
    return render_template("share.html", link=link)


@app.route("/view/<id>", methods=["GET", "POST"])
def view(id):
    if id not in data_store:
        return "<h1>Invalid Link</h1>"

    if request.method == "POST":
        entered_key = request.form["key"]

        if entered_key == data_store[id]["key"]:
            return render_template("message.html", msg=data_store[id]["message"])
        else:
            return render_template("view.html", id=id, error="Wrong Key")

    return render_template("view.html", id=id)


if __name__ == "__main__":
    app.run(debug=True)
