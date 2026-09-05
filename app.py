from flask import Flask, render_template

app = Flask(__name__)


# ================= HOME PAGE =================

@app.route("/")
def home():
    return render_template("index.html")


# ================= CART PAGE =================

@app.route("/cart")
def cart():
    return render_template("cart.html")


# ================= RUN WEBSITE =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)