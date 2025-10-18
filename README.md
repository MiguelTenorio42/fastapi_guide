# 📚 FastAPI Guide - Guia Completo de Estudo

> **Documentação estruturada para aprender e desenvolver APIs FastAPI do básico ao avançado**

Este repositório contém um guia completo e estruturado para aprender FastAPI, desde conceitos básicos até implementações avançadas para produção.

## 🚀 Acesso à Documentação

A documentação está disponível online em: **[GitHub Pages](https://seu-usuario.github.io/fastapi_guide/)**

## 📖 Sobre o Projeto

Esta documentação foi criada para ser um **guia completo** no aprendizado e desenvolvimento de APIs com FastAPI. Seja você um iniciante ou desenvolvedor experiente, aqui você encontrará tudo o que precisa.

### 🎯 Trilhas de Aprendizado

- **🚀 Trilha Rápida** (1-2 semanas) - Para criar APIs simples rapidamente
- **📚 Trilha Completa** (4-6 semanas) - Para dominar FastAPI completamente  
- **🏭 Trilha Produção** (8-12 semanas) - Para APIs enterprise e produção

### 📋 Estrutura da Documentação

- **📖 Fundamentos** - Conceitos essenciais de APIs e FastAPI
- **🔧 Desenvolvimento** - Recursos básicos e intermediários
- **🚀 Avançado** - Recursos avançados e otimizações
- **🏭 Produção** - Deploy, monitoramento e melhores práticas
- **🏗️ Guia End-to-End** - Projetos completos passo a passo

## 🛠️ Desenvolvimento Local

### Pré-requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacotes)

### Configuração

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/fastapi_guide.git
cd fastapi_guide

# Instale as dependências
uv sync

# Build da documentação
cd docs
uv run sphinx-build -b html . _build/html

# Ou use o make (Linux/Mac)
make html

# Ou use o make.bat (Windows)
make.bat html
```

### Visualização Local

Após o build, abra o arquivo `docs/_build/html/index.html` no seu navegador.

## 🔧 Tecnologias Utilizadas

- **[Sphinx](https://www.sphinx-doc.org/)** - Gerador de documentação
- **[MyST Parser](https://myst-parser.readthedocs.io/)** - Markdown avançado para Sphinx
- **[Sphinx RTD Theme](https://sphinx-rtd-theme.readthedocs.io/)** - Tema responsivo
- **[GitHub Actions](https://github.com/features/actions)** - CI/CD automático
- **[GitHub Pages](https://pages.github.com/)** - Hospedagem estática

## 📝 Contribuindo

Contribuições são bem-vindas! Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Diretrizes para Contribuição

- Siga a estrutura de numeração existente
- Mantenha referências cruzadas atualizadas
- Use exemplos práticos sempre que possível
- Teste os códigos antes de documentar
- Mantenha compatibilidade com MyST Parser

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Suporte

Se você encontrar algum problema ou tiver sugestões:

- Abra uma [Issue](https://github.com/seu-usuario/fastapi_guide/issues)
- Contribua com um [Pull Request](https://github.com/seu-usuario/fastapi_guide/pulls)

---

**Feito com ❤️ para a comunidade Python/FastAPI**
