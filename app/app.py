import calendar
from sqlalchemy import func
from datetime import date, datetime
from config.settings import engine, Base, SessionLocal
from routes.alunos import bp as alunos_bp
from routes.livros import bp as livros_bp
from routes.emprestimos import bp as emprestimos_bp
from models.escola import Escola
from models.aluno import Aluno
from models.livro import Livro
from models.emprestimo import Emprestimo
from flask_login import current_user, LoginManager, login_user, logout_user, login_required
from routes.auth import bp as auth_bp
from models.usuario import Usuario
from flask import Flask, render_template, redirect, url_for, request
from models.acesso import Acesso
from routes.users import bp as users_bp
from flask_wtf import CSRFProtect
import os
from flask import send_from_directory


class CloudflareProxyFix:
    """Corrige REMOTE_ADDR e o esquema quando a app roda atrás de
    Cloudflare → nginx. Usa CF-Connecting-IP (IP real do cliente, garantido
    pela Cloudflare); se ausente, cai para o primeiro X-Forwarded-For. Também
    reflete o X-Forwarded-Proto para request.is_secure funcionar.

    Só afeta log/exibição e o esquema — NENHUMA decisão de segurança depende do
    IP (o lockout de login é por conta, não por IP), então um header forjado
    não abre brecha; no máximo suja o log de acessos.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        cf = environ.get('HTTP_CF_CONNECTING_IP')
        xff = environ.get('HTTP_X_FORWARDED_FOR', '')
        cliente = cf or (xff.split(',')[0].strip() if xff else None)
        if cliente:
            environ['REMOTE_ADDR'] = cliente
        proto = environ.get('HTTP_X_FORWARDED_PROTO')
        if proto:
            environ['wsgi.url_scheme'] = proto.split(',')[0].strip()
        return self.wsgi_app(environ, start_response)


def create_app(testing=False):
    app = Flask(__name__,template_folder='templates',static_folder='static')
    # Em produção (SaaS) a chave vem do .env; nunca versione o valor real.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-me')

    # Confia nos headers de proxy da Cloudflare/nginx (IP real + esquema).
    app.wsgi_app = CloudflareProxyFix(app.wsgi_app)

    # Endurecimento do cookie de sessão (app servido só via HTTPS/Cloudflare).
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,   # JS não lê o cookie (mitiga XSS)
        SESSION_COOKIE_SECURE=True,     # cookie só trafega em HTTPS
        SESSION_COOKIE_SAMESITE='Lax',  # mitiga CSRF em navegação cross-site
        WTF_CSRF_TIME_LIMIT=None,       # token vale enquanto durar a sessão
        # Não exige o header Referer no POST HTTPS: alguns navegadores/políticas
        # de privacidade o removem, e o token + SameSite já protegem contra CSRF.
        WTF_CSRF_SSL_STRICT=False,
    )

    # Em testes, desliga a proteção CSRF (o test_client não envia token).
    if testing:
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

    # Proteção CSRF em TODOS os POST (forms e chamadas AJAX). Os forms enviam
    # o campo oculto {{ csrf_token() }}; o fetch envia o header X-CSRFToken
    # (injetado no base.html). Sem token → 400, mitigando CSRF de verdade.
    csrf = CSRFProtect(app)

    # Cria as tabelas que ainda não existirem (idempotente). Retry porque o
    # MySQL pode não estar pronto quando o app sobe. Em testes o banco é o
    # SQLite montado pelo conftest — não toca no MySQL.
    if not testing:
        import time
        for tentativa in range(20):
            try:
                Base.metadata.create_all(bind=engine)
                break
            except Exception as e:
                if tentativa == 19:
                    raise
                print(f'⏳ Aguardando o banco… ({tentativa+1}/20): {e}', flush=True)
                time.sleep(3)


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


    @app.context_processor
    def inject_atrasados():
        """Nº de empréstimos vencidos (para o badge de atrasados no menu)."""
        if not current_user.is_authenticated:
            return dict(atrasados_count=0)
        try:
            with SessionLocal() as db:
                q = db.query(func.count(Emprestimo.id)).filter(
                    Emprestimo.data_devolucao.is_(None),
                    Emprestimo.data_prevista_devolucao < date.today(),
                )
                if getattr(current_user, 'escola_id', None) is not None:
                    q = q.filter(Emprestimo.escola_id == current_user.escola_id)
                return dict(atrasados_count=q.scalar() or 0)
        except Exception:
            return dict(atrasados_count=0)


    @app.context_processor
    def inject_asset_helpers():
        def static_v(filename):
            """URL do estático com ?v=<mtime> para furar cache do navegador e
            da Cloudflare quando o arquivo muda (evita servir CSS/JS velho)."""
            caminho = os.path.join(app.static_folder, filename)
            try:
                versao = int(os.path.getmtime(caminho))
            except OSError:
                versao = 0
            return url_for('static', filename=filename, v=versao)
        return dict(static_v=static_v)
    
    
    # redireciona home (/) para dashboard, mas só se estiver logado
    @app.before_request
    def require_login():
        # lista de endpoints que não exigem login
        public = ('auth.login', 'auth.logout', 'static')
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
        eid = current_user.escola_id
        with SessionLocal() as db:
            # métricas gerais (escopadas por escola)
            total_alunos   = db.query(Aluno).filter_by(escola_id=eid).count()
            total_livros   = db.query(Livro).filter_by(escola_id=eid).count()
            disponiveis    = db.query(Livro).filter_by(escola_id=eid, situacao='disponível').count()
            emprestados    = db.query(Livro).filter_by(escola_id=eid, situacao='emprestado').count()
            ativos         = db.query(Emprestimo).filter_by(escola_id=eid, data_devolucao=None).count()
            atrasados      = db.query(Emprestimo).filter(
                                 Emprestimo.escola_id==eid,
                                 Emprestimo.data_devolucao==None,
                                 Emprestimo.data_prevista_devolucao<date.today()
                               ).count()
            # empréstimos registrados hoje
            emprestimos_hoje = (
                db.query(Emprestimo)
                .filter(Emprestimo.escola_id==eid,
                        func.date(Emprestimo.data_emprestimo) == date.today())
                .count()
            )

            # empréstimos por mês no ano atual — uma única query agregada
            # (GROUP BY mês) em vez de 12 COUNTs separados.
            ano_atual = date.today().year
            meses = list(range(1, 13))
            emprestimos_mes_labels = [calendar.month_abbr[m] for m in meses]
            linhas_mes = (
                db.query(
                    func.extract('month', Emprestimo.data_emprestimo).label('mes'),
                    func.count(Emprestimo.id)
                )
                .filter(
                    Emprestimo.escola_id == eid,
                    func.extract('year', Emprestimo.data_emprestimo) == ano_atual
                )
                .group_by('mes')
                .all()
            )
            # normaliza a chave para int (o extract do MySQL pode vir como Decimal)
            contagem_mes = {int(mes): qtd for mes, qtd in linhas_mes}
            emprestimos_mes_data = [int(contagem_mes.get(m, 0)) for m in meses]


            # BI: top 5 alunos e livros
            top_alunos = (
                db.query(Aluno.nome, func.count(Emprestimo.id).label('qtd'))
                  .join(Emprestimo, Emprestimo.aluno_id==Aluno.id)
                  .filter(Aluno.escola_id==eid)
                  .group_by(Aluno.id)
                  .order_by(func.count(Emprestimo.id).desc())
                  .limit(5)
                  .all()
            )
            top_livros = (
                db.query(Livro.titulo, func.count(Emprestimo.id).label('qtd'))
                  .join(Emprestimo, Emprestimo.livro_id==Livro.id)
                  .filter(Livro.escola_id==eid)
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