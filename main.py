from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sys
from io import StringIO
import traceback
import re

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Request & Response Models
# =========================
class CodeRequest(BaseModel):
    code: str

class CodeResponse(BaseModel):
    error: List[int]
    result: str


# =========================
# TOOL FUNCTION
# =========================
def execute_python_code(code: str) -> dict:
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        exec(code)
        output = sys.stdout.getvalue()
        return {"success": True, "output": output}

    except Exception:
        output = traceback.format_exc()
        return {"success": False, "output": output}

    finally:
        sys.stdout = old_stdout


# =========================
# CORRECT ERROR LINE EXTRACTOR
# =========================
def extract_line_number(traceback_str: str) -> List[int]:
    """
    Extract the line number from:
    File "<string>", line X
    which represents the user's executed code.
    """

    matches = re.findall(r'File "<string>", line (\d+)', traceback_str)

    if matches:
        return [int(matches[-1])]  # Use the last occurrence

    return []


# =========================
# MAIN ENDPOINT
# =========================
@app.post("/code-interpreter", response_model=CodeResponse)
async def code_interpreter(request: CodeRequest):

    execution = execute_python_code(request.code)

    if execution["success"]:
        return CodeResponse(error=[], result=execution["output"])

    error_lines = extract_line_number(execution["output"])

    return CodeResponse(
        error=error_lines,
        result=execution["output"]
    )


@app.get("/")
def home():
    return {"message": "Code Interpreter API Running"}