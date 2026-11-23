# Campo Minado Probabilístico

**Disciplina:** Introdução à Inteligência Artificial (IMD3001)  
**Semestre:** 2026.2  
**Professor:** Prof. Dr. André Fonseca  
**Turma:** [T0X]

## Integrantes do Grupo
* Gildo Cordeiro Duarte (20190146782)
* Nome Completo (Matrícula)
* Nome Completo (Matrícula)

## Descrição do Projeto
Agente que joga Campo Minado automaticamente, pelo terminal. A cada jogada o agente
transforma os números revelados em restrições, deduz as células que são certamente
seguras ou certamente minas e, quando a lógica não basta, calcula a probabilidade de
cada célula fechada conter uma mina, escolhendo a de menor risco.

O projeto compara agentes de complexidade crescente (aleatório, lógico, CSP e
probabilístico) e mede seu desempenho em diferentes dificuldades. Implementado em
Python, com interface de linha de comando.

A modelagem PEAS e a arquitetura do agente estão em [`docs/PEAS.md`](docs/PEAS.md).

## Guia de Instalação e Execução

### 1. Instalação das Dependências
Certifique-se de ter o **Python 3.10+** instalado.

```bash
git clone https://github.com/gildo-cordeiro/campo-minado.git
cd campo-minado
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

O `pip install -e .` instala o pacote em modo editável: as mudanças no código valem na hora,
sem reinstalar. Ele também cria o comando `minesweeper`, um atalho para `python -m minesweeper`.

### 2. Como Executar
*(em desenvolvimento)*

Ative o ambiente virtual antes de rodar (`source .venv/bin/activate`). A instalação só
precisa ser feita uma vez; nas próximas sessões basta ativar o venv.

```bash
# Jogar como humano (digite '?' no jogo para ver os comandos)
python -m minesweeper --mode human --difficulty easy

# Assistir um agente jogar (o nome vem do atributo `name` do agente)
python -m minesweeper --mode agent --agent random --difficulty easy --seed 42

# Em desenvolvimento: mostrar as probabilidades do agente probabilístico
python -m minesweeper --mode agent --agent prob --show-prob --seed 42

# Ver todas as opções
python -m minesweeper --help
```

Com o pacote instalado, também dá pra usar o comando curto `minesweeper`, que aceita as
mesmas opções:

```bash
minesweeper --mode human --difficulty easy
```

## Estrutura dos Arquivos

* `src/minesweeper/environment/`: tabuleiro, regras do jogo e percepções do agente.
* `src/minesweeper/agents/`: implementações dos agentes.
* `src/minesweeper/inference/`: restrições, busca (CSP) e cálculo de probabilidades.
* `src/minesweeper/cli/`: interface de terminal.
* `experiments/`: scripts de benchmark e resultados.
* `docs/`: modelagem PEAS e documentação.
* `assets/`: imagens e gráficos de resultados.
* `pyproject.toml`: metadados do pacote, dependências e o comando `minesweeper`.

## Resultados e Demonstração
*(em desenvolvimento)*

## Referências

* RUSSELL, S.; NORVIG, P. *Artificial Intelligence: A Modern Approach*, 4ª ed. https://aima.cs.berkeley.edu/
* UC Berkeley. CS188: Introduction to Artificial Intelligence. https://inst.eecs.berkeley.edu/~cs188/
* Template do projeto: https://github.com/oandrefonseca/project_template
