import shutil
import os
import subprocess
import tempfile
import uuid

def sanitize_code(code: str, language: str):
    banned_keywords = {
        "python": ["os.system", "subprocess", "open(", "shutil", "eval", "exec"],
        "r": ["system(", "unlink(", "file.remove", "shell(", "eval", "assign"]
    }

    for keyword in banned_keywords.get(language, []):
        if keyword in code:
            raise ValueError(f"Use of '{keyword}' is not allowed in scripts.")


def run_script_in_docker(code, language, output_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        script_file = "script.py" if language == "python" else "script.R"
        script_path = os.path.join(temp_dir, script_file)

        with open(script_path, "w") as f:
            f.write(code)

        abs_output_dir = os.path.abspath("output")
        os.makedirs(abs_output_dir, exist_ok=True)

        image = "viz-python:latest" if language == "python" else "viz-r:latest"

        try:
            subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{script_path}:/scripts/{script_file}",
                "-v", f"{abs_output_dir}:/output",
                image
            ], check=True, timeout=15)

            # Detect output file (assume only one file is generated)
            files = os.listdir(abs_output_dir)
            output_files = [f for f in files if f.endswith((".png", ".html"))]

            if not output_files:
                raise FileNotFoundError("No output .png or .html file found in /output")

            detected_file = output_files[0]
            src = os.path.join(abs_output_dir, detected_file)

            # Use same extension in final filename
            ext = os.path.splitext(detected_file)[-1]
            final_output = f"{uuid.uuid4()}{ext}"
            final_path = os.path.join(abs_output_dir, final_output)

            shutil.move(src, final_path)

            # Clean up any stray files
            for f in files:
                stray = os.path.join(abs_output_dir, f)
                if stray != final_path and os.path.isfile(stray):
                    os.remove(stray)

            return final_output  # Return filename for API response

        except subprocess.TimeoutExpired:
            raise RuntimeError("Script execution timed out.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Execution failed: {e.stderr or str(e)}")
        except FileNotFoundError as e:
            raise RuntimeError(f"Expected output file not found: {e}")

