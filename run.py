
from app.app import create_app
from flask import send_from_directory
import os

app = create_app()

@app.route("/static/swagger.json")
def swagger_json():
    # Caminho absoluto do projeto
    base_dir = os.path.dirname(os.path.abspath(__file__))
    swagger_path = os.path.join(base_dir, "app", "swagger")

    return send_from_directory(swagger_path, "swagger.json")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=3000,
        debug=True
    )
