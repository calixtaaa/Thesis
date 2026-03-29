"""
Static site generator for Netlify deployment.
Registers mock Flask routes so url_for() works, then renders
all Jinja2 templates into plain HTML for Netlify's CDN.
"""

from pathlib import Path
from flask import Flask, render_template

app = Flask(
    __name__,
    template_folder="WebPages/templates",
    static_folder="WebPages/static",
    static_url_path="/static",
)
app.secret_key = "netlify-build-key"

# Provide csrf_token() in templates (static placeholder for Netlify)
app.jinja_env.globals["csrf_token"] = lambda: "static-deploy"


# Register stub routes so url_for() resolves correctly
@app.route("/")
def index(): pass

@app.route("/login")
def login(): pass

@app.route("/dashboard")
def dashboard(): pass

@app.route("/logout")
def logout(): pass


PUBLIC = Path("public")


def render_page(template_name, output_path, **context):
    with app.test_request_context("/"):
        html = render_template(template_name, **context)
    dest = PUBLIC / output_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    print(f"  + {template_name}  ->  public/{output_path}")


if __name__ == "__main__":
    PUBLIC.mkdir(exist_ok=True)

    render_page("home.html", "index.html")
    render_page("login.html", "login/index.html")
    render_page("dashboard.html", "dashboard/index.html", username="Admin")

    print(f"\n  All pages rendered to {PUBLIC.resolve()}")
