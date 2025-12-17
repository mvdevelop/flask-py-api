
from app.app import create_app
from flask import send_from_directory
import os

app = create_app()

# 🔹 Swagger JSON
@app.route("/static/swagger.json")
def swagger_json():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    swagger_path = os.path.join(base_dir, "app", "swagger")
    return send_from_directory(swagger_path, "swagger.json")

# 🔹 Servir imagens dos produtos
@app.route("/uploads/produtos/<filename>")
def product_image(filename):
    upload_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "uploads",
        "produtos"
    )
    return send_from_directory(upload_dir, filename)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True
    )
