# 🛒 Sprint4-GenAI: Sistema de Scraping de Cartuchos HP

## 📖 Descrição

Sistema automatizado de extração de dados de produtos (cartuchos HP) utilizando **Agents SDK** e **Selenium WebDriver**. O projeto implementa uma arquitetura de agentes inteligentes para coletar, processar e consolidar informações de produtos de diferentes e-commerces brasileiros.

## 🎯 Funcionalidades

- ✅ **Extração automatizada** de dados de produtos da Amazon Brasil
- ✅ **Extração automatizada** de dados de produtos do Mercado Livre Brasil  
- ✅ **Processamento inteligente** com regex otimizado e seletores CSS
- ✅ **Consolidação de dados** com remoção de duplicatas
- ✅ **Exportação para CSV** com dados estruturados
- ✅ **Relatórios estatísticos** automáticos
- ✅ **Arquitetura de agentes** usando OpenAI GPT-4o-mini

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**
- **Selenium WebDriver** - Automação de navegador
- **Agents SDK** - Framework de agentes inteligentes
- **OpenAI GPT-4o-mini** - Modelo de linguagem
- **Pandas** - Manipulação de dados
- **WebDriver Manager** - Gerenciamento automático do ChromeDriver
- **Python-dotenv** - Gerenciamento de variáveis de ambiente

## 📁 Estrutura do Projeto

```
Sprint4-GenAI/
├── agentsSDK.py              # Script principal com agentes e ferramentas
├── requirements.txt          # Dependências do projeto
├── hp_cartridges_search_data.csv  # Dados extraídos (gerado automaticamente)
├── .env                      # Variáveis de ambiente (criar manualmente)
└── .gitignore               # Arquivos ignorados pelo Git
```

## ⚙️ Configuração e Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/marcosPaolucci/Sprint4-GenAI.git
cd Sprint4-GenAI
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto:
```env
OPENAI_API_KEY=sua_chave_openai_aqui
```

### 4. Execute o sistema
```bash
python agentsSDK.py
```

## 🤖 Arquitetura dos Agentes

O sistema implementa **3 agentes especializados**:

### 🔍 Agente Amazon Search
- **Função**: Extração de dados da Amazon Brasil
- **Ferramentas**: `extract_amazon_search_data`
- **Tecnologia**: Regex otimizado para parsing HTML
- **Dados extraídos**: Nome, preço, avaliação, URL, disponibilidade, ASIN

### 🔍 Agente Mercado Livre Search  
- **Função**: Extração de dados do Mercado Livre Brasil
- **Ferramentas**: `extract_mercadolivre_search_data`
- **Tecnologia**: Seletores CSS baseados em scraper Scrapy
- **Dados extraídos**: Nome, preço, avaliação, URL, disponibilidade, MLB_ID

### 📊 Agente Consolidador
- **Função**: Consolidação e persistência de dados
- **Ferramentas**: `csv_writer_tool`
- **Processamento**: Remoção de duplicatas, ordenação por preço
- **Saída**: Arquivo CSV estruturado

## 📊 Dados Coletados

O sistema coleta as seguintes informações para cada produto:

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `Nome do Produto` | Nome completo do produto | "Cartucho HP 664XL preto Original" |
| `Preço (R$)` | Preço em reais | 169.99 |
| `Avaliação (estrelas)` | Nota de 0 a 5 estrelas | 4.7 |
| `URL` | Link direto para o produto | "https://amazon.com.br/dp/..." |
| `Disponibilidade` | Status do estoque | "Em estoque" |
| `ASIN/MLB_ID` | Identificador único do produto | "B075736YWS" |

## 🎯 URLs de Busca Configuradas

- **Amazon Brasil**: `https://www.amazon.com.br/s?k=cartucho+hp+664+original`
- **Mercado Livre Brasil**: `https://lista.mercadolivre.com.br/cartucho-hp-662`

## 📈 Relatórios Automáticos

O sistema gera automaticamente:
- 📊 **Estatísticas gerais**: Total de produtos, preços médio/mín/máx
- ⭐ **Análise de avaliações**: Média de estrelas dos produtos
- 🏆 **Top 5 produtos**: Ranking por preço
- 🔧 **Remoção de duplicatas**: Produtos únicos identificados

## 🚀 Exemplo de Execução

```bash
🚀 INÍCIO DO SCRAPING DE CARTUCHOS HP - PÁGINAS DE BUSCA
============================================================

[FLUXO] 📊 Extraindo dados de 2 páginas de busca...

  🌐 Processando: Amazon Brasil
     URL: https://www.amazon.com.br/s?k=cartucho+hp+664+original
     ✅ 10 produtos extraídos

  🌐 Processando: Mercado Livre Brasil  
     URL: https://lista.mercadolivre.com.br/cartucho-hp-662
     ✅ 10 produtos extraídos

[FLUXO] 📋 Total de produtos coletados: 20
[FLUXO] 🔧 18 produtos únicos após remoção de duplicatas

✅ Dados de 18 produtos salvos com sucesso em hp_cartridges_search_data.csv

📊 RESUMO DOS DADOS COLETADOS:
   • Total de produtos: 18
   • Preço médio: R$ 145.23
   • Preço mínimo: R$ 85.00
   • Preço máximo: R$ 195.99
   • Avaliação média: 4.5 estrelas

🎉 SCRAPING CONCLUÍDO!
```

## 🔧 Configurações Avançadas

### Selenium WebDriver
- **Modo**: Headless (sem interface gráfica)
- **User-Agent**: Simulação de navegador real
- **Anti-detecção**: Propriedades de automação removidas
- **Timeouts**: 5 segundos para carregamento de páginas

### Processamento de Dados
- **Regex otimizado** para extração precisa
- **Validação de dados** com ranges apropriados
- **Encoding UTF-8** para caracteres especiais
- **Ordenação automática** por preço

## 🚨 Requisitos do Sistema

- **Python**: 3.8 ou superior
- **Chrome Browser**: Instalado no sistema
- **Conexão com Internet**: Para acesso aos e-commerces
- **Chave OpenAI**: Para funcionamento dos agentes
- **RAM**: Mínimo 4GB recomendado

