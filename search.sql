-- encode
CREATE
OR REPLACE TABLE `CustomerReview.review_embeddings` AS
SELECT *
FROM ML.GENERATE_EMBEDDING (
        MODEL `CustomerReview.Embeddings`, (
            SELECT review_text AS content
            FROM
                `CustomerReview.customer_reviews`
        )
    );

-- create a vector index
CREATE
OR REPLACE VECTOR INDEX `CustomerReview.reviews_index` ON `CustomerReview.review_embeddings` (text_embedding) OPTIONS (
    index_type = 'IVF',
    distance_type = 'COSINE'
);

-- search
CREATE
OR REPLACE TABLE `CustomerReview.customer_reviews_embedded` AS
SELECT
    query.query AS query_text,
    base.content AS matched_review,
    distance
FROM VECTOR_SEARCH (
        TABLE `CustomerReview.review_embeddings`, 'text_embedding', (
            SELECT text_embedding, content AS query
            FROM ML.GENERATE_EMBEDDING (
                    MODEL `CustomerReview.Embeddings`, (
                        SELECT 'service' AS content
                    )
                )
        ), top_k = > 5, options = > '{"fraction_lists_to_search": 0.01}'
    );

# -------------------------------------

CREATE OR REPLACE MODEL `CustomerReview.Embeddings`
REMOTE WITH CONNECTION `us.embedding_conn`
OPTIONS (ENDPOINT = 'gemini-embedding-2-preview');

LOAD DATA OVERWRITE CustomerReview.customer_reviews (
    customer_review_id INT64,
    customer_id INT64,
    location_id INT64,
    review_datetime DATETIME,
    review_text STRING,
    social_media_source STRING,
    social_media_handle STRING
)
FROM FILES (
        format = 'CSV', uris = ['gs://spls/gsp1249/customer_reviews.csv']
    );

CREATE
OR REPLACE TABLE `CustomerReview.customer_reviews_embedded` AS
SELECT *
FROM ML.GENERATE_EMBEDDING (
        MODEL `CustomerReview.Embeddings`, (
            SELECT review_text AS content
            FROM
                `CustomerReview.customer_reviews`
        )
    );

CREATE
OR REPLACE VECTOR INDEX `CustomerReview.reviews_index` ON `CustomerReview.customer_reviews_embedded` (ml_generate_embedding_result) OPTIONS (
    distance_type = 'COSINE',
    index_type = 'IVF'
);

CREATE
OR REPLACE TABLE `CustomerReview.vector_search_result` AS
SELECT query.query, base.content
FROM VECTOR_SEARCH (
        TABLE `CustomerReview.customer_reviews_embedded`, 'ml_generate_embedding_result', (
            SELECT
                ml_generate_embedding_result, content AS query
            FROM ML.GENERATE_EMBEDDING (
                    MODEL `CustomerReview.Embeddings`, (
                        SELECT 'service' AS content
                    )
                )
        ), top_k = > 5, options = > '{"fraction_lists_to_search": 0.01}'
    );

CREATE
OR REPLACE MODEL `CustomerReview.Gemini` REMOTE
WITH
    CONNECTION `us.embedding_conn` OPTIONS (ENDPOINT = 'gemini-2.5-flash');

SELECT ml_generate_text_llm_result AS generated
FROM ML.GENERATE_TEXT (
        MODEL `CustomerReview.Gemini`, (
            SELECT CONCAT (
                    'Summarize what customers think about our services', STRING_AGG (
                        FORMAT(
                            'review text: %s', base.content
                        ), ',\n'
                    )
                ) AS prompt
            FROM
                `CustomerReview.vector_search_result` AS base
        ), STRUCT (
            0.4 AS temperature, 300 AS max_output_tokens, 0.5 AS top_p, 5 AS top_k, TRUE AS flatten_json_output
        )
    );