# Série de Artigos para o LinkedIn: Engenharia de Dados, E-commerce e IA na Tese USP

Este documento contém os rascunhos estruturados para uma série de **3 artigos para o LinkedIn**, cobrindo toda a jornada técnica e científica do seu projeto. Eles foram escritos com uma linguagem profissional, engajadora e técnica, ideal para destacar a complexidade do seu trabalho no seu perfil.

---

# 🚀 Artigo 1: Como Estruturei um Pipeline de Dados 100% Serverless na GCP para Monitorar E-commerce

**Título Sugerido:** Como construir um pipeline de dados robusto e serverless na GCP para monitorar e-commerces (Sem gastar uma fortuna)

**Conteúdo do Post:**

Quem trabalha com ciência de dados sabe que a qualidade da análise começa na coleta. Para a minha dissertação de MBA na USP, estruturei um pipeline de dados automatizado capaz de monitorar preços, metadados e métricas de desempenho técnico (WPO) de grandes e-commerces do Brasil. 

A regra de ouro do projeto foi clara: usar uma arquitetura **100% serverless, incremental e de baixo custo** na Google Cloud Platform (GCP).

### 🛠️ A Arquitetura do Pipeline:
O fluxo funciona de forma integrada e automatizada:
1. **GitHub como Origem**: O código do pipeline é versionado e atualizado.
2. **CI/CD com Cloud Build**: Cada `git push` no repositório aciona um gatilho que empacota o código.
3. **Google Cloud Functions (Gen 2)**: O motor de execução em Python que realiza a coleta (Content, CrUX e PageSpeed). Ela é altamente escalável e cobrada apenas pelo tempo exato de execução.
4. **Cloud Scheduler (Cron)**: O agendador que executa a Cloud Function 3 vezes ao dia (10h, 15h e 21h).
5. **Google Cloud Storage (GCS)**: Onde os dados brutos (JSONs de extração) são armazenados de forma segura e barata.
6. **BigQuery**: A base analítica onde os dados são processados, limpos e carregados incrementalmente para consultas SQL rápidas.

### 📈 O Resultado em Números:
Em poucas semanas de execução automática, acumulamos mais de **1.500 registros** estruturados de experiência real de usuário (Chrome UX Report - CrUX), auditorias do PageSpeed e metadados de 7 SKUs em 15 grandes e-commerces brasileiros.

Esse pipeline serve de base para testarmos hipóteses sobre o desempenho de plataformas móveis versus desktop no e-commerce brasileiro e auditar a precisão de recomendações de compras feitas por modelos de linguagem (LLMs).

No próximo post, vou compartilhar as barreiras invisíveis que descobrimos ao tentar extrair dados de gigantes como Vivo, Magazine Luiza e Mercado Livre — spoilers: a nuvem é vigiada! 

O que você achou dessa arquitetura? Deixe suas dúvidas nos comentários! ⬇️

*Tags:* `#EngenhariaDeDados` `#GCP` `#Serverless` `#DataScience` `#MBAUSP`

---

# 🛡️ Artigo 2: As Barreiras Invisíveis do Web Scraping: Cloudflare, SPAs e IPs na Lista Negra

**Título Sugerido:** Por que extrair dados da web na Nuvem (GCP/AWS) é muito mais difícil do que no seu computador local?

**Conteúdo do Post:**

Se você acha que fazer Web Scraping é apenas enviar requisições HTTP e extrair tags com BeautifulSoup, o mercado corporativo atual tem um balde de água fria para você. 

Durante o diagnóstico de dados da minha tese na USP, nos deparamos com dados que revelaram um comportamento fascinante de segurança em grandes e-commerces brasileiros (como Vivo, Mercado Livre e Magalu).

### 1. A Nuvem está na Lista Negra (Blacklist)
Ao analisar o banco de dados do BigQuery, percebemos que lojas como a *Vivo* e o *Magazine Luiza* tinham **100% de taxa de bloqueio** na nuvem, retornando a famosa página `"Just a moment..."` do Cloudflare. 

Fizemos um teste: rodamos a mesma consulta a partir do meu computador local (IP residencial) e... **sucesso!** A página carregou.
* **O aprendizado**: Firewalls corporativos (WAF) bloqueiam preventivamente blocos inteiros de IPs de nuvens públicas (GCP, AWS, Azure) para evitar ataques de DDoS e raspagem em massa por concorrentes, mas deixam IPs de internet residencial passarem.

### 2. A Ilusão da Página Carregada (SPAs)
Mesmo contornando o IP usando o computador local, a requisição tradicional de Python coletou apenas **133 palavras** na Vivo. Cadê o preço? Cadê o produto?
* **O aprendizado**: O e-commerce moderno é construído como **Single Page Application (SPA)**. O servidor envia apenas um "esqueleto" HTML com menus e rodapés. O preço e os detalhes do produto são carregados depois via JavaScript (APIs). Uma requisição estática em Python é incapaz de ler isso sem rodar um navegador real.

### 3. Nem o disfarce ajudou: O bloqueio de Hardware (WebGL e Canvas)
Decidimos elevar o nível: usamos o **Playwright com o plugin Stealth** (que mascara o robô desativando a variável `navigator.webdriver` e fingindo ser um usuário real). Mesmo assim, no site da Vivo, a página retornou em branco.
* **O aprendizado**: Tecnologias modernas de detecção de bots (como Cloudflare Enterprise e Adobe Identity Service) não olham apenas para o navegador. Elas realizam análises de **TLS Fingerprinting** (assinatura de rede do handshake SSL) e medem renderização de GPU (WebGL/Canvas) em milissegundos para desmascarar automações de navegador.

Essas barreiras provam que a coleta de dados na web se tornou uma batalha sofisticada entre engenheiros de segurança e engenheiros de dados. No último post dessa série, explicarei como contornamos o orçamento limitado de uma tese acadêmica pivotando a nossa estratégia de testes de Inteligência Artificial.

Você já foi bloqueado por WAFs em projetos de raspagem de dados? Como resolveu? ⬇️

*Tags:* `#WebScraping` `#Cybersecurity` `#Cloudflare` `#Playwright` `#DataEngineering`

---

# 🤖 Artigo 3: O Pivot Estratégico: Avaliando Três Gerações de LLMs do Google sob Temperatura Zero

**Título Sugerido:** Restrição de Orçamento na Pesquisa? Como transformamos a limitação de APIs pagas em um estudo comparativo robusto do ecossistema Gemini.

**Conteúdo do Post:**

Em projetos acadêmicos e corporativos, nem sempre o orçamento é infinito. No planejamento inicial do meu projeto de IA para a USP, a ideia era enviar 21 consultas de compras para o Claude (Anthropic) e para o Gemini (Google) para avaliar a factualidade e o nível de alucinação de preços de cada assistente. 

No entanto, as restrições financeiras para consumo de APIs pagas (como a do Claude) bateram à porta. 

### 💡 O Pivot Metodológico
Em vez de abortar o teste de IA ou usar dados parciais, realizamos um **pivot estratégico**: mantivemos o foco no ecossistema do Google (que integrava-se gratuitamente às cotas da nossa Cloud Function via Vertex AI) e estruturamos um estudo comparativo profundo entre **três gerações e arquiteturas diferentes do Gemini**:

1. **`gemini-2.5-pro`** (O modelo premium de raciocínio lógico complexo e alto poder de parâmetros).
2. **`gemini-2.5-flash`** (O modelo de última geração otimizado para velocidade e eficiência).
3. **`gemini-1.5-flash`** (A geração anterior, servindo como linha de base/baseline histórico).

Isso nos permite responder cientificamente: *A evolução dos modelos reduziu a alucinação de preços ao longo das gerações? O modelo Pro erra menos que o Flash em dados numéricos brasileiros?*

### 🌡️ O Controle da Temperatura (Incerteza)
Para garantir o rigor científico, introduzimos a parametrização de **Temperatura em nível baixo (próxima a 0.2)**. 
Na IA Generativa, a temperatura controla a "criatividade". Em tarefas criativas, valores altos (0.8 a 1.0) são ótimos. Mas para e-commerce, onde queremos precisão de preços centavo por centavo, a temperatura baixa força o modelo a ser determinístico, reduzindo drasticamente a chance de "chutar" (alucinar) preços falsos.

### 🔄 Automação Integrada na GCP
O script de consulta aos agentes de IA foi integrado diretamente na Cloud Function principal. Agora, três vezes ao dia, o pipeline:
1. Coleta o preço real das URLs no e-commerce (quando não bloqueado).
2. Envia as perguntas de compras para as três LLMs no BigQuery.
3. Carrega tudo no banco de dados para cruzarmos na fase de avaliação da tese.

Este pivot transformou uma restrição de orçamento em um caso de estudo sobre como as empresas podem auditar internamente as respostas dos seus chatbots de atendimento contra dados reais de inventário.

Acompanhe as próximas atualizações da pesquisa e comente o que achou dessa abordagem comparativa! ⬇️

*Tags:* `#ArtificialIntelligence` `#LLMs` `#Gemini` `#GoogleCloud` `#TeseDeMestrado`
