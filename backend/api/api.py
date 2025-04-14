from flask import Flask, request, jsonify, send_from_directory
from api_utils import create_upload_folder, upload_file_from_export

app = Flask(__name__)


@app.route('/upload_file', methods=['POST'])
def upload_file():

    try:
        data = request.form if request.form else request.json
        target_id = data.get('target_id')
        file_name = data.get('file_name')

        if not target_id or not file_name:
            return jsonify({'error': 'target_id und file_name erforderlich'}), 400

        folder_name = f"{target_id}_files"
        file_path = upload_file_from_export(folder_name, file_name)

        return jsonify({
            'message': f"Die Datei '{file_name}' wurde erfolgreich hochgeladen.",
            'uploaded_file': file_path
        }), 200

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except FileNotFoundError as fnf:
        return jsonify({'error': str(fnf)}), 404
    except Exception as e:
        return jsonify({'error': f"Fehler beim hochladen der Datei: {str(e)}"}), 500



if __name__ == '__main__':
    app.run(host=..., port=5000, debug=True)