"""Testes do registro de feedback e da validação dos prints enviados."""
import io
from datetime import date

import pytest
from werkzeug.datastructures import FileStorage

from app.services import feedback_service
from app.services.excecoes import RegraNegocioError

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 32


def arquivo(nome, conteudo):
    return FileStorage(stream=io.BytesIO(conteudo), filename=nome)


@pytest.mark.parametrize(
    ("conteudo", "tipo"),
    [(PNG, "image/png"), (JPG, "image/jpeg"), (WEBP, "image/webp"), (b"GIF89a...", "image/gif"), (b"%PDF-1.4", None)],
)
def test_detecta_tipo_pela_assinatura(conteudo, tipo):
    assert feedback_service.detectar_tipo_imagem(conteudo) == tipo


DADOS = {
    "nome_testador": "  Carla Teste ",
    "email": "CARLA@EMAIL.COM",
    "perfil_testador": "Colega de curso",
    "data_teste": date(2026, 11, 20),
    "funcionou": "Criação de carteira e compra de ativos.",
    "nao_funcionou": "",
    "nao_testado": "Área administrativa",
    "sugestoes": None,
    "nota": "4",
}


def test_registra_feedback_com_prints(app):
    fb = feedback_service.registrar_feedback(
        DADOS, [arquivo("tela 1.png", PNG), arquivo("", b""), arquivo("t2.jpg", JPG)], "Mozilla/5.0"
    )
    assert fb.id and fb.nome_testador == "Carla Teste" and fb.email == "carla@email.com"
    assert fb.nao_funcionou is None and fb.nota == 4 and fb.status == "NOVO"
    assert [(a.nome_arquivo, a.tipo_mime) for a in fb.anexos] == [("tela_1.png", "image/png"), ("t2.jpg", "image/jpeg")]


def test_rejeita_arquivo_que_nao_e_imagem(app):
    with pytest.raises(RegraNegocioError, match="não é uma imagem"):
        feedback_service.registrar_feedback(DADOS, [arquivo("virus.png", b"MZ\x90\x00 executavel")])


def test_rejeita_mais_de_tres_imagens(app):
    with pytest.raises(RegraNegocioError, match="no máximo 3"):
        feedback_service.preparar_anexos([arquivo(f"{i}.png", PNG) for i in range(4)])


def test_rejeita_imagem_grande(app):
    grande = PNG + b"\x00" * (2 * 1024 * 1024)
    with pytest.raises(RegraNegocioError, match="passa de 2 MB"):
        feedback_service.preparar_anexos([arquivo("grande.png", grande)])


def test_tratativa(app):
    fb = feedback_service.registrar_feedback(DADOS)
    feedback_service.atualizar_tratativa(fb, "CORRIGIDO", "  Ajustado na versão 1.1 ")
    assert (fb.status, fb.tratativa, fb.status_descricao) == ("CORRIGIDO", "Ajustado na versão 1.1", "Corrigido")
    with pytest.raises(RegraNegocioError):
        feedback_service.atualizar_tratativa(fb, "XYZ", None)
