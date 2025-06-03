import json
import pytest
from models.aluno import Aluno
from models.livro import Livro
from models.emprestimo import Emprestimo

def setup_entities(session):
    aluno = Aluno(codigo='A001', nome='Fulano', turma='1A', barcode_img='A001.png')
    livro = Livro(codigo='L001', titulo='Teste', autor='Autor', ano_publicacao=2020,
                  categoria='X', situacao='disponível', barcode_img='L001.png')
    session.add_all([aluno, livro])
    session.commit()
    return aluno, livro

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
    # tenta de novo
    resp2 = client.post('/emprestimos/', json={'codigo_aluno':aluno.codigo,'codigo_livro':livro.codigo})
    assert resp2.status_code == 409
    assert 'Livro não está disponível' in resp2.get_json()['error']

def test_devolucao_sucesso(client, session):
    aluno, livro = setup_entities(session)
    # cria empréstimo
    resp = client.post('/emprestimos/', json={'codigo_aluno':aluno.codigo,'codigo_livro':livro.codigo})
    emp_id = resp.get_json()['id']
    # devolve
    resp2 = client.post('/emprestimos/devolucao', json={'codigo_livro': livro.codigo})
    assert resp2.status_code == 200
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
