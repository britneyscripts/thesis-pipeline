-- =====================================================================
-- Queries de Análise de Qualidade de Extração - Tese USP
-- Objetivo: Identificar bloqueios (WAF/Cloudflare) e sucesso de dados
-- Tabela base: `thesisusp.content`
-- =====================================================================

-- 1. % da categoria 'electronics' que respondeu COM DADOS (Sucesso)
-- Filtra eletrônicos e calcula quantos escaparam do bloqueio.
SELECT
  COUNT(*) AS total_eletronicos,
  COUNTIF(has_errors = FALSE AND extraction_blocked = FALSE) AS total_sucesso,
  ROUND(COUNTIF(has_errors = FALSE AND extraction_blocked = FALSE) / COUNT(*) * 100, 2) AS percentual_sucesso_com_dados
FROM
  `thesisusp.content`
WHERE
  category = 'electronics';


-- 2. % Geral de Erros (Todas as categorias)
-- Mede o tamanho real do "buraco" na amostra total causado por defesas das lojas.
SELECT
  COUNT(*) AS total_produtos,
  COUNTIF(has_errors = TRUE OR extraction_blocked = TRUE) AS total_erros,
  ROUND(COUNTIF(has_errors = TRUE OR extraction_blocked = TRUE) / COUNT(*) * 100, 2) AS percentual_erros_geral
FROM
  `thesisusp.content`;


-- 3. Tipologia do Erro (Onde os scripts estão falhando?)
-- Cruza o Status Code HTTP com o Title da página para revelar bloqueios (ex: "Just a moment...")
SELECT
  robots_txt_status_code AS http_status,
  title AS sintoma_do_bloqueio,
  COUNT(*) AS quantidade_ocorrencias,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER() * 100, 2) AS percentual_deste_erro
FROM
  `thesisusp.content`
WHERE
  has_errors = TRUE OR extraction_blocked = TRUE
GROUP BY
  robots_txt_status_code,
  title
ORDER BY
  quantidade_ocorrencias DESC;
