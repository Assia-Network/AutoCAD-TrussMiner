import sys
import os
import streamlit.web.cli as stcli

def resolve_path(path):
    if getattr(sys, '_MEIPASS', False):
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.getcwd(), path)

if __name__ == "__main__":

    app_path = resolve_path("app.py")

    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
        "--browser.gatherUsageStats=false", 
        "--server.headless=false", 
        "--server.address=localhost",
        "--server.port=8501",
    ]

    sys.exit(stcli.main())
