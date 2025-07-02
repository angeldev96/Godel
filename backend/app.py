from flask import Flask, request, jsonify
from flask_cors import CORS
from pathlib import Path
import sys
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import tempfile
import uuid

# Cargar variables de entorno
load_dotenv()

# Añadir la ruta de SPCTR al path para poder importar los módulos
sys.path.append(str(Path(__file__).parent.parent / 'SPCTR' / 'SPCTRLLMPipLne'))

from llm.llm_document_processor import LLMDocumentProcessor

app = Flask(__name__)
CORS(app) # Habilitar CORS para todas las rutas

# Configuración de Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

@app.route('/process-document', methods=['POST'])
def process_document_endpoint():
    """
    Endpoint para procesar un documento desde Supabase Storage.
    Espera un JSON con:
    {
        "file_path": "ruta/del/archivo/en/supabase/storage.docx"
    }
    """
    data = request.get_json()
    if not data or 'file_path' not in data:
        return jsonify({"error": "Missing file_path"}), 400

    file_path = data['file_path']
    
    # Crear un directorio temporal para las descargas si no existe
    temp_dir = Path(tempfile.gettempdir()) / "doc_processing"
    temp_dir.mkdir(exist_ok=True)
    
    # Generar un nombre de archivo local único para evitar colisiones
    local_filename = f"{uuid.uuid4()}.docx"
    local_file_path = temp_dir / local_filename

    try:
        # Descargar el archivo desde Supabase Storage
        print(f"Downloading {file_path} from Supabase Storage...")
        with open(local_file_path, "wb+") as f:
            res = supabase.storage.from_("documents").download(file_path)
            f.write(res)
        print(f"File downloaded to {local_file_path}")

        # Inicializar el procesador de documentos
        processor = LLMDocumentProcessor()
        
        # Procesar el archivo descargado
        results = processor.check_citations(str(local_file_path), None, debug=True)

        if results:
            return jsonify(results), 200
        else:
            return jsonify({"error": "Failed to process document"}), 500

    except Exception as e:
        print(f"Error processing document: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Limpiar el archivo temporal
        if local_file_path.exists():
            local_file_path.unlink()
            print(f"Cleaned up temporary file: {local_file_path}")

if __name__ == '__main__':
    app.run(debug=True, port=5001) 