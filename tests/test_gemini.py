from app.config import settings
import google.generativeai as genai

print(f'Gemini API key present: {bool(settings.gemini_api_key)}')
print(f'Gemini model: {settings.gemini_model}')

try:
    genai.configure(api_key=settings.gemini_api_key)
    # Use the model from settings
    model = genai.GenerativeModel(settings.gemini_model)
    response = model.generate_content('Extract company name and email from: Contact Acme Corp at sales@acme.com')
    print(f'Response: {response.text[:200]}')
    print('Gemini is WORKING!')
except Exception as e:
    print(f'Error: {e}')
