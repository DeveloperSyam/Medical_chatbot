import google.generativeai as genai
import os

# Load API key from environment variable
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use Gemini 1.5 Flash for fast responses
model = genai.GenerativeModel("gemini-1.5-flash")

def format_response_as_html(response_text):
    """Convert plain text advice into a beautifully formatted HTML response with icons."""
    lines = response_text.strip().split("\n")
    
    html_response = """
    <div style="padding:8px;">
      <h5 style="color:#0d6efd; margin-bottom:12px;">📝 Recommended Healthcare Advice:</h5>
      <ul style="padding-left:18px; margin-bottom:12px;">
    """

    icons = ["💧", "🛌", "🍽️", "🏥", "☕", "🥗", "📞", "⚠️", "📋", "🩺"]

    icon_index = 0
    for line in lines:
        clean_line = line.lstrip("1234567890.•- ").strip()
        if clean_line:
            icon = icons[icon_index % len(icons)]
            html_response += f"<li style='margin-bottom:10px; line-height:1.6;'>{icon} {clean_line}</li>"
            icon_index += 1

    html_response += """
      </ul>
      <div style="background:#f8f9fa; border-left:4px solid #dc3545; padding:10px 14px; border-radius:8px; font-size:0.85rem; color:#555;">
        ⚠️ <strong>Disclaimer:</strong> This chatbot provides general health information only. 
        For serious symptoms or emergencies, please consult a licensed healthcare professional immediately.
      </div>
    </div>
    """

    return html_response

def generate_medical_response(question):
    prompt = f"""
You are an AI-powered medical assistant designed to provide basic healthcare advice in simple, safe, and easy-to-understand language.

**Important guidelines:**
- Provide general, evidence-based health information.
- Avoid giving specific diagnoses or prescriptions.
- Include clear disclaimers for serious or emergency symptoms.
- Keep the tone kind, reassuring, and informative.
- If symptoms sound serious or urgent, advise consulting a doctor immediately.

User Question:
"{question}"

Respond clearly, in a bullet point format. Use emojis like 💧, 🛌, 🥗, ⚠️ etc. to make the advice engaging and easy to follow.
    """.strip()

    try:
        response = model.generate_content(prompt)
        final_response = response.text.strip()
        formatted_response = format_response_as_html(final_response)
        return formatted_response

    except Exception as e:
        error_html = f"""
        <div style="color:#dc3545;">
          ❌ <strong>Error:</strong> Sorry, I'm currently unable to provide a response. 
          Please try again later.
        </div>
        """
        return error_html









