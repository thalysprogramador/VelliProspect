# 🚀 Velli Prospect V3 — Mobile & PC

Software profissional de prospecção B2B inteligente, movido a IA (Google Gemini), com interface moderna e responsiva focada em performance tanto no Desktop quanto no Celular (Android).

## ✨ Funcionalidades
- **Varredura Inteligente**: Busca leads no Instagram, Google e outras fontes.
- **Avaliação em Tempo Real (IA)**: O "VELLIX IA" analisa a bio, posts e sites para dar uma nota de 0 a 10 e justificar o fit.
- **Design Premium**: Interface minimalista Black & White com animações suaves.
- **Responsivo**: Layout adaptável (Navigation Rail no PC, Bottom Bar no Celular).
- **Exportação**: Gera CSV para integração com CRMs.
- **Persistência Local**: Banco de dados SQLite integrado para rodar offline e no celular.

## 📱 Mobile (Android)
Este projeto foi construído com **Flet**, o que permite gerar um APK nativo facilmente. 
O layout foi otimizado para telas pequenas, garantindo que os cards de leads e o Copilot sejam perfeitamente utilizáveis.

## 🛠️ Como rodar

### 1. Requisitos
- Python 3.10+
- Chave de API do Gemini (Gratuita no [Google AI Studio](https://aistudio.google.com/))

### 2. Instalação
```bash
# Clone o repositório
git clone <url-do-seu-repo>
cd VelliProspect

# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 3. Execução
```bash
python main.py
```

## 🏗️ Estrutura do Projeto
- `main.py`: Ponto de entrada e lógica de navegação responsiva.
- `views/`: Telas do aplicativo (Prospectar, Campanhas, Configurações).
- `scraper.py`: Motores de busca (DuckDuckGo, Instagram Scraper).
- `ai_evaluator.py`: Integração com Gemini para análise de leads.
- `database.py`: Camada de dados SQLite compatível com Mobile.

## 📄 Licença
Privado - Uso exclusivo da Velli Systems.
