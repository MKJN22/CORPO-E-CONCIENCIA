import json
import random
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS # Importamos para lidar com o CORS
import os

# Configuração do Flask
app = Flask(__name__, static_folder='.')
CORS(app) # Habilita CORS para todas as rotas da sua aplicação Flask

# Nome do arquivo JSON onde os dados do treino estão armazenados
JSON_FILE_NAME = "treinos.json"

# Variáveis para armazenar os dados carregados do JSON
workout_data_full = {}
motivational_phrases = []

def load_data(file_name):
    """
    Carrega os dados de um arquivo JSON.
    Retorna um dicionário contendo os dados ou None em caso de erro.
    """
    if not os.path.exists(file_name):
        print(f"ERRO: O ficheiro '{file_name}' não foi encontrado. Certifique-se de que está na mesma pasta.")
        return None
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"INFO: Dados de '{file_name}' carregados com sucesso.")
        return data
    except json.JSONDecodeError as e:
        print(f"ERRO: Não foi possível descodificar o JSON do ficheiro '{file_name}'. Verifique a formatação: {e}")
        return None
    except Exception as e:
        print(f"ERRO: Ocorreu um erro inesperado ao carregar o ficheiro '{file_name}': {e}")
        return None

# Carrega os dados do treino e frases motivacionais ao iniciar o aplicativo
loaded_data = load_data(JSON_FILE_NAME)
if loaded_data:
    workout_data_full = loaded_data.get("treinos", {})
    motivational_phrases = loaded_data.get("frases_genericas", [])
    if not workout_data_full:
        print("AVISO: A seção 'treinos' está vazia ou não foi encontrada no JSON.")
    if not motivational_phrases:
        print("AVISO: A seção 'frases_genericas' está vazia ou não foi encontrada no JSON.")
else:
    print("ERRO CRÍTICO: Não foi possível carregar os dados iniciais. O aplicativo pode não funcionar.")

# Rota para servir o ficheiro HTML principal
@app.route('/')
def serve_index():
    print("DEBUG: Requisição recebida para a rota raiz ('/'). Servindo index.html.")
    return send_from_directory('.', 'index.html')

# Rota da API para gerar o plano de treino
# Adicionei 'GET' temporariamente para depuração.
@app.route('/generate_workout', methods=['POST', 'OPTIONS', 'GET'])
def generate_workout():
    # --- INÍCIO DA DEPURARÃO ADICIONAL ---
    print(f"\nDEBUG: Requisição recebida em /generate_workout. Método: {request.method}")
    print(f"DEBUG: Headers da requisição: {request.headers}")
    # --- FIM DA DEPURARÃO ADICIONAL ---

    # Se for uma requisição OPTIONS (preflight CORS), apenas retorne OK
    if request.method == 'OPTIONS':
        print("DEBUG: Requisição OPTIONS recebida. Respondendo para CORS preflight.")
        return '', 200 # Retorna um corpo vazio com status OK

    # Se for uma requisição GET (apenas para diagnóstico temporário)
    if request.method == 'GET':
        print("DEBUG: Requisição GET recebida em /generate_workout (diagnóstico).")
        return "Esta é a rota de API para gerar treinos. Use o método POST para enviar dados do quiz."


    # Se for uma requisição POST
    try:
        user_answers = request.get_json() # Recebe as respostas do utilizador como JSON
        if not user_answers:
            print("ERRO: Requisição POST sem JSON válido ou corpo vazio.")
            return jsonify({"error": "Dados de requisição inválidos ou corpo vazio."}), 400

        # --- INÍCIO DA DEPURARÃO ADICIONAL ---
        print(f"DEBUG: Dados JSON recebidos: {user_answers}")
        # --- FIM DA DEPURARÃO ADICIONAL ---

        user_name = user_answers.get('userName', 'Utilizador')
        focused_areas = user_answers.get('focusedAreas', [])
        activity_level = user_answers.get('activityLevel', 'Não informado')
        main_goal = user_answers.get('mainGoal', 'Não informado')

        # Verifica se os dados de treino foram carregados
        if not workout_data_full:
            print("ERRO: Dados de treino não disponíveis no backend (workout_data_full vazio).")
            return jsonify({"error": "Dados de treino não carregados no servidor."}), 500
        if not motivational_phrases:
            print("AVISO: Frases motivacionais não disponíveis no backend. Usando padrão.")
            chosen_phrase = "Continue firme nos seus objetivos!"
        else:
            chosen_phrase = random.choice(motivational_phrases)

        suggested_workouts = []
        if focused_areas:
            for area in focused_areas:
                area_key = area.lower() # Normaliza o nome da área para corresponder às chaves no JSON
                if area_key in workout_data_full:
                    suggested_workouts.append({
                        "area": area,
                        "exercicios": workout_data_full[area_key]["exercicios"]
                    })
                else:
                    print(f"AVISO: Área de foco '{area}' não encontrada nos dados de treino.")
        
        # Se nenhuma área de foco foi selecionada OU se as áreas selecionadas não encontraram correspondência
        if not suggested_workouts and not focused_areas:
             # Nenhuma área focada selecionada pelo utilizador
             pass # O frontend vai exibir a mensagem de "não selecionou nenhuma área"
        elif not suggested_workouts and focused_areas:
            # Caso o utilizador selecione áreas, mas elas não existam no JSON (erro de digitação/dado)
            print(f"AVISO: Nenhuma das áreas focadas selecionadas ({focused_areas}) encontrou correspondência nos dados de treino.")


        # Monta o resumo dos dados do utilizador para exibição
        user_data_summary = {
            "Nome": user_name,
            "Nível de Atividade": activity_level,
            "Objetivo Principal": main_goal.replace('_', ' ').capitalize()
        }

        # Retorna o resultado como JSON para o frontend
        return jsonify({
            "phrase": chosen_phrase,
            "workouts": suggested_workouts,
            "userDataSummary": user_data_summary
        })

    except Exception as e:
        print(f"ERRO INTERNO no endpoint /generate_workout: {e}")
        # Retorna um erro 500 com a mensagem de erro para o frontend
        return jsonify({"error": f"Ocorreu um erro interno no servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
