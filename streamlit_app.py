import runpy

# Entry point wrapper for Streamlit Community Cloud auto-detection
if __name__ == "__main__":
    runpy.run_path("app.py", run_name="__main__")
else:
    runpy.run_path("app.py")
