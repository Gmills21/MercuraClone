import json
from typing import List
from .data import ExtractionResult

def visualize(extraction_result_path_or_obj: str | ExtractionResult) -> str:
    """
    Generate interactive HTML visualization for extraction results.
    """
    if isinstance(extraction_result_path_or_obj, str):
        # Load from file (jsonl)
        # Mocking file load for now as we likely pass object directly
        return "<html><body>Visualization not implemented for file path input yet</body></html>"
    
    result = extraction_result_path_or_obj
    text = result.document_text
    extractions = result.extractions
    
    # Simple HTML template with highlighting
    # We Sort extractions by position to insert spans
    
    # Filter out extractions with no position
    valid_extractions = [e for e in extractions if e.source_start_char is not None]
    valid_extractions.sort(key=lambda x: x.source_start_char)
    
    # Construct HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: sans-serif; display: flex; height: 100vh; margin: 0; }
            .container { display: flex; width: 100%; }
            .text-panel { flex: 1; padding: 20px; overflow-y: auto; border-right: 1px solid #ccc; line-height: 1.6; white-space: pre-wrap; }
            .data-panel { flex: 1; padding: 20px; overflow-y: auto; background: #f9f9f9; }
            .highlight { background-color: #e6fffa; border-bottom: 2px solid #00b8d9; cursor: pointer; transition: background 0.2s; }
            .highlight:hover { background-color: #b3f5ea; }
            .highlight.selected { background-color: #b3f5ea; border-bottom: 2px solid #005f73; }
            .card { background: white; padding: 10px; margin-bottom: 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #00b8d9; }
            .card:hover { transform: translateY(-1px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h2 { color: #333; }
        </style>
        <script>
            function highlight(id) {
                // Remove existing
                document.querySelectorAll('.highlight').forEach(el => el.classList.remove('selected'));
                document.querySelectorAll('.card').forEach(el => el.style.background = 'white');
                
                // Add new
                const span = document.getElementById('span-' + id);
                if (span) {
                    span.classList.add('selected');
                    span.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                const card = document.getElementById('card-' + id);
                if (card) {
                    card.style.background = '#e6fffa';
                }
            }
        </script>
    </head>
    <body>
        <div class="container">
            <div class="text-panel">
                <h2>Source Document</h2>
                <div>
    """
    
    # Insert spans
    current_pos = 0
    formatted_text = ""
    
    # We need to handle overlaps, but assuming no overlaps for MVP
    for i, ext in enumerate(valid_extractions):
        start = ext.source_start_char
        end = ext.source_end_char
        
        # Add text before match
        formatted_text += text[current_pos:start]
        
        # Add highlighted match
        formatted_text += f'<span id="span-{i}" class="highlight" onclick="highlight({i})">{text[start:end]}</span>'
        
        current_pos = end
    
    formatted_text += text[current_pos:]
    html += formatted_text
    
    html += """
                </div>
            </div>
            <div class="data-panel">
                <h2>Extracted Data</h2>
    """
    
    for i, ext in enumerate(valid_extractions):
        html += f"""
        <div id="card-{i}" class="card" onclick="highlight({i})">
            <div><strong>{ext.extraction_class}</strong></div>
            <div style="font-size: 1.1em; color: #111;">{ext.extraction_text}</div>
            <div style="font-size: 0.8em; color: #666;">Confidence: {int((ext.confidence or 0)*100)}%</div>
        </div>
        """
        
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def save_annotated_documents(results: List[ExtractionResult], output_name: str):
    # Mock
    pass
