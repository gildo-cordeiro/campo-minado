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

**Como jogar:** as células têm nome no estilo xadrez, com a letra da coluna e o número
da linha (o tabuleiro mostra os dois). Digite `C4` para abrir a célula C4 e `!C4` para
colocar ou tirar a bandeira. `?` mostra a ajuda e `q` sai.

Sem argumentos (`python -m minesweeper`), o jogo pergunta o modo, o agente e a dificuldade.
O que for passado por argumento não é perguntado.

A tela segue o modelo da interface de referência da disciplina (`tictac.py`) e é redesenhada
a cada jogada:

* **Tabuleiro** à esquerda, com a seed no título e as minas restantes e jogadas embaixo;
* **Log de Jogadas** (modo humano) ou **Log de Raciocínio do Agente** (modo agente) à direita;
* **Legenda** com os símbolos e o placar da sessão.

Ao fim de cada partida dá pra jogar de novo e trocar as configurações. No modo agente,
`--delay` controla o intervalo entre as jogadas, em segundos (padrão: 0.4).

## Estrutura dos Arquivos

* `src/minesweeper/environment/`: tabuleiro, regras do jogo e percepções do agente.
* `src/minesweeper/agents/`: implementações dos agentes.
* `src/minesweeper/inference/`: restrições, busca (CSP) e cálculo de probabilidades.
* `src/minesweeper/cli/`: interface de terminal.
  * `app.py`: a interface completa (argumentos, configuração, tela, turnos e placar),
    no formato do `tictac.py` da disciplina.
  * `render.py`: desenha o tabuleiro.
  * `commands.py` e `coords.py`: interpretam o que o jogador digita (`C4`, `!C4`).
  * `registry.py`: encontra os agentes pelo nome.
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
