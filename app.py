#redeploy
from flask import Flask, render_template, request, send_file
import os
import cv2
from PIL import Image
import uuid

app = Flask(__name__,template_folder="templates")

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

DATABASE = {}

# 🔐 Encode
def encode_image(image_path, message, key):
    img = Image.open(image_path).convert("RGB")

    full_message = message + "||" + key + "~~~"
    binary = ''.join(format(ord(i), '08b') for i in full_message)

    data = list(img.getdata())
    new_data = []

    index = 0
    for pixel in data:
        r, g, b = pixel

        if index < len(binary):
            r = r & ~1 | int(binary[index]); index += 1
        if index < len(binary):
            g = g & ~1 | int(binary[index]); index += 1
        if index < len(binary):
            b = b & ~1 | int(binary[index]); index += 1

        new_data.append((r, g, b))

    img.putdata(new_data)
    path = os.path.join(OUTPUT_FOLDER, "encoded.png")
    img.save(path)

    return path


# 🎥 Video embed
def embed_image_in_video(video_path, image_path):
    cap = cv2.VideoCapture(video_path)

    width = int(cap.get(3))
    height = int(cap.get(4))

    out_path = os.path.join(OUTPUT_FOLDER, "output.avi")

    out = cv2.VideoWriter(out_path,
        cv2.VideoWriter_fourcc(*'XVID'),
        20.0,
        (width, height))

    img = cv2.imread(image_path)
    img = cv2.resize(img, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(img)

    cap.release()
    out.release()

    return out_path


# 🔓 Decode
def decode_image(image_path):
    img = Image.open(image_path).convert("RGB")
    binary = ""

    for pixel in img.getdata():
        for val in pixel[:3]:
            binary += str(val & 1)

    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]

    msg = ""
    for c in chars:
        msg += chr(int(c, 2))
        if msg.endswith("~~~"):
            break

    msg = msg[:-3]
    parts = msg.split("||", 1)

    return parts if len(parts) == 2 else (msg, None)


# 🌐 HOME
@app.route("/")
def index():
    return "app is working"


# 🔐 ENCODE
@app.route("/encode", methods=["POST"])
def encode():
    message = request.form["message"]
    key = request.form["key"]

    image = request.files["image"]
    video = request.files["video"]

    img_path = os.path.join(UPLOAD_FOLDER, image.filename)
    vid_path = os.path.join(UPLOAD_FOLDER, video.filename)

    image.save(img_path)
    video.save(vid_path)

    enc_img = encode_image(img_path, message, key)
    embed_image_in_video(vid_path, enc_img)

    uid = str(uuid.uuid4())

    DATABASE[uid] = {"image": enc_img, "key": key}

    link = f"http://127.0.0.1:5000/open/{uid}"

    whatsapp_link = f"https://wa.me/?text=Open%20this%20secret%20message:%20{link}"

    return f"""
    <html>
    <body style='text-align:center;margin-top:80px;font-family:Arial;'>

    <h2>✅ Message Ready!</h2>

    <a href="/download">⬇ Download Video</a><br><br>

    <h3>🔗 Share this link</h3>
    <p>{link}</p>

    <button onclick="navigator.clipboard.writeText('{link}')">
    Copy Link 📋
    </button><br><br>

    <a href="{whatsapp_link}" target="_blank">
    📱 Share on WhatsApp
    </a>

    </body>
    </html>
    """


# 📥 Download
@app.route("/download")
def download():
    return send_file(os.path.join(OUTPUT_FOLDER, "output.avi"), as_attachment=True)


# 🔓 OPEN PAGE
@app.route("/open/<id>")
def open_page(id):
    return f"""
    <html>
    <head>
    <style>
    body {{
        background: linear-gradient(135deg,#ff758c,#ff7eb3);
        font-family: Arial;
        text-align:center;
        margin-top:150px;
        color:white;
    }}
    .box {{
        background:white;
        color:black;
        padding:25px;
        border-radius:15px;
        width:300px;
        margin:auto;
    }}
    input {{
        padding:10px;
        width:80%;
    }}
    button {{
        background:#ff758c;
        color:white;
        padding:10px;
        border:none;
    }}
    </style>
    </head>

    <body>
    <div class="box">
    <h2>🔓 Unlock Message</h2>

    <form method="post" action="/view/{id}">
    <input type="password" name="key" placeholder="Secret key 🔒"><br><br>
    <button>Unlock</button>
    </form>

    </div>
    </body>
    </html>
    """


# 🔓 VIEW MESSAGE
@app.route("/view/<id>", methods=["POST"])
def view(id):
    key = request.form["key"]
    data = DATABASE.get(id)

    if not data:
        return "<h1>❌ Invalid Link</h1>"

    if key == data["key"]:
        msg, _ = decode_image(data["image"])

        if "love" in msg.lower():
            return f"<h1 style='color:red;text-align:center;margin-top:150px;'>❤️ {msg} 💖</h1>"

        return f"""
        <html>
        <body style="background:linear-gradient(135deg,#43e97b,#38f9d7);text-align:center;">

        <div style="margin-top:150px;font-size:30px;">
        🎉 {msg}
        </div>

        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
        confetti();
        </script>

        </body>
        </html>
        """
    else:
        return "<h1 style='color:red;text-align:center;margin-top:150px;'>❌ Wrong Key</h1>"


if __name__ == "__main__":
        app.run(host="0.0.0.0",port=10000)
