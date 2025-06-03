import calendar
from sqlalchemy import func
from datetime import date, datetime
from config.settings import engine, Base, SessionLocal
from routes.alunos import bp as alunos_bp
from routes.livros import bp as livros_bp
from routes.emprestimos import bp as emprestimos_bp
from models.aluno import Aluno
from models.livro import Livro
from models.emprestimo import Emprestimo
from flask_login import current_user, LoginManager, login_user, logout_user, login_required
from routes.auth import bp as auth_bp
from models.usuario import Usuario
from flask import Flask, render_template, redirect, url_for, request
from sqlalchemy import func
from models.acesso import Acesso
from routes.users import bp as users_bp
import os
from flask import send_from_directory




def create_app():
    app = Flask(__name__,template_folder='templates',static_folder='static')
    app.config['SECRET_KEY'] = 'Ohfh:a!()*95T?F4KxR5mZkq9'
    
    
    # inicializa o LoginManager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'        # nome do endpoint de login
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        with SessionLocal() as db:
            return db.get(Usuario, int(user_id))
    

    # registra blueprints
    app.register_blueprint(auth_bp,       url_prefix='/auth')
    app.register_blueprint(alunos_bp,     url_prefix='/alunos')
    app.register_blueprint(livros_bp,     url_prefix='/livros')
    app.register_blueprint(emprestimos_bp,url_prefix='/emprestimos')
    app.register_blueprint(users_bp)
    
    
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)
    
    
    # redireciona home (/) para dashboard, mas só se estiver logado
    @app.before_request
    def require_login():
        # lista de endpoints que não exigem login
        public = ('auth.login', 'auth.logout', 'auth.register', 'static')
        # se endpoint não for público e o usuário NÃO estiver autenticado:
        if not current_user.is_authenticated and request.endpoint not in public:
            return redirect(url_for('auth.login'))
    
    
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(app.root_path, 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
    )
    
    
    # rota dashboard
    @app.route('/')
    def dashboard():
        with SessionLocal() as db:
            # métricas gerais
            total_alunos   = db.query(Aluno).count()
            total_livros   = db.query(Livro).count()
            disponiveis    = db.query(Livro).filter_by(situacao='disponível').count()
            emprestados    = db.query(Livro).filter_by(situacao='emprestado').count()
            ativos         = db.query(Emprestimo).filter_by(data_devolucao=None).count()
            atrasados      = db.query(Emprestimo).filter(
                                 Emprestimo.data_devolucao==None,
                                 Emprestimo.data_prevista_devolucao<date.today()
                               ).count()
            # empréstimos registrados hoje
            emprestimos_hoje = (
                db.query(Emprestimo)
                .filter(func.date(Emprestimo.data_emprestimo) == date.today())
                .count()
            )

            # empréstimos por mês no ano atual
            ano_atual = date.today().year
            meses = list(range(1, 13))
            emprestimos_mes_labels = [calendar.month_abbr[m] for m in meses]
            emprestimos_mes_data = []
            for m in meses:
                qtd = (
                    db.query(Emprestimo)
                    .filter(
                        func.extract('year', Emprestimo.data_emprestimo) == ano_atual,
                        func.extract('month', Emprestimo.data_emprestimo) == m
                    )
                    .count()
                )
                emprestimos_mes_data.append(qtd)

            
            # BI: top 5 alunos e livros
            top_alunos = (
                db.query(Aluno.nome, func.count(Emprestimo.id).label('qtd'))
                  .join(Emprestimo, Emprestimo.aluno_id==Aluno.id)
                  .group_by(Aluno.id)
                  .order_by(func.count(Emprestimo.id).desc())
                  .limit(5)
                  .all()
            )
            top_livros = (
                db.query(Livro.titulo, func.count(Emprestimo.id).label('qtd'))
                  .join(Emprestimo, Emprestimo.livro_id==Livro.id)
                  .group_by(Livro.id)
                  .order_by(func.count(Emprestimo.id).desc())
                  .limit(5)
                  .all()
            )

        # prepara listas para gráficos
        alunos_labels = [a.nome for a in top_alunos]
        alunos_data   = [a.qtd  for a in top_alunos]
        livros_labels = [l.titulo for l in top_livros]
        livros_data   = [l.qtd     for l in top_livros]
        ano_atual = date.today().year
        
        return render_template(
            'index.html',
            total_alunos=total_alunos,
            total_livros=total_livros,
            disponiveis=disponiveis,
            emprestados=emprestados,
            ativos=ativos,
            atrasados=atrasados,
            top_alunos_labels=alunos_labels,
            top_alunos_data=alunos_data,
            top_livros_labels=livros_labels,
            top_livros_data=livros_data,
            emprestimos_hoje=emprestimos_hoje,
            emprestimos_mes_labels=emprestimos_mes_labels,
            emprestimos_mes_data=emprestimos_mes_data,
            ano_atual=ano_atual
        )

    return app


app = create_app()

# if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=5000, debug=True)
#