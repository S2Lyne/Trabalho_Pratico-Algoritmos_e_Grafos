# Hamiltonian Path (HP): Complexidade, Algoritmos e Transição de Fase

**Desenvolvido por Aline Athaydes**

Este repositório contém a implementação e a análise experimental de dois algoritmos exatos para o problema do **Caminho Hamiltoniano (HP)** em grafos **não-direcionados**, desenvolvida para a disciplina **Algoritmos e Grafos (IC0004)** da **UFBA**.

O foco principal do projeto é analisar **esforço computacional**, **efetividade de podas** e o comportamento em **instâncias críticas (Transição de Fase)**.

---

## 🚀 Destaques Técnicos

- **Backtracking Otimizado (BT):** implementação instrumentada com **heurística de Warnsdorff** e **poda por componentes conexos** (checagem de conectividade no subgrafo restante e identificação de estruturas críticas que inviabilizam a continuação do caminho).
- **Programação Dinâmica (DP):** algoritmo no estilo **Bellman–Held–Karp** via *bitmasking*, com complexidade **O(n² · 2ⁿ)**, adequado para instâncias onde o BT tende à explosão combinatória.
- **Pipeline Experimental:** gerador de instâncias aleatórias usando o modelo **Erdős–Rényi** **G(n, p)** para mapear a dificuldade do problema em diferentes densidades.

---

## 📁 Estrutura do Projeto

```text
src/
├── hp_main.py        # CLI principal e exportação Graphviz (1-based)
├── hp_bt0.py         # Core do Backtracking com podas avançadas (0-based)
├── hp_dp.py          # Solver via Programação Dinâmica (0-based)
├── graph_gen.py      # Gerador de grafos (modelos HP e Erdős–Rényi)
├── bench.py          # Pipeline automático de benchmarks
├── plot_results.py   # Geração de gráficos a partir do CSV
├── plot_results2.py  # Alternativa de visualização (variações)
└── plot_analysis.py  # Visualização/análises (Matplotlib)
examples/             # Instâncias clássicas para testes e validação
outputs/              # Resultados consolidados (CSV, plots e visualizações)
```

---

## 🛠️ Configuração e Instalação

### Pré-requisitos

- Python 3.8+
- Graphviz (para gerar as visualizações `.dot`)

### Instalação das dependências

#### Instalação do Graphviz (Ubuntu/WSL)

```bash
sudo apt-get update && sudo apt-get install -y graphviz
```

#### Instalação de bibliotecas Python

```bash
pip install pandas matplotlib seaborn
```

---

## 📊 Execução dos Experimentos

Para reproduzir o benchmark e gerar as métricas utilizadas no relatório técnico:

### Rodar o pipeline de dados

```bash
python3 src/bench.py --csv outputs/results.csv --timeout-bt 10 --trials 5
```

### Gerar visualizações de análise

```bash
python3 src/plot_analysis.py
python3 src/plot_results2.py
python3 src/plot_results.py
```

Os resultados salvos em `outputs/results.csv` detalham o número de chamadas recursivas, podas realizadas e o tempo de execução para cada algoritmo.

---

## 📝 Referências Teóricas

- Garey, M. R., & Johnson, D. S. (1979). *Computers and Intractability*.  
  Redução clássica do Ciclo Hamiltoniano para o Caminho Hamiltoniano.

- Karp, R. M. (1972). *Reducibility Among Combinatorial Problems*.

- Bellman–Held–Karp: fundamentação para a complexidade da solução via Programação Dinâmica (DP por subconjuntos/bitmasking).
