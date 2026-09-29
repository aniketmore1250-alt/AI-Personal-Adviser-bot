import os

from app import create_app

app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", str(app.config.get("PORT", 3000))))
    if app.config.get("ENABLE_NGROK") and app.config.get("NGROK_AUTHTOKEN"):
        try:
            from pyngrok import conf, ngrok
            conf.get_default().auth_token = app.config["NGROK_AUTHTOKEN"]
            tunnel = ngrok.connect(port, "http")
            print(f"Ngrok public URL: {tunnel.public_url}")
        except Exception as error:
            print(f"Ngrok was not started: {error}")
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV") == "development")
