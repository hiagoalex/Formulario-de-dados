# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pandas as pd
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# --- Configurações Iniciais ---
app = Flask(__name__)
# MUDE ESTA CHAVE PARA UMA CHAVE FORTE EM PRODUÇÃO!
app.config['SECRET_KEY'] = 'chave_de_seguranca_muito_secreta' 
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para upload
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'csv'} 

DATA_FILE = 'data/dados_coletados.csv'

# Senha ÚNICA para acesso ao painel
MASTER_PASSWORD = 'smvdados' 

# --- Funções Auxiliares ---
def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def initialize_data_file():
    """Cria o arquivo CSV e a pasta de uploads se não existirem."""
    if not os.path.exists('data'):
        os.makedirs('data')
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        
    if not os.path.exists(DATA_FILE):
        columns = [
            'data_envio', 
            'prazo_entrega', 
            'objetivo_analise', 
            'indicadores_metricas', 
            'setores_envolvidos', 
            'fonte_dados',
            'arquivo_anexado'
        ]
        df = pd.DataFrame(columns=columns)
        df.to_csv(DATA_FILE, index=False)

def add_data_to_csv(data):
    """Adiciona uma nova linha de dados ao CSV."""
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        initialize_data_file()
        df = pd.read_csv(DATA_FILE)
        
    new_row = pd.DataFrame([data])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

initialize_data_file()

# --- Autenticação com Flask-Login Adaptada (Apenas Senha) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

class User(UserMixin):
    def get_id(self):
        return 'painel_unico' 

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'painel_unico':
        return User()
    return None

# --- Rotas da Aplicação ---

# 1. Formulário Público 
@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        uploaded_filename = None
        if 'arquivo' in request.files:
            file = request.files['arquivo']
            if file.filename != '' and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                uploaded_filename = f"{timestamp}_{original_filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], uploaded_filename))
            elif file.filename != '':
                 flash('Tipo de arquivo não permitido.', 'warning')
                 return redirect(url_for('formulario'))

        try:
            data = {
                'data_envio': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prazo_entrega': request.form.get('prazo_entrega'),
                'objetivo_analise': request.form.get('objetivo_analise'),
                'indicadores_metricas': request.form.get('indicadores_metricas'),
                'setores_envolvidos': request.form.get('setores_envolvidos'),
                'fonte_dados': request.form.get('fonte_dados'),
                'arquivo_anexado': uploaded_filename if uploaded_filename else 'Nenhum'
            }
            
            add_data_to_csv(data)
            
            flash('Sua solicitação e anexos foram enviados com sucesso!', 'success')
            return redirect(url_for('formulario'))
            
        except Exception as e:
            flash(f'Erro ao salvar os dados: {e}', 'error')
            
    return render_template('formulario.html')

# 2. Rota de Download Protegida
@app.route('/download/<path:filename>', methods=['GET'])
@login_required 
def download_file(filename):
    """Permite o download de arquivos da pasta uploads/, protegido por login."""
    try:
        # Garante que o usuário só possa baixar arquivos da pasta de upload configurada
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return "Arquivo não encontrado.", 404

# 3. Área Restrita (Visualização da Lista de Registros)
@app.route('/registros')
@login_required
def registros():
    try:
        df = pd.read_csv(DATA_FILE)
        df = df.iloc[::-1] # Mais recentes primeiro
        
        # Função para criar links de download na tabela
        def make_download_link(filename):
            if filename in ('Nenhum', 'nan') or pd.isna(filename):
                return 'Nenhum'
            
            # Cria o link para a rota '/download/<filename>'
            link = url_for('download_file', filename=filename)
            return f'<a href="{link}" target="_blank">{filename}</a>'
            
        df_display = df.copy()
        df_display['arquivo_anexado'] = df_display['arquivo_anexado'].astype(str).apply(make_download_link)
        
        # O escape=False é crucial para o Flask renderizar o HTML do link
        data_html = df_display.to_html(classes='table table-striped table-hover', index=False, escape=False)
        num_registros = len(df)

    except Exception as e:
        data_html = f"<div class='alert alert-warning'>Erro ao carregar dados: {e}</div>"
        num_registros = 0
        
    return render_template('registros.html', data_html=data_html, num_registros=num_registros, data_file=DATA_FILE)

# 4. Login (Somente Senha: 'smvdados')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('registros'))
        
    if request.method == 'POST':
        password_attempt = request.form.get('password')
        
        if password_attempt == MASTER_PASSWORD:
            user = User()
            login_user(user)
            flash('Acesso concedido.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('registros'))
        else:
            flash('Senha incorreta. Tente novamente.', 'error')
            
    return render_template('login.html') 

# 5. Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('formulario'))

# --- Execução da Aplicação ---
if __name__ == '__main__':
    # Em produção, use um servidor robusto (ex: Gunicorn) e debug=False
    app.run(debug=True)