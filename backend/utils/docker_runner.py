import shutil
import os
import subprocess
import tempfile

def sanitize_code(code: str, language: str):
    banned_keywords = {
        "python": ["os.system", "subprocess", "open(", "shutil", "eval", "exec"],
        "r": ["system(", "unlink(", "file.remove", "shell(", "eval", "assign"]
    }

    for keyword in banned_keywords.get(language, []):
        if keyword in code:
            raise ValueError(f"Use of '{keyword}' is not allowed in scripts.")


def run_script_in_docker(code, language, output_path, output_type, visualization_type):
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
                "-e", f"OUTPUT_TYPE={output_type}",
                "-e", f"VIS_TYPE={visualization_type}",
                image
            ], check=True, timeout=15)

            # Determine default filename
            if output_type == "png":
                expected_filename = "chart.png"
            else:
                expected_filename = "plot.html"

            src = os.path.join(abs_output_dir, expected_filename)

            # Move to final filename (UUID-based)
            shutil.move(src, output_path)

            # Clean up all other files
            for filename in os.listdir(abs_output_dir):
                full_path = os.path.join(abs_output_dir, filename)
                if full_path != output_path and os.path.isfile(full_path):
                    os.remove(full_path)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Execution failed: {e.stderr or e}")
        except FileNotFoundError as e:
            raise RuntimeError(f"Expected output file not found: {e}")
