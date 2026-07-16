#!/usr/bin/env python3
"""
populate.py — Plataforma Web de Dados Institucionais - UnB
=============================================================
Cria via endpoints REST:
  • 10 Categorias temáticas com ícones
  • 4 Pipelines com os scripts Python reais
  • 10 Painéis vinculados às categorias (com embed links e UUIDs)
  • 6 Sugestões de diferentes tipos

Uso:
    python populate.py
    python populate.py --base-url http://localhost:5042
    python populate.py --base-url http://localhost:5042 --email admin@unb.br --senha Admin123!
    python populate.py --somente-sugestoes    # só cria sugestões
"""

import argparse
import mimetypes
import sys
import time
import uuid
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERRO: Instale o 'requests': pip install requests")
    sys.exit(1)

# ─────────────────────────── configuração padrão ────────────────────────────

DEFAULT_BASE_URL = "http://localhost:5042"
DEFAULT_EMAIL    = "admin@unb.br"
DEFAULT_SENHA    = "Admin123!"

REPO_ROOT   = Path(__file__).parent
ICONS_DIR   = REPO_ROOT / "docs" / "icons"
PIPELINE_DIR = REPO_ROOT / "docs" / "pipelines"

# ─────────────────────────── dados das categorias ────────────────────────────

CATEGORIAS = [
    {
        "nome": "Graduação",
        "descricao": (
            "Dados sobre cursos de graduação, matrículas, turmas e "
            "desempenho acadêmico dos discentes da UnB."
        ),
        "icone": "graduated.svg",
        "sort_ordem": 1,
    },
    {
        "nome": "Pós-Graduação",
        "descricao": (
            "Informações sobre programas de pós-graduação, egressos, "
            "dissertações e teses da universidade."
        ),
        "icone": "graduated-2.svg",
        "sort_ordem": 9,
    },
    {
        "nome": "Restaurante Universitário",
        "descricao": (
            "Estatísticas de refeições servidas, tipo de cardápio e "
            "períodos de funcionamento dos restaurantes da UnB."
        ),
        "icone": "restaurant-2.svg",
        "sort_ordem": 3,
    },
    {
        "nome": "Servidores",
        "descricao": (
            "Dados sobre o corpo de servidores técnico-administrativos "
            "e docentes da universidade."
        ),
        "icone": "teacher.svg",
        "sort_ordem": 4,
    },
    {
        "nome": "Pesquisa e Laboratórios",
        "descricao": (
            "Panorama das atividades de pesquisa, grupos e laboratórios "
            "ativos na UnB."
        ),
        "icone": "laboratory.svg",
        "sort_ordem": 5,
    },
    {
        "nome": "Biblioteca",
        "descricao": (
            "Acervo, empréstimos e indicadores de uso das bibliotecas "
            "do sistema BCE/UnB."
        ),
        "icone": "library.png",
        "sort_ordem": 6,
    },
    {
        "nome": "Finanças e Orçamento",
        "descricao": (
            "Execução orçamentária, receitas, despesas e investimentos "
            "da universidade."
        ),
        "icone": "financial.svg",
        "sort_ordem": 7,
    },
    {
        "nome": "Extensão e Comunidade",
        "descricao": (
            "Projetos de extensão, ações comunitárias e impacto social "
            "das iniciativas da UnB."
        ),
        "icone": "helping.svg",
        "sort_ordem": 8,
    },
    {
        "nome": "Processos Seletivos",
        "descricao": (
            "Resultados e estatísticas dos processos seletivos, ENEM e "
            "transferências para ingresso na UnB."
        ),
        "icone": "searching.svg",
        "sort_ordem": 2,
    },
    {
        "nome": "Institucional",
        "descricao": (
            "Visão geral da universidade: histórico, estrutura acadêmica, "
            "campus e indicadores institucionais."
        ),
        "icone": "university.svg",
        "sort_ordem": 10,
    },
]

# ─────────────────────────── dados dos pipelines ────────────────────────────

def ler_script(nome_arquivo: str) -> str:
    caminho = PIPELINE_DIR / nome_arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Script não encontrado: {caminho}")
    return caminho.read_text(encoding="utf-8")


PIPELINES = [
    {
        "nome": "Discentes Ativos",
        "descricao": (
            "Processa a lista de discentes ativos, normaliza nomes, "
            "cursos e matrículas, valida registros e gera tabelas "
            "silver (individual) e gold (agregada por curso e ano)."
        ),
        "script_arquivo": "lista_de_discentes_ativos.py",
    },
    {
        "nome": "Dados do Restaurante Universitário",
        "descricao": (
            "Normaliza e carrega os dados de refeições do RU, "
            "tipando colunas de período e quantidade e "
            "propagando para as camadas silver e gold."
        ),
        "script_arquivo": "pipeline_dados_ru.py",
    },
    {
        "nome": "Egressos da UnB",
        "descricao": (
            "Processa registros de egressos, calcula semestres cursados, "
            "classifica o tempo de conclusão e produz distribuições "
            "temporais e por classificação nas camadas silver e gold."
        ),
        "script_arquivo": "pipeline_egressos_unb.py",
    },
    {
        "nome": "Relatório de Turmas",
        "descricao": (
            "Normaliza o relatório de turmas, extrai indicadores de "
            "aprovação e MFA por componente curricular e produz "
            "resumos agregados por departamento."
        ),
        "script_arquivo": "pipeline_relatorio_turmas.py",
    },
]

# ─────────────────────────── dados dos painéis ────────────────────────────
# Os UUIDs de embed são provisórios (serão substituídos pelos reais do Superset).
# Os GraphEmbedLinks seguem o padrão de guest-token do Superset configurado.

SUPERSET_BASE = "http://localhost:8088"

PAINEIS = [
    # Graduação (categoria índice 0)
    {
        "nome": "Discentes Ativos por Curso",
        "descricao": (
            "Visualização interativa da distribuição de discentes ativos "
            "por curso, unidade, grau e turno na UnB."
        ),
        "categoria_idx": 0,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 1,
    },
    {
        "nome": "Evolução de Matrículas por Ano",
        "descricao": (
            "Série histórica do total de matrículas ativas por ano "
            "e modalidade de curso na graduação."
        ),
        "categoria_idx": 0,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 2,
    },
    # Pós-Graduação (categoria índice 1)
    {
        "nome": "Egressos por Ano de Formatura",
        "descricao": (
            "Distribuição anual de egressos da UnB com média de "
            "semestres cursados e classificação de tempo de conclusão."
        ),
        "categoria_idx": 1,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 1,
    },
    {
        "nome": "Classificação de Tempo de Conclusão",
        "descricao": (
            "Proporção de egressos por categoria: no prazo, leve atraso, "
            "atrasado e grande atraso."
        ),
        "categoria_idx": 1,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 2,
    },
    # Restaurante Universitário (categoria índice 2)
    {
        "nome": "Refeições Servidas por Período",
        "descricao": (
            "Quantidade de refeições servidas no RU segmentadas por "
            "tipo de refeição e período letivo."
        ),
        "categoria_idx": 2,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 1,
    },
    # Graduação — relatório de turmas (categoria índice 0)
    {
        "nome": "Desempenho por Componente Curricular",
        "descricao": (
            "Taxa de aprovação e média final por componente curricular, "
            "permitindo identificar disciplinas com maior reprovação."
        ),
        "categoria_idx": 0,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 3,
    },
    {
        "nome": "Resumo de Turmas por Departamento",
        "descricao": (
            "Visão consolidada por departamento: total de alunos, "
            "aprovados, MFA média e taxa de aprovação."
        ),
        "categoria_idx": 0,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 4,
    },
    # Institucional (categoria índice 9)
    {
        "nome": "Painel Institucional da UnB",
        "descricao": (
            "Indicadores gerais da universidade: número de cursos, "
            "discentes, servidores e unidades acadêmicas."
        ),
        "categoria_idx": 9,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 1,
    },
    # Pesquisa (categoria índice 4)
    {
        "nome": "Grupos de Pesquisa Ativos",
        "descricao": (
            "Mapeamento dos grupos de pesquisa cadastrados, "
            "por área do conhecimento e unidade acadêmica."
        ),
        "categoria_idx": 4,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 1,
    },
    # Finanças (categoria índice 6)
    {
        "nome": "Execução Orçamentária Anual",
        "descricao": (
            "Acompanhamento da execução do orçamento da UnB: "
            "dotação, empenho, liquidação e pagamento."
        ),
        "categoria_idx": 6,
        "embed_uuid": str(uuid.uuid4()),
        "sort_ordem": 1,
    },
]

# ─────────────────────────── dados das sugestões ────────────────────────────

SUGESTOES = [
    {
        "tipo": "Sugestao",
        "titulo": "Adicionar painel de evasão estudantil",
        "descricao": (
            "Seria muito útil ter um painel que mostre as taxas de evasão "
            "por curso, semestre e perfil socioeconômico dos estudantes, "
            "permitindo identificar grupos de risco e orientar políticas de permanência."
        ),
        "nome_contato": "Maria Silva",
        "email_contato": "maria.silva@aluno.unb.br",
    },
    {
        "tipo": "Sugestao",
        "titulo": "Incluir dados de assistência estudantil",
        "descricao": (
            "Gostaria de sugerir a criação de uma categoria específica para "
            "assistência estudantil com dados sobre bolsas, auxílios e atendimento "
            "psicossocial, contribuindo para a transparência das ações de suporte."
        ),
        "nome_contato": "João Pereira",
        "email_contato": "joao.pereira@aluno.unb.br",
    },
    {
        "tipo": "Erro",
        "titulo": "Gráfico de matrículas exibindo valores zerados",
        "descricao": (
            "Ao acessar o painel de discentes ativos, o gráfico de barras "
            "mostra zero matrículas para todos os cursos do período 2023/2. "
            "O problema ocorre apenas nesse período específico; os demais "
            "aparecem corretamente."
        ),
        "nome_contato": "Carlos Lima",
        "email_contato": "carlos.lima@unb.br",
    },
    {
        "tipo": "Relato",
        "titulo": "Plataforma utilizada em trabalho de conclusão de curso",
        "descricao": (
            "Gostaria de relatar que a plataforma foi fundamental para meu TCC "
            "sobre análise do desempenho acadêmico na UnB. Os dados abertos e "
            "os painéis interativos facilitaram muito a coleta e visualização "
            "das informações necessárias para a pesquisa."
        ),
        "nome_contato": "Ana Rodrigues",
        "email_contato": "ana.rodrigues@aluno.unb.br",
    },
    {
        "tipo": "Sugestao",
        "titulo": "Exportação de dados em formato CSV e Excel",
        "descricao": (
            "Seria muito útil disponibilizar a opção de exportar os dados "
            "exibidos nos painéis em formatos abertos como CSV e Excel, "
            "facilitando análises externas por pesquisadores e estudantes."
        ),
        "nome_contato": None,
        "email_contato": None,
    },
    {
        "tipo": "Erro",
        "titulo": "Página de categorias não carrega no celular",
        "descricao": (
            "Em dispositivos móveis com tela menor que 400px, a grade de "
            "categorias da página inicial fica sobreposta e os ícones "
            "aparecem cortados, impossibilitando a navegação correta "
            "entre as seções da plataforma."
        ),
        "nome_contato": "Pedro Souza",
        "email_contato": "pedro.souza@unb.br",
    },
]

# ─────────────────────────── helpers HTTP ────────────────────────────────────

class PopulateClient:
    def __init__(self, base_url: str, email: str, senha: str):
        self.base = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.token: str | None = None
        self._login(email, senha)

    def _login(self, email: str, senha: str) -> None:
        url = f"{self.base}/Usuario/login"
        resp = self.session.post(url, json={"Email": email, "Senha": senha}, timeout=15)
        if resp.status_code != 200:
            print(f"ERRO: Falha no login ({resp.status_code}): {resp.text[:200]}")
            sys.exit(1)
        data = resp.json()
        self.token = data["accessToken"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        print(f"Login realizado como {email}")

    def post_json(self, path: str, payload: dict, tentativas: int = 3) -> dict:
        ultimo_erro = None
        for n in range(tentativas):
            try:
                resp = self.session.post(
                    f"{self.base}/{path}", json=payload, timeout=30
                )
                resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                ultimo_erro = exc
                if n < tentativas - 1:
                    time.sleep(2)
        raise ultimo_erro  # type: ignore[misc]

    def post_form(self, path: str, data: dict, files: dict | None = None, tentativas: int = 3) -> dict:
        ultimo_erro = None
        for n in range(tentativas):
            try:
                resp = self.session.post(
                    f"{self.base}/{path}", data=data, files=files, timeout=30
                )
                if not resp.ok:
                    print(f"   AVISO: {resp.status_code}: {resp.text[:300]}")
                    resp.raise_for_status()
                return resp.json()
            except Exception as exc:
                ultimo_erro = exc
                if n < tentativas - 1:
                    time.sleep(2)
        raise ultimo_erro  # type: ignore[misc]


# ─────────────────────────── lógica de populate ──────────────────────────────

def criar_categorias(client: PopulateClient) -> list[dict]:
    print("\nCriando categorias...")
    criadas = []
    for cat in CATEGORIAS:
        icone_path = ICONS_DIR / cat["icone"]
        if not icone_path.exists():
            print(f"   AVISO: Icone nao encontrado: {icone_path} -- pulando imagem")
            files = None
        else:
            mime, _ = mimetypes.guess_type(str(icone_path))
            mime = mime or "image/svg+xml"
            files = {"Imagem": (icone_path.name, icone_path.read_bytes(), mime)}

        form_data = {
            "Nome": cat["nome"],
            "Descricao": cat["descricao"],
            "SortOrdem": str(cat["sort_ordem"]),
        }

        resultado = client.post_form("Categoria", form_data, files)
        criadas.append(resultado)
        print(f"   OK  [{resultado['id']}] {resultado['nome']}")

    return criadas


def criar_pipelines(client: PopulateClient) -> list[dict]:
    print("\nCriando pipelines...")
    criados = []
    for pipe in PIPELINES:
        script = ler_script(pipe["script_arquivo"])
        payload = {
            "Nome": pipe["nome"],
            "Descricao": pipe["descricao"],
            "ScriptPython": script,
        }
        resultado = client.post_json("Pipeline", payload)
        criados.append(resultado)
        print(f"   OK  [{resultado['id']}] {resultado['nome']}")

    return criados


def criar_paineis(client: PopulateClient, categorias: list[dict]) -> list[dict]:
    print("\nCriando paineis...")
    criados = []
    for painel in PAINEIS:
        cat = categorias[painel["categoria_idx"]]
        embed_uuid = painel["embed_uuid"]
        # Link de incorporação provisório baseado no UUID (substituir pelo real do Superset)
        embed_link = f"{SUPERSET_BASE}/superset/dashboard/{embed_uuid}/?standalone=3"

        payload = {
            "Nome": painel["nome"],
            "Descricao": painel["descricao"],
            "GraphEmbedLink": embed_link,
            "EmbedDashboardUuid": embed_uuid,
            "SortOrdem": painel["sort_ordem"],
            "CategoriaId": cat["id"],
        }
        resultado = client.post_json("Painel", payload)
        criados.append(resultado)
        print(
            f"   OK  [{resultado['id']}] {resultado['nome']} "
            f"-> categoria '{cat['nome']}'"
        )

    return criados


def criar_sugestoes(client: PopulateClient) -> list[dict]:
    print("\nCriando sugestoes...")
    criadas = []
    for sug in SUGESTOES:
        payload = {
            "Tipo": sug["tipo"],
            "Titulo": sug["titulo"],
            "Descricao": sug["descricao"],
        }
        if sug.get("nome_contato"):
            payload["NomeContato"] = sug["nome_contato"]
        if sug.get("email_contato"):
            payload["EmailContato"] = sug["email_contato"]

        resultado = client.post_json("Sugestao", payload)
        criadas.append(resultado)
        print(f"   OK  [{sug['tipo']}] {sug['titulo']}")

    return criadas


# ─────────────────────────── entrypoint ──────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Populate da Plataforma Web de Dados UnB")
    parser.add_argument("--base-url",        default=DEFAULT_BASE_URL, help="URL base da API")
    parser.add_argument("--email",           default=DEFAULT_EMAIL,    help="E-mail do administrador")
    parser.add_argument("--senha",           default=DEFAULT_SENHA,    help="Senha do administrador")
    parser.add_argument("--somente-sugestoes", action="store_true",
                        help="Cria apenas as sugestões (útil para retry parcial)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Plataforma Web de Dados Institucionais - UnB")
    print("  Script de Populate")
    print("=" * 60)
    print(f"  API: {args.base_url}")

    client = PopulateClient(args.base_url, args.email, args.senha)

    if args.somente_sugestoes:
        _sugestoes = criar_sugestoes(client)
        print("\n" + "=" * 60)
        print("  Sugestoes criadas com sucesso!")
        print(f"      Sugestoes  : {len(_sugestoes)}")
        print("=" * 60)
        return

    categorias = criar_categorias(client)
    _pipelines  = criar_pipelines(client)
    _paineis    = criar_paineis(client, categorias)
    _sugestoes  = criar_sugestoes(client)

    print("\n" + "=" * 60)
    print("  Populate concluido com sucesso!")
    print(f"      Categorias : {len(categorias)}")
    print(f"      Pipelines  : {len(_pipelines)}")
    print(f"      Paineis    : {len(_paineis)}")
    print(f"      Sugestoes  : {len(_sugestoes)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
