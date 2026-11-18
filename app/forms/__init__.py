"""Formulários (Flask-WTF): validação de entrada no servidor + proteção CSRF.

A validação no navegador (HTML5/JS) melhora a experiência, mas a validação que
vale é sempre a do servidor.
"""
from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    EmailField,
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.i18n import get_translations
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)

from app.simulador.regras import CLASSES, COMPRA, VENDA
from app.utils.tempo import ANO_MAXIMO, ANO_MINIMO, data_valida
from app.utils.validadores import senha_forte

OBRIGATORIO = "Campo obrigatório."


def _aparar(valor):
    """Remove espaços nas pontas (comum ao colar e-mails e nomes)."""
    return valor.strip() if isinstance(valor, str) else valor


def _maiusculas(valor):
    return valor.strip().upper() if isinstance(valor, str) else valor


APARAR = [_aparar]


def _senha(form, field):
    if field.data and not senha_forte(field.data):
        raise ValidationError("A senha precisa ter ao menos 8 caracteres, com letras e números.")


def _data_na_faixa(form, field):
    if field.data and not data_valida(field.data):
        raise ValidationError(f"Informe uma data entre {ANO_MINIMO} e {ANO_MAXIMO}.")


class Formulario(FlaskForm):
    """Base de todos os formulários: mensagens padrão do WTForms em português.

    O Flask-WTF só traduz quando o Flask-Babel está instalado; aqui usamos direto o
    catálogo 'pt' que acompanha o próprio WTForms.
    """

    class Meta:
        def get_translations(self, form):
            return get_translations(["pt_BR", "pt"])


# --------------------------------------------------------------------------- autenticação
class LoginForm(Formulario):
    email = EmailField("E-mail", filters=APARAR, validators=[DataRequired(OBRIGATORIO), Email("E-mail inválido.")])
    senha = PasswordField("Senha", validators=[DataRequired(OBRIGATORIO)])
    lembrar = BooleanField("Manter conectado")


class CadastroForm(Formulario):
    nome = StringField(
        "Seu nome", filters=APARAR,
        validators=[DataRequired(OBRIGATORIO), Length(3, 120, "Use entre 3 e 120 caracteres.")],
    )
    email = EmailField(
        "E-mail", filters=APARAR,
        validators=[DataRequired(OBRIGATORIO), Email("E-mail inválido."), Length(max=120)],
    )
    senha = PasswordField("Senha", validators=[DataRequired(OBRIGATORIO), _senha])
    confirmacao = PasswordField(
        "Confirme a senha",
        validators=[DataRequired(OBRIGATORIO), EqualTo("senha", "As senhas não conferem.")],
    )


class AlterarSenhaForm(Formulario):
    senha_atual = PasswordField("Senha atual", validators=[DataRequired(OBRIGATORIO)])
    nova_senha = PasswordField("Nova senha", validators=[DataRequired(OBRIGATORIO), _senha])
    confirmacao = PasswordField(
        "Confirme a nova senha",
        validators=[DataRequired(OBRIGATORIO), EqualTo("nova_senha", "As senhas não conferem.")],
    )


class ExcluirContaForm(Formulario):
    senha = PasswordField("Sua senha", validators=[DataRequired(OBRIGATORIO)])
    confirmacao = StringField(
        "Digite EXCLUIR para confirmar", filters=[_maiusculas],
        validators=[DataRequired(OBRIGATORIO), Regexp(r"^EXCLUIR$", message="Digite exatamente EXCLUIR.")],
    )


class UsuarioForm(Formulario):
    nome = StringField(
        "Nome", filters=APARAR,
        validators=[DataRequired(OBRIGATORIO), Length(3, 120, "Use entre 3 e 120 caracteres.")],
    )
    email = EmailField(
        "E-mail", filters=APARAR,
        validators=[DataRequired(OBRIGATORIO), Email("E-mail inválido."), Length(max=120)],
    )
    perfil = SelectField(
        "Perfil",
        choices=[("INVESTIDOR", "Investidor"), ("ADMIN", "Administrador")],
        validators=[DataRequired(OBRIGATORIO)],
    )
    senha = PasswordField(
        "Senha", validators=[Optional(), _senha], description="Deixe em branco para manter a atual."
    )


# --------------------------------------------------------------------------- simulador
class CarteiraForm(Formulario):
    nome = StringField(
        "Nome da carteira", filters=APARAR,
        validators=[DataRequired(OBRIGATORIO), Length(2, 80, "Use entre 2 e 80 caracteres.")],
    )
    descricao = TextAreaField("Objetivo / descrição", filters=APARAR, validators=[Optional(), Length(max=500)])


class OperacaoForm(Formulario):
    ativo_id = SelectField("Ativo", coerce=int, validators=[DataRequired("Escolha o ativo.")])
    tipo = RadioField(
        "Operação", choices=[(COMPRA, "Compra"), (VENDA, "Venda")], default=COMPRA,
        validators=[DataRequired("Escolha compra ou venda.")],
    )
    data = DateField("Data da operação", validators=[DataRequired("Informe a data."), _data_na_faixa])
    modo = RadioField(
        "Informar por", choices=[("VALOR", "Valor em R$"), ("QUANTIDADE", "Quantidade")], default="VALOR",
    )
    valor = DecimalField("Valor (R$)", places=2, validators=[Optional(), NumberRange(min=0.01, message="Informe um valor maior que zero.")])
    quantidade = DecimalField("Quantidade", places=8, validators=[Optional(), NumberRange(min=0, message="Quantidade inválida.")])
    preco = DecimalField(
        "Preço unitário (R$)", places=8,
        validators=[Optional(), NumberRange(min=0.00000001, message="Preço inválido.")],
        description="Em branco = fechamento do dia (busca automática).",
    )
    taxas = DecimalField(
        "Taxas e custos (R$)", places=2, default=0,
        validators=[Optional(), NumberRange(min=0, message="As taxas não podem ser negativas.")],
    )
    observacao = TextAreaField("Observação", filters=APARAR, validators=[Optional(), Length(max=500)])

    def validate(self, extra_validators=None):
        # Regras que dependem de outro campo (o Optional() dos campos interromperia validadores próprios).
        valido = super().validate(extra_validators)
        if self.modo.data == "VALOR" and not self.valor.data and not self.valor.errors:
            self.valor.errors.append("Informe quanto quer aplicar (ou resgatar) em reais.")
            valido = False
        if self.modo.data == "QUANTIDADE" and not self.quantidade.data and not self.quantidade.errors:
            self.quantidade.errors.append("Informe a quantidade.")
            valido = False
        return valido


class AtivoForm(Formulario):
    ticker = StringField(
        "Código (ticker)", filters=[_maiusculas],
        validators=[DataRequired(OBRIGATORIO), Regexp(r"^[A-Z0-9]{2,12}$", message="Use só letras e números, ex.: PETR4.")],
    )
    nome = StringField("Nome", filters=APARAR, validators=[DataRequired(OBRIGATORIO), Length(2, 120)])
    classe = SelectField("Classe", choices=list(CLASSES.items()))
    simbolo_fonte = StringField(
        "Símbolo na fonte de dados", filters=[_maiusculas],
        validators=[DataRequired(OBRIGATORIO), Regexp(r"^[A-Z0-9.-]{2,30}$", message="Símbolo inválido.")],
        description="Código na fonte de dados (brapi). Normalmente igual ao ticker: PETR4, KNRI11, BTC.",
    )


# --------------------------------------------------------------------------- feedback
class FeedbackForm(Formulario):
    nome_testador = StringField(
        "Seu nome", filters=APARAR,
        validators=[DataRequired(OBRIGATORIO), Length(3, 120, "Use entre 3 e 120 caracteres.")],
    )
    email = EmailField(
        "Seu e-mail", filters=APARAR, validators=[Optional(), Email("E-mail inválido."), Length(max=120)]
    )
    perfil_testador = SelectField(
        "Você é",
        choices=[
            ("Colega de curso", "Colega de curso"),
            ("Profissional de TI", "Profissional de TI"),
            ("Profissional do mercado financeiro", "Profissional do mercado financeiro"),
            ("Investidor", "Investidor"),
            ("Outro", "Outro"),
        ],
    )
    data_teste = DateField("Data do teste", validators=[DataRequired(OBRIGATORIO), _data_na_faixa])
    funcionou = TextAreaField(
        "O que você testou e FUNCIONOU",
        validators=[DataRequired(OBRIGATORIO), Length(5, 5000, "Descreva com ao menos 5 caracteres.")],
    )
    nao_funcionou = TextAreaField(
        "O que você testou e NÃO funcionou (e o que deve ser corrigido)",
        validators=[Optional(), Length(max=5000)],
    )
    nao_testado = TextAreaField(
        "Funcionalidades que você NÃO testou (e por quê)", validators=[Optional(), Length(max=5000)]
    )
    sugestoes = TextAreaField("Sugestões de melhoria", validators=[Optional(), Length(max=5000)])
    nota = RadioField(
        "Nota geral do sistema",
        choices=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")],
        validators=[DataRequired("Escolha uma nota de 1 a 5.")],
    )
    prints = MultipleFileField("Prints das telas (opcional, até 3 imagens de 2 MB)")


class TratativaFeedbackForm(Formulario):
    status = SelectField("Situação")
    tratativa = TextAreaField("Tratativa / correção realizada", validators=[Optional(), Length(max=5000)])
