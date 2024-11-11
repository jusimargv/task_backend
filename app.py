from flask import Flask, jsonify, request, abort, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from datetime import datetime
from flask_cors import CORS  # Adicionando o CORS

app = Flask(__name__)

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tarefas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Inicializando o CORS para permitir requisições de diferentes origens
CORS(app)

# Modelo da tabela Tarefas
class Tarefa(db.Model):
    __tablename__ = 'tarefas'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    custo = db.Column(db.Float, nullable=True)
    data_limite = db.Column(db.Date, nullable=True)
    ordem = db.Column(db.Integer, nullable=False, unique=True)

# Inicializar o banco de dados
with app.app_context():
    db.create_all()

# Rota para carregar a página HTML
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint para listar todas as tarefas
@app.route('/tarefas', methods=['GET'])
def listar_tarefas():
    tarefas = Tarefa.query.order_by(Tarefa.ordem).all()
    resultado = [
        {
            "id": tarefa.id,
            "nome": tarefa.nome,
            "custo": tarefa.custo,
            "data_limite": tarefa.data_limite.strftime('%Y-%m-%d') if tarefa.data_limite else None,
            "ordem": tarefa.ordem,
            "destaque": tarefa.custo >= 1000.00
        } for tarefa in tarefas
    ]
    return jsonify(resultado)

# Endpoint para adicionar uma nova tarefa
@app.route('/tarefas', methods=['POST'])
def adicionar_tarefa():
    dados = request.json
    
    # Validação do nome da tarefa
    if not dados.get('nome'):
        abort(400, description="O campo 'nome' é obrigatório.")
    
    if Tarefa.query.filter_by(nome=dados['nome']).first():
        abort(400, description="O nome da tarefa já existe.")
    
    # Criando a nova tarefa
    nova_tarefa = Tarefa(
        nome=dados['nome'],
        custo=dados['custo'],
        data_limite=datetime.strptime(dados['data_limite'], '%Y-%m-%d').date() if dados['data_limite'] else None,
        ordem=db.session.query(func.max(Tarefa.ordem)).scalar() + 1 if Tarefa.query.count() > 0 else 1
    )
    
    # Adicionando ao banco de dados
    db.session.add(nova_tarefa)
    db.session.commit()
    
    return jsonify({"id": nova_tarefa.id}), 201

# Endpoint para editar uma tarefa existente
@app.route('/tarefas/<int:id>', methods=['PUT'])
def editar_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)
    dados = request.json
    
    # Validação do nome da tarefa
    if not dados.get('nome'):
        abort(400, description="O campo 'nome' é obrigatório.")
    if tarefa.nome != dados['nome'] and Tarefa.query.filter_by(nome=dados['nome']).first():
        abort(400, description="O nome da tarefa já existe.")
    
    # Atualizando os dados da tarefa
    tarefa.nome = dados['nome']
    tarefa.custo = dados['custo']
    tarefa.data_limite = datetime.strptime(dados['data_limite'], '%Y-%m-%d').date() if dados['data_limite'] else None
    db.session.commit()
    
    return jsonify({"id": tarefa.id})

# Endpoint para excluir uma tarefa
@app.route('/tarefas/<int:id>', methods=['DELETE'])
def excluir_tarefa(id):
    tarefa = Tarefa.query.get_or_404(id)
    db.session.delete(tarefa)
    db.session.commit()
    return jsonify({"message": "Tarefa excluída com sucesso."})

# Endpoint para reordenar tarefas
@app.route('/tarefas/<int:id>/mover', methods=['PATCH'])
def reordenar_tarefa(id):
    direcao = request.json.get('direcao')
    
    if direcao not in ['subir', 'descer']:
        abort(400, description="Direção inválida. Use 'subir' ou 'descer'.")
    
    tarefa_atual = Tarefa.query.get_or_404(id)
    
    if direcao == 'subir' and tarefa_atual.ordem > 1:
        tarefa_anterior = Tarefa.query.filter_by(ordem=tarefa_atual.ordem - 1).first()
        tarefa_atual.ordem, tarefa_anterior.ordem = tarefa_anterior.ordem, tarefa_atual.ordem
    elif direcao == 'descer':
        tarefa_proxima = Tarefa.query.filter_by(ordem=tarefa_atual.ordem + 1).first()
        if tarefa_proxima:
            tarefa_atual.ordem, tarefa_proxima.ordem = tarefa_proxima.ordem, tarefa_atual.ordem
    
    db.session.commit()
    
    return jsonify({"message": "Ordem alterada com sucesso."})

# Iniciar o aplicativo Flask
if __name__ == '__main__':
    app.run(debug=True)
