# Como criar um agente

Todo agente herda de `Agent` (em `src/minesweeper/agents/base.py`) e implementa um
único método, `choose_action(observation)`, que recebe o que o agente vê (veja
[`ENVIRONMENT.md`](ENVIRONMENT.md)) e devolve uma `Action`.

```python
import random

from minesweeper.agents import Action, Agent
from minesweeper.environment import Observation


class RandomAgent(Agent):
    name = "random"

    def reset(self, seed: int | None = None) -> None:
        self.random_generator = random.Random(seed)

    def choose_action(self, observation: Observation) -> Action:
        row, col = self.random_generator.choice(observation.hidden_cells())
        return Action.reveal(row, col, is_guess=not observation.is_first_move)
```

## Ações

| Criação | Efeito |
|---|---|
| `Action.reveal(row, col, is_guess=False)` | Abre a célula. |
| `Action.flag(row, col)` | Coloca bandeira. |
| `Action.unflag(row, col)` | Tira a bandeira. |

Marque `is_guess=True` quando o agente abrir uma célula sem certeza lógica (um chute).
Isso alimenta a métrica "número de chutes" do PEAS. A primeira jogada não conta como
chute, porque é sempre segura.

`reset(seed)` é chamado antes de cada partida. Use para limpar a memória do agente e
para criar o gerador aleatório com a seed, assim a mesma partida pode ser repetida.

## Jogar uma partida

```python
from minesweeper.agents import play_game
from minesweeper.environment import Game, get_config

result = play_game(RandomAgent(), Game(get_config("easy"), seed=42))
print(result.won, result.revealed_ratio, result.guesses)
```

`play_game` repete observar, decidir e agir até a partida acabar, e devolve um
`GameResult` com:

* `status` e `won`;
* `moves`, `reveals`, `flags`, `guesses` e `wasted_moves` (ações sem efeito, como abrir
  uma célula já aberta);
* `revealed_cells` e `revealed_ratio` (fração das células seguras abertas);
* `thinking_seconds` e `seconds_per_move` (tempo gasto só dentro de `choose_action`).

Parâmetros opcionais:

* `on_step(observation, action, move_result)`: chamado depois de cada ação. A CLI usa
  para desenhar o tabuleiro a cada passo.
* `max_moves`: limite de ações (padrão: 3 vezes o número de células). Se o agente
  passar disso sem terminar, gera `AgentStuckError`.

## Explicar as decisões na CLI

No modo agente, a CLI mostra um painel "Log de Raciocínio do Agente". Depois de cada ação,
ela chama `agent.explain()` e acrescenta as linhas devolvidas ao log. O método é opcional
(o padrão devolve `[]`) e as linhas aceitam markup do rich:

```python
class LogicAgent(Agent):
    name = "logic"

    def choose_action(self, observation: Observation) -> Action:
        ...
        self._reason = [f"  [green]segura[/green] por dedução: {cell}"]
        return Action.reveal(*cell)

    def explain(self) -> list[str]:
        return self._reason
```
