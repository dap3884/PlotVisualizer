import shutil
import os
import subprocess
import tempfile
import uuid
import logging

logger = logging.getLogger(__name__)

def sanitize_code(code: str, language: str):
    banned_keywords = {
        "python": ["os.system", "subprocess", "open(", "shutil", "eval", "exec"],
        "r": ["system(", "unlink(", "file.remove", "shell(", "eval", "assign"]
    }

    for keyword in banned_keywords.get(language, []):
        if keyword in code:
            logger.warning(f"Blocked keyword detected: '{keyword}' in {language} code.")
            raise ValueError(f"Use of '{keyword}' is not allowed in scripts.")
    logger.debug(f"Code passed sanitization for language: {language}")


def run_script_in_docker(code, language, output_path):
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Creating temporary directory at {temp_dir}")

        script_file = "script.py" if language == "python" else "script.R"
        script_path = os.path.join(temp_dir, script_file)

        with open(script_path, "w") as f:
            f.write(code)
        logger.info(f"Script written to {script_path}")

        abs_output_dir = os.path.abspath("output")
        os.makedirs(abs_output_dir, exist_ok=True)
        logger.info(f"Output directory ensured at {abs_output_dir}")

        image = "viz-python:latest" if language == "python" else "viz-r:latest"
        logger.info(f"Running Docker container with image: {image}")

        # Cleanup
        for f in os.listdir(abs_output_dir):
            stray = os.path.join(abs_output_dir, f)
            if os.path.isfile(stray):
                os.remove(stray)
                logger.debug(f"Removed stray file: {stray}")

        try:
            result = subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{script_path}:/scripts/{script_file}",
                "-v", f"{abs_output_dir}:/output",
                image
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15)

            logger.info(f"Docker run completed with return code {result.returncode}")

            if result.returncode != 0:
                logger.error(f"Docker stderr: {result.stderr.strip()}")
                raise RuntimeError(f"Script failed with error:\n{result.stderr.strip() or 'Unknown error'}")

            files = os.listdir(abs_output_dir)
            output_files = [f for f in files if f.endswith((".png", ".html"))]

            logger.info(f"Output Files: {output_files}")
            if not output_files:
                raise FileNotFoundError("No output .png or .html file found in /output")

            detected_file = output_files[0]
            src = os.path.join(abs_output_dir, detected_file)
            ext = ".png" if ".png" in code else ".html"
            final_output = f"{uuid.uuid4()}{ext}"
            final_path = os.path.join(abs_output_dir, final_output)

            shutil.move(src, final_path)
            logger.info(f"Moved output file to: {final_path}")

            # Cleanup
            for f in files:
                stray = os.path.join(abs_output_dir, f)
                if stray != final_path and os.path.isfile(stray):
                    os.remove(stray)
                    logger.debug(f"Removed stray file: {stray}")

            return final_output

        except subprocess.TimeoutExpired:
            logger.exception("Script execution timed out.")
            raise RuntimeError("Script execution timed out.")
        except subprocess.CalledProcessError as e:
            logger.exception("Subprocess failed.")
            raise RuntimeError(f"Execution failed: {e.stderr or str(e)}")
        except FileNotFoundError as e:
            logger.exception("Expected output not found.")
            raise RuntimeError(f"Expected output file not found: {e}")
