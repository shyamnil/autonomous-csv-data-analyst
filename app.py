from flask import Flask, render_template, request
from utils import preprocess_and_save
import pandas as pd
from groq import Groq
import os

app = Flask(__name__)

# Hardcoded API Key - Replace with your actual key
GROQ_API_KEY = ""

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    df = None
    df_html = ""
    df_preview_html = ""
    result_html = ""
    code_generated = ""

    if request.method == "POST":
        file = request.files.get("file")
        query = request.form.get("query")

        if file:
            df, cols, df_html, err = preprocess_and_save(file)
            if err:
                message = err
            else:
                # Show first 5 rows preview
                df_preview_html = df.head().to_html(classes="table-auto w-full") if df is not None else ""

                if query:
                    try:
                        # Improved prompt including column names
                        prompt = f"""
                        You are a Python data analyst. The dataframe `df` has these columns: {cols}
                        
                        Write ONLY the Python code using pandas to answer this question:
                        Question: {query}
                        
                        Rules:
                        1. Use 'result' as the final output variable.
                        2. Do not include markdown code blocks (like ```python).
                        3. Use the column names exactly as provided above.
                        """

                        client = Groq(api_key=GROQ_API_KEY)
                        chat_completion = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama-3.3-70b-versatile"
                        )

                        code_generated = chat_completion.choices[0].message.content.strip()
                        
                        # Execute generated code
                        local_vars = {"df": df, "pd": pd}
                        exec(code_generated, {}, local_vars)

                        result = local_vars.get("result", "No result generated.")
                        if isinstance(result, pd.DataFrame):
                            result_html = result.to_html(classes="table-auto w-full")
                        else:
                            result_html = str(result)

                    except Exception as e:
                        message = f"Error running analysis: {e}"
        else:
            message = "Please upload a file."

    return render_template(
        "index.html",
        message=message,
        df_html=df_html,
        df_preview_html=df_preview_html,
        code_generated=code_generated,
        result_html=result_html,
    )

if __name__ == "__main__":
    app.run(debug=True)