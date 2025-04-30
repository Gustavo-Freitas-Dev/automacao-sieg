# 🧾 SiegAutomator

Automatize o download e processamento de documentos fiscais eletrônicos (CT-e e NF-e) diretamente da plataforma SIEG, gerando relatórios em Excel de forma rápida e eficiente.

---

## 📌 Visão Geral

**SiegAutomator** é uma aplicação desenvolvida em Python com uma interface gráfica feita com [Flet](https://flet.dev).  
O objetivo é simplificar o processo de obtenção de documentos fiscais, permitindo ao usuário:

- Informar o CNPJ, mês e ano
- Escolher entre CT-e ou NF-e
- Executar a automação com apenas um clique

A aplicação faz login na plataforma SIEG, navega até os documentos desejados, baixa os XMLs e gera uma planilha Excel com os dados extraídos.

---

## 🚀 Funcionalidades

- 🔐 Login automático na plataforma SIEG
- 📄 Download automatizado de XMLs de CT-e e NF-e
- 📤 Extração de dados dos XMLs: data, emitente, valor, impostos etc.
- 📊 Geração de planilhas Excel (.xlsx) com formatação profissional
- 📂 Seletor de pasta interativo para definir onde salvar os arquivos
- 🖥 Interface gráfica moderna, feita com Flet

---

## 🖼 Interface

> Interface gráfica intuitiva para:
> - Inserção de CNPJ
> - Escolha de mês e ano
> - Seleção do tipo de documento (CT-e ou NF-e)
> - Execução simples com botão único  
> 
> Indicador de progresso e mensagens informativas inclusas

---

## ⚙️ Tecnologias Utilizadas

- [Python 3.10+](https://www.python.org/)
- [Playwright](https://playwright.dev/python/)
- [Flet](https://flet.dev/)
- [Pandas](https://pandas.pydata.org/)
- [XlsxWriter](https://xlsxwriter.readthedocs.io/)
- [dotenv](https://pypi.org/project/python-dotenv/)

---

## 📦 Instalação Rápida

1. **Clone o repositório:**

```bash
git clone https://github.com/Gustavo-Freitas-Dev/automacao-sieg.git
cd automacao-sieg
