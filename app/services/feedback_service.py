"""Registro e tratamento dos feedbacks dos testadores (Situação-Problema 3)."""
from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import FeedbackAnexo, FeedbackTeste
from app.services.excecoes import RegraNegocioError

# Assinaturas (magic numbers) para não confiar só na extensão/Content-Type enviados.
_ASSINATURAS = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}


def detectar_tipo_imagem(conteudo: bytes) -> str | None:
    for assinatura, tipo in _ASSINATURAS.items():
        if conteudo.startswith(assinatura):
            return tipo
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "image/webp"
    return None


def preparar_anexos(arquivos) -> list[FeedbackAnexo]:
    """Valida quantidade, tamanho e tipo real dos prints enviados."""
    arquivos = [a for a in (arquivos or []) if a and a.filename]
    limite_qtd = current_app.config["ANEXO_QTD_MAX"]
    limite_tamanho = current_app.config["ANEXO_TAMANHO_MAX"]
    permitidos = current_app.config["ANEXO_TIPOS_PERMITIDOS"]

    if len(arquivos) > limite_qtd:
        raise RegraNegocioError(f"Envie no máximo {limite_qtd} imagens.", campo="prints")

    anexos = []
    for arquivo in arquivos:
        conteudo = arquivo.read()
        nome = secure_filename(arquivo.filename) or "print"
        if len(conteudo) > limite_tamanho:
            raise RegraNegocioError(
                f"A imagem “{nome}” passa de {limite_tamanho // (1024 * 1024)} MB.", campo="prints"
            )
        tipo = detectar_tipo_imagem(conteudo)
        if tipo not in permitidos:
            raise RegraNegocioError(
                f"O arquivo “{nome}” não é uma imagem válida (use PNG, JPG, WEBP ou GIF).",
                campo="prints",
            )
        anexos.append(
            FeedbackAnexo(
                nome_arquivo=nome, tipo_mime=tipo, tamanho_bytes=len(conteudo), conteudo=conteudo
            )
        )
    return anexos


def registrar_feedback(dados: dict, arquivos=None, navegador: str | None = None) -> FeedbackTeste:
    anexos = preparar_anexos(arquivos)
    feedback = FeedbackTeste(
        nome_testador=dados["nome_testador"].strip(),
        email=(dados.get("email") or "").strip().lower() or None,
        perfil_testador=(dados.get("perfil_testador") or "").strip() or None,
        data_teste=dados["data_teste"],
        funcionou=dados["funcionou"].strip(),
        nao_funcionou=(dados.get("nao_funcionou") or "").strip() or None,
        nao_testado=(dados.get("nao_testado") or "").strip() or None,
        sugestoes=(dados.get("sugestoes") or "").strip() or None,
        nota=int(dados["nota"]),
        navegador=(navegador or "")[:255] or None,
        anexos=anexos,
    )
    db.session.add(feedback)
    db.session.commit()
    return feedback


def atualizar_tratativa(feedback: FeedbackTeste, status: str, tratativa: str | None) -> None:
    if status not in FeedbackTeste.STATUS:
        raise RegraNegocioError("Status inválido.")
    feedback.status = status
    feedback.tratativa = (tratativa or "").strip() or None
    db.session.commit()
