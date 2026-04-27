import pandas as pd
import tempfile
import csv
import os
from groq import Groq

# ======= CONFIGURATION =======
# Your API Key is now hardcoded here and will not be asked for again.
GROQ_API_KEY = "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"

def preprocess_and_save(file_path):
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8', na_values=['NA', 'N/A', 'missing'])
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, na_values=['NA', 'N/A', 'missing'])
        else:
            return None, None, None, "Unsupported file format."

        # Clean column names (removes newlines and extra spaces that cause KeyErrors)
        df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode='w', newline='', encoding='utf-8') as temp_file:
            df.to_csv(temp_file.name, index=False, quoting=csv.QUOTE_ALL)
            return df, df.columns.tolist(), df.head().to_html(), None
    except Exception as e:
        return None, None, None, str(e)

# ======= EXECUTION FLOW =======
def run_analysis(file_path, query):
    if not GROQ_API_KEY:
        print("❌ Error: GROQ_API_KEY is not set in the source code.")
        return

    try:
        df, cols, df_html, err = preprocess_and_save(file_path)

        if err:
            print(f"❌ Error: {err}")
            return

        # The prompt now includes the actual columns so the AI doesn't hallucinate 'applicant'
        prompt = f"""
        You are a Python data analyst. The dataframe `df` has these columns: {cols}
        Based on these columns, write Python code using pandas to answer the question.
        
        Question: {query}

        Rules:
        - Use 'result' as the final output variable.
        - Only return the raw code. Do not include markdown formatting or 'python' tags.
        """

        client = Groq(api_key=GROQ_API_KEY)
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile"
        )

        code_generated = chat_completion.choices[0].message.content.strip().replace("```python", "").replace("```", "")
        
        print("\n🤖 Generated Code:")
        print(code_generated)

        # Execute the code safely
        local_vars = {"df": df, "pd": pd}
        exec(code_generated, {}, local_vars)

        result = local_vars.get("result", "⚠️ No result generated.")
        print("\n📈 Final Result:")
        print(result)

    except Exception as e:
        print(f"❌ Exception occurred: {e}")

# Example Usage:
if __name__ == "__main__":
    # Change these values as needed
    path = "diabetes.csv" 
    user_query = "Find the count of suman in the Name of Applicant column"
    run_analysis(path, user_query)