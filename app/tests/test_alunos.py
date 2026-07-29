import io
from models.escola import Escola
from models.aluno import Aluno
from models.emprestimo import Emprestimo
from models.livro import Livro
from models.log_atividade import LogAtividade


def _aluno(session, codigo, **kw):
    eid = session.query(Escola).first().id
    a = Aluno(escola_id=eid, codigo=codigo, nome=kw.pop('nome', 'Fulano'),
              tipo=kw.pop('tipo', 'aluno'), **kw)
    session.add(a); session.commit()
    return a


def test_novo_aluno_cria(client, session):
    resp = client.post('/alunos/novo', data={
        'codigo': 'A001', 'nome': 'Maria', 'tipo': 'aluno', 'turma': '5A',
    })
    assert resp.status_code == 302
    aluno = session.query(Aluno).filter_by(codigo='A001').one()
    assert aluno.nome == 'Maria' and aluno.turma == '5A'
    log = session.query(LogAtividade).filter_by(acao='criar', entidade='aluno').first()
    assert log is not None and 'Maria' in log.descricao


def test_novo_aluno_codigo_duplicado_nao_quebra(client, session):
    _aluno(session, 'DUP1')
    resp = client.post('/alunos/novo', data={
        'codigo': 'DUP1', 'nome': 'Outra Pessoa', 'tipo': 'aluno', 'turma': '',
    })
    assert resp.status_code == 302  # redireciona com flash de erro, não 500
    assert session.query(Aluno).filter_by(codigo='DUP1').count() == 1


def test_professor_nao_tem_turma(client, session):
    resp = client.post('/alunos/novo', data={
        'codigo': 'PR01', 'nome': 'Professor X', 'tipo': 'professor', 'turma': '5A',
    })
    assert resp.status_code == 302
    prof = session.query(Aluno).filter_by(codigo='PR01').one()
    assert prof.turma == ''


def test_editar_aluno_atualiza(client, session):
    _aluno(session, 'E001', nome='Nome Antigo', turma='1A')
    resp = client.post('/alunos/E001/editar', data={
        'nome': 'Nome Novo', 'tipo': 'aluno', 'turma': '2B',
    })
    assert resp.status_code == 302
    session.expire_all()
    aluno = session.query(Aluno).filter_by(codigo='E001').one()
    assert aluno.nome == 'Nome Novo' and aluno.turma == '2B'


def test_deletar_aluno_sem_emprestimo(client, session):
    _aluno(session, 'D001', nome='Vai Sair')
    resp = client.post('/alunos/D001/deletar')
    assert resp.status_code == 302
    assert session.query(Aluno).filter_by(codigo='D001').count() == 0
    log = session.query(LogAtividade).filter_by(acao='excluir', entidade='aluno').first()
    assert log is not None


def test_deletar_aluno_com_emprestimo_aberto_bloqueia(client, session):
    from datetime import date
    aluno = _aluno(session, 'D002', nome='Com Livro')
    eid = session.query(Escola).first().id
    livro = Livro(escola_id=eid, codigo='LB01', titulo='T', autor='', categoria='',
                  situacao='emprestado')
    session.add(livro); session.commit()
    session.add(Emprestimo(escola_id=eid, aluno_id=aluno.id, livro_id=livro.id,
                            data_emprestimo=date.today(), data_prevista_devolucao=date.today()))
    session.commit()

    resp = client.post('/alunos/D002/deletar')
    assert resp.status_code == 302
    # NÃO foi excluído — bloqueado por empréstimo em aberto
    assert session.query(Aluno).filter_by(codigo='D002').count() == 1


def test_listar_alunos_filtro_tipo(client, session):
    _aluno(session, 'AL01', nome='Um Aluno', tipo='aluno')
    _aluno(session, 'PR02', nome='Um Professor', tipo='professor')
    resp = client.get('/alunos/listar?tipo=professor')
    html = resp.get_data(as_text=True)
    assert 'Um Professor' in html and 'Um Aluno' not in html


def test_importar_alunos_csv(client, session):
    csv_content = 'codigo,nome,turma,tipo\n1001,Pessoa Importada,3C,aluno\n'
    data = {'file': (io.BytesIO(csv_content.encode('utf-8')), 'alunos.csv')}
    resp = client.post('/alunos/importar', data=data, content_type='multipart/form-data')
    assert resp.status_code == 302
    aluno = session.query(Aluno).filter_by(codigo='1001').one()
    assert aluno.nome == 'Pessoa Importada'


def test_aluno_de_outra_escola_nao_aparece(client, session):
    outra = Escola(nome='Outra Escola')
    session.add(outra); session.commit()
    session.add(Aluno(escola_id=outra.id, codigo='O001', nome='De Outra Escola', tipo='aluno'))
    session.commit()

    resp = client.get('/alunos/listar')
    assert 'De Outra Escola' not in resp.get_data(as_text=True)

    r = client.post('/alunos/O001/editar', data={'nome': 'Hackeado', 'tipo': 'aluno'})
    assert r.status_code == 302
    session.expire_all()
    assert session.query(Aluno).filter_by(codigo='O001').one().nome == 'De Outra Escola'
