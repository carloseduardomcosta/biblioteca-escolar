import json
import pytest
from models.escola import Escola
from models.aluno import Aluno
from models.livro import Livro
from models.emprestimo import Emprestimo

def setup_entities(session):
    # usa a escola (tenant) criada pela fixture — multi-tenant exige escola_id
    eid = session.query(Escola).first().id
    aluno = Aluno(escola_id=eid, codigo='A001', nome='Fulano', turma='1A',
                  barcode_img='A001.png')
    livro = Livro(escola_id=eid, codigo='L001', titulo='Teste', autor='Autor',
                  ano_publicacao=2020, categoria='X', situacao='disponível',
                  barcode_img='L001.png')
    session.add_all([aluno, livro])
    session.commit()
    return aluno, livro


# As rotas alteram os registros por OUTRA sessão/conexão. Depois de chamar a
# rota é preciso expirar o identity-map da sessão de teste para reler do banco
# (senão ela devolve o valor antigo já carregado ao montar o payload do POST).

def test_criar_emprestimo_sucesso(client, session):
    aluno, livro = setup_entities(session)
    resp = client.post('/emprestimos/', json={
        'codigo_aluno': aluno.codigo,
        'codigo_livro': livro.codigo,
        'dias': 5
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['message'] == 'Empréstimo registrado'
    session.expire_all()          # relê o que a rota gravou noutra conexão
    # verifica no BD
    emp = session.query(Emprestimo).filter_by(id=data['id']).one()
    assert emp.aluno_id == aluno.id and emp.livro_id == livro.id
    # livro deve ter mudado de situação
    livro_db = session.query(Livro).filter_by(id=livro.id).one()
    assert livro_db.situacao == 'emprestado'

def test_emprestimo_livro_indisponivel(client, session):
    aluno, livro = setup_entities(session)
    # primeiro empréstimo
    client.post('/emprestimos/', json={'codigo_aluno':aluno.codigo,'codigo_livro':livro.codigo})
    # tenta de novo → 409 com code='unavailable' (fonte da verdade = empréstimo ativo)
    resp2 = client.post('/emprestimos/', json={'codigo_aluno':aluno.codigo,'codigo_livro':livro.codigo})
    assert resp2.status_code == 409
    assert resp2.get_json()['code'] == 'unavailable'

def test_devolucao_sucesso(client, session):
    aluno, livro = setup_entities(session)
    # cria empréstimo
    resp = client.post('/emprestimos/', json={'codigo_aluno':aluno.codigo,'codigo_livro':livro.codigo})
    emp_id = resp.get_json()['id']
    # devolve
    resp2 = client.post('/emprestimos/devolucao', json={'codigo_livro': livro.codigo})
    assert resp2.status_code == 200
    session.expire_all()          # relê o que a rota gravou noutra conexão
    # verifica data_devolucao preenchida
    emp = session.query(Emprestimo).filter_by(id=emp_id).one()
    assert emp.data_devolucao is not None
    # livro volta a ficar disponível
    livro_db = session.query(Livro).filter_by(id=livro.id).one()
    assert livro_db.situacao == 'disponível'

def test_listar_emprestimos_json(client, session):
    aluno, livro = setup_entities(session)
    client.post('/emprestimos/', json={'codigo_aluno':aluno.codigo,'codigo_livro':livro.codigo})
    resp = client.get('/emprestimos/')
    assert resp.status_code == 200
    lst = resp.get_json()
    assert isinstance(lst, list) and lst[0]['aluno'] == aluno.codigo


# ── Política por papel: professor pega qualquer livro; aluno só 🟢 ──

def _pessoa(session, codigo, tipo='aluno'):
    eid = session.query(Escola).first().id
    p = Aluno(escola_id=eid, codigo=codigo, nome='X', tipo=tipo, barcode_img=codigo + '.png')
    session.add(p); session.commit()
    return p

def _livro(session, codigo, politica):
    eid = session.query(Escola).first().id
    l = Livro(escola_id=eid, codigo=codigo, titulo='T', autor='A', categoria='X',
              situacao='disponível', politica=politica, barcode_img=codigo + '.png')
    session.add(l); session.commit()
    return l

def test_professor_pega_livro_restrito(client, session):
    _pessoa(session, 'P001', 'professor')
    _livro(session, 'R001', 'restrito')
    r = client.post('/emprestimos/', json={'codigo_aluno': 'P001', 'codigo_livro': 'R001'})
    assert r.status_code == 201

def test_professor_pega_livro_consulta(client, session):
    _pessoa(session, 'P002', 'professor')
    _livro(session, 'C001', 'consulta')
    r = client.post('/emprestimos/', json={'codigo_aluno': 'P002', 'codigo_livro': 'C001'})
    assert r.status_code == 201

def test_aluno_nao_pega_livro_restrito(client, session):
    _pessoa(session, 'A100', 'aluno')
    _livro(session, 'R002', 'restrito')
    r = client.post('/emprestimos/', json={'codigo_aluno': 'A100', 'codigo_livro': 'R002'})
    assert r.status_code == 409
    assert 'professor' in r.get_json()['error'].lower()

def test_aluno_nao_pega_livro_consulta(client, session):
    _pessoa(session, 'A101', 'aluno')
    _livro(session, 'C002', 'consulta')
    r = client.post('/emprestimos/', json={'codigo_aluno': 'A101', 'codigo_livro': 'C002'})
    assert r.status_code == 409


# ── Prazo padrão por papel, renovação e fonte da verdade ──

def _dias_ate(iso):
    from datetime import date
    y, m, d = map(int, iso.split('-'))
    return (date(y, m, d) - date.today()).days

def test_prazo_padrao_por_tipo(client, session):
    _pessoa(session, 'A200', 'aluno')
    _pessoa(session, 'P200', 'professor')
    _livro(session, 'L200', 'emprestavel')
    _livro(session, 'L201', 'emprestavel')
    ra = client.post('/emprestimos/', json={'codigo_aluno': 'A200', 'codigo_livro': 'L200'})
    rp = client.post('/emprestimos/', json={'codigo_aluno': 'P200', 'codigo_livro': 'L201'})
    assert _dias_ate(ra.get_json()['data_prevista']) == 7    # aluno
    assert _dias_ate(rp.get_json()['data_prevista']) == 30   # professor

def test_data_prevista_explicita_prevalece(client, session):
    _pessoa(session, 'A210', 'aluno')
    _livro(session, 'L210', 'emprestavel')
    r = client.post('/emprestimos/', json={'codigo_aluno': 'A210', 'codigo_livro': 'L210',
                                           'data_prevista': '2099-12-31'})
    assert r.get_json()['data_prevista'] == '2099-12-31'

def test_policy_tem_code(client, session):
    _pessoa(session, 'A220', 'aluno')
    _livro(session, 'R220', 'restrito')
    r = client.post('/emprestimos/', json={'codigo_aluno': 'A220', 'codigo_livro': 'R220'})
    assert r.status_code == 409 and r.get_json()['code'] == 'policy'

def test_renovar_estende_prazo(client, session):
    _pessoa(session, 'A230', 'aluno')
    _livro(session, 'L230', 'emprestavel')
    client.post('/emprestimos/', json={'codigo_aluno': 'A230', 'codigo_livro': 'L230',
                                       'data_prevista': '2000-01-01'})
    r = client.post('/emprestimos/renovar', json={'codigo_livro': 'L230', 'dias': 10})
    assert r.status_code == 200
    assert _dias_ate(r.get_json()['nova_data']) == 10

def test_renovar_livro_nao_emprestado(client, session):
    _livro(session, 'L240', 'emprestavel')
    r = client.post('/emprestimos/renovar', json={'codigo_livro': 'L240'})
    assert r.status_code == 404 and r.get_json()['code'] == 'not_lent'

def test_devolucao_livro_nao_emprestado(client, session):
    _livro(session, 'L250', 'emprestavel')
    r = client.post('/emprestimos/devolucao', json={'codigo_livro': 'L250'})
    assert r.status_code == 404 and r.get_json()['code'] == 'not_lent'

def test_obter_livro_estado(client, session):
    _pessoa(session, 'A260', 'aluno')
    _livro(session, 'L260', 'emprestavel')
    # disponível
    d = client.get('/emprestimos/obter_livro/L260').get_json()
    assert d['disponivel'] is True and 'emprestimo' not in d
    # após emprestar → emprestado, com dados do portador
    client.post('/emprestimos/', json={'codigo_aluno': 'A260', 'codigo_livro': 'L260'})
    e = client.get('/emprestimos/obter_livro/L260').get_json()
    assert e['disponivel'] is False
    assert e['emprestimo']['aluno_codigo'] == 'A260'
