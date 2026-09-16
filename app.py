from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from ats.parser import UnsupportedFileError, extract_text
from ats.scorer import score_resume

MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    resume_file = request.files.get("resume")
    jd_text = (request.form.get("job_description") or "").strip()

    if resume_file is None or resume_file.filename == "":
        return jsonify({"error": "Please upload a resume file (PDF or DOCX)."}), 400

    if not jd_text:
        return jsonify({"error": "Please paste a job description."}), 400

    if len(jd_text) < 30:
        return jsonify({"error": "Job description is too short to analyze."}), 400

    file_bytes = resume_file.read()
    if not file_bytes:
        return jsonify({"error": "The uploaded resume file is empty."}), 400

    try:
        resume_text = extract_text(file_bytes, resume_file.filename)
    except UnsupportedFileError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Could not read the uploaded file. Please make sure it is a valid PDF or DOCX."}), 400

    if len(resume_text.strip()) < 30:
        return jsonify({
            "error": "Could not extract readable text from this resume. "
                     "It may be a scanned/image-based file — try a text-based PDF or DOCX instead."
        }), 400

    result = score_resume(resume_text, jd_text)
    return jsonify(result.to_dict())


@app.errorhandler(413)
def file_too_large(_exc):
    return jsonify({"error": "File is too large. Maximum size is 5 MB."}), 413


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
