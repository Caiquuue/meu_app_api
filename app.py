from flask_openapi3 import OpenAPI, Info, Tag
from flask import redirect
from urllib.parse import unquote

from sqlalchemy.exc import IntegrityError

from model import Session, Profissional, Conhecimento
from logger import logger
from schemas import *
from flask_cors import CORS

info = Info(title="Minha API", version="1.0.0")
app = OpenAPI(__name__, info=info)
CORS(app)

# definindo tags
home_tag = Tag(name="Documentação", description="Seleção de documentação: Swagger, Redoc ou RapiDoc")
profissional_tag = Tag(name="Profissional", description="Adição, visualização e remoção de profissionais à base")
conhecimento_tag = Tag(name="Conhecimento", description="Adição de um conhecimento à um profissional cadastrado na base")


@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação.
    """
    return redirect('/openapi')


@app.post('/profissional', tags=[profissional_tag],
          responses={"200": ProfissionalViewSchema, "409": ErrorSchema, "400": ErrorSchema})
def add_profissional(form: ProfissionalSchema):
    """Adiciona um novo Profissional à base de dados

    Retorna uma representação dos profissionais e conhecimentos associados.   
    """
    profissional = Profissional(
        nome=form.nome,
        celular=form.celular,
        email=form.email)
    logger.debug(f"Adicionando profissional de nome: '{profissional.nome}'")
    try:
        # criando conexão com a base
        session = Session()
        # adicionando profissional
        session.add(profissional)
        # efetivando o camando de adição de novo item na tabela
        session.commit()
        logger.debug(f"Adicionado profissional de nome: '{profissional.nome}'")
        return apresenta_Profissional(profissional), 200

    except IntegrityError as e:
        # como a duplicidade do nome é a provável razão do IntegrityError
        error_msg = "Profissional de mesmo nome já salvo na base :/"
        logger.warning(f"Erro ao adicionar profissional '{profissional.nome}', {error_msg}")
        return {"mesage": error_msg}, 409
    
    except Exception as e:
        # caso um erro fora do previsto
        error_msg = "Não foi possível salvar novo item :/"
        logger.warning(f"Erro ao adicionar profissional '{profissional.nome}', {error_msg}")
        return {"mesage": error_msg}, 400

@app.get('/profissionais', tags=[profissional_tag],
         responses={"200": ListagemProfissionaisSchema, "404": ErrorSchema})
def get_profissionais():
    """Faz a busca por todos os Profissional cadastrados

    Retorna uma representação da listagem de profissionais.
    """
    logger.debug(f"Coletando profissionais ")
    # criando conexão com a base
    session = Session()
    # fazendo a busca
    profissional = session.query(Profissional).order_by(Profissional.id).all()

    if not profissional:
        # se não há profissionais cadastrados
        return {"profissionais": []}, 200
    else:
        logger.debug(f"%d profissionais econtrados" % len(profissional))
        # retorna a representação de profissional
        print(profissional)
        return apresenta_profissionais(profissional), 200

@app.get('/conhecimentos', tags=[conhecimento_tag],
         responses={"200": ListagemConhecimentoSchema, "404": ErrorSchema})
def get_conhecimento():
    """Faz a busca por todos os conhecimentos cadastrados

    Retorna uma representação da listagem de conhecimentos.
    """
    logger.debug(f"Coletando conhecimentos")
    # criando conexão com a base
    session = Session()
    # fazendo a busca
    conhecimentos = session.query(Conhecimento.nome).distinct().all()

    if not conhecimentos:
        # se não há profissionais cadastrados
        return {"conhecimentos": []}, 200
    else:
        logger.debug(f"%d rodutos econtrados" % len(conhecimentos))
        # retorna a representação de profissional
        print(conhecimentos)
        return apresenta_conhecimento(conhecimentos), 200



@app.get('/profissional', tags=[profissional_tag],
         responses={"200": ProfissionalViewSchema, "404": ErrorSchema})
def get_profissional(query: ConhecimentoBuscaSchema):
    """Faz a busca por um Profissional a partir do id do profissional

    Retorna uma representação dos profissionais e conhecimentos associados.
    """
    # profissional_id = query.id
    conhecimento = query.nome
    
    logger.debug(f"Coletando dados sobre profissional #{conhecimento}")
    # criando conexão com a base
    session = Session()
    # fazendo a busca
    # profissional = session.query(Profissional).filter(Profissional.id == profissional_id).first()

    profissionais = session.query(Profissional) \
        .join(Conhecimento, Profissional.id == Conhecimento.id_profissional) \
        .filter(Conhecimento.nome == conhecimento) \
        .all()

    if not profissionais:
        # se o profissional não foi encontrado
        error_msg = "Profissional não encontrado na base :/"
        logger.warning(f"Erro ao buscar profissional com conhecimento'{conhecimento}', {error_msg}")
        return {"mesage": error_msg}, 404
    else:
        logger.debug(f"Profissional econtrado: '{profissionais}'")
        # retorna a representação de profissional
        return apresenta_profissionais(profissionais), 200
    


@app.delete('/profissional', tags=[profissional_tag],
            responses={"200": ProfissionalDelSchema, "404": ErrorSchema})
def del_profissional(query: ProfissionalBuscaSchema):
    """Deleta um Profissional a partir do nome de profissional informado

    Retorna uma mensagem de confirmação da remoção.
    """
    profissional_nome = unquote(unquote(query.nome))
    print(profissional_nome)
    logger.debug(f"Deletando dados sobre profissional #{profissional_nome}")
    # criando conexão com a base
    session = Session()
    # fazendo a remoção
    count = session.query(Profissional).filter(Profissional.nome == profissional_nome).delete()
    session.commit()

    if count:
        # retorna a representação da mensagem de confirmação
        logger.debug(f"Deletado profissional #{profissional_nome}")
        return {"mesage": "Profissional removido", "id": profissional_nome}
    else:
        # se o profissional não foi encontrado
        error_msg = "Profissional não encontrado na base :/"
        logger.warning(f"Erro ao deletar profissional #'{profissional_nome}', {error_msg}")
        return {"mesage": error_msg}, 404

@app.post('/conhecimento', tags=[conhecimento_tag],
          responses={"200": ConhecimentoViewSchema, "404": ErrorSchema})
def add_conhecimento(form: ConhecimentoSchema):
    """Adiciona de um novo conhecimento à um profissionais cadastrado na base identificado pelo id

    Retorna uma representação dos profissionais e conhecimentos associados.
    """
    profissional_id  = form.id_profissional
    
    logger.debug(f"Adicionando conhecimentos ao profissional #{profissional_id}")
    # criando conexão com a base
    session = Session()
    # fazendo a busca pelo profissional
    profissional = session.query(Profissional).filter(Profissional.id == profissional_id).first()

    if not profissional:
        # se profissional não encontrado
        error_msg = "Profissional não encontrado na base :/"
        logger.warning(f"Erro ao adicionar conhecimento ao profissional '{profissional_id}', {error_msg}")
        return {"mesage": error_msg}, 404

    # criando o conhecimento
    nome = form.nome
    conhecimento = Conhecimento(nome)
    
    # adicionando o conhecimento ao profissional
    profissional.adiciona_conhecimento(conhecimento)
    session.commit()

    logger.debug(f"Adicionado conhecimento ao profissional #{profissional_id}")

    # retorna a representação de profissional
    return apresenta_Profissional(profissional), 200

@app.get('/conhecimentoPorID', tags=[conhecimento_tag],
         responses={"200": ListagemConhecimentoSchema, "404": ErrorSchema})
def get_conhecimentos_profissional(query: ConhecimentoporIDBuscaSchema):
    """Obtém os conhecimentos de um profissional com base no ID do profissional.

    Retorna uma representação dos conhecimentos do profissional.
    """
    profissional = query.id_profissional

    logger.debug(f"Coletando conhecimentos do profissional #{profissional}")
    # criando conexão com a base
    session = Session()
    # fazendo a busca pelo profissional
    conhecimentoprofissional = session.query(Conhecimento).filter(Conhecimento.id_profissional == profissional).order_by(Conhecimento.id_profissional).all()



    logger.debug(f"%d rodutos econtrados" % len(conhecimentoprofissional))
        # retorna a representação de profissional
    print(conhecimentoprofissional)
    return apresenta_conhecimento(conhecimentoprofissional), 200

@app.delete('/conhecimento', tags=[conhecimento_tag],
            responses={"200": ConhecimentoDelSchema, "404": ErrorSchema})
def del_conhecimento(query: ConhecimentoDelSchema):
    """Deleta um Conhecimento a partir do ID do profissional informado

    Retorna uma mensagem de confirmação da remoção.
    """
    profissional_id = query.id_profissional

    logger.debug(f"Deletando conhecimento do profissional #{profissional_id}")
    # criando conexão com a base
    session = Session()
    # fazendo a remoção
    count = session.query(Conhecimento).filter(Conhecimento.id_profissional == profissional_id).delete()
    session.commit()

    if count:
        # retorna a representação da mensagem de confirmação
        logger.debug(f"Deletado conhecimento do profissional #{profissional_id}")
        return {"message": "Conhecimento removido", "id_profissional": profissional_id}
    else:
        # se o conhecimento não foi encontrado
        error_msg = "Conhecimento não encontrado na base :/"
        logger.warning(f"Erro ao deletar conhecimento do profissional #{profissional_id}, {error_msg}")
        return {"message": error_msg}, 404


    