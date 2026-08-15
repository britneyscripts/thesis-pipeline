# Zero-Click E-commerce: How AI is Shifting Search from Hunting to Passive Discovery


I hope this article finds you well this monday.

Before talking about my findings I want to address a quick point because a friend just threw tomatoes at me for my previous article. When I talked about the "Gemini paradox", I was talking from the user point of view. From Google's architectural standpoint there is no paradox: the chat uses parametric memory plus RAG, and the sidebar consumes the Shopping Graph API deterministically. Two separate systems. For the user and the retailer sitting on the same interface, though, it still feels like one. Enough said.

Well, let's go see what we have here. The commercial LLMs are a bunch of black boxes. We don't know exactly what happens there, we just can infer, collect data, and think about what the rules and guidance are.

### Magalu Vanished from Google Shopping

Let's look at Magalu. In my last article, I showed that Magazine Luiza had six inconsistent entries inside the Shopping Graph for the same query, with three different snapshots of the same product captured at different times, with varying shipping prices and delivery estimates.

And then, for the query "iPhone 17 Pro laranja 256GB", Magalu disappeared from Google Shopping results completely. Competitors like iPlace, Fast Shop, Mercado Livre, and Carrefour are occupying the top slots. Magalu does not appear on the first shelf for me right now.

Why did they vanish? I have two main hypotheses:

First, it could be content controls. Retailers can use data-nosnippet to exclude page text from snippets, while the pause: all attribute in Google Merchant Center temporarily excludes products from Google Shopping ads and free listings. If Magalu, or Google automatically due to bot validation issues, triggered these controls, the items would still reside in the backend Shopping Graph but would immediately vanish from the frontend Google Shopping interface.

Second, it could be the natural rotation of the Shopping Graph. The graph is dynamic. Those inconsistent snapshots we documented are a sign of a feed that Google cannot reliably validate. If the system detects conflicting data points, like different delivery rates for the same product id, the algorithm rotates the options and penalizes the inconsistent merchant.

Is this an internal corporate silo issue or an external Google algorithm shift? Genuinely, I don't know and I won't risk a guess. But it shows how fragile visibility is when security, feed health, and search engine updates collide without coordination.

### The Data Behind the Friction: 1,595 Extractions

For this analysis, we cut our dataset at 1,595 total content extractions. We tracked seven specific PDPs across different stores, three times a day, using a crawler to retrieve content, schema markup, and pagespeed data, while CrUX metrics were collected 28 days apart. The real scale of this study lies in the frequency of these extractions and the query responses, not the number of pages.

As we saw previously, the data shows a stark divide. Some retailers block bots completely: Magazine Luiza, Vivo, and Cosmetis have a 100% block rate. Mercado Livre is close behind at 99.6%, Fastshop at 89.8%. On the other end, Apple Brasil, Kabum, Natura, Americanas, and Boticario D2C show a 0% block rate.

A quick note on methodology: a 0% block rate does not automatically mean full content extraction. A site can return HTTP 200 and deliver only the page header while the actual PDP content is hidden behind a JavaScript challenge. We validated this using the simplest way possible: counting words. Kabum passed this test, returning full text and critical schema fields. Americanas, however, was a false positive for a completely different reason: it simply returned a 404 dead link on the monitored URL. That contrast shows why you cannot just trust the server response code—a critical blind spot for any e-commerce Product Manager relying solely on standard uptime monitoring.

Out of 1,595 total content extractions, only about 783 were actually readable. The rest were blocked at the door.

### The Three Query Types and What They Reveal

I use a query type parameter to test three distinct behaviors. They produce radically different results.

For product_exact, the query is the exact product name and model: "iPhone 17 Pro 512GB laranja cosmico preco disponibilidade Brasil". The agent tries to search the web and cite specific stores. This is where PDP quality and crawlability actually matter.

For brand, the query is brand plus intention: "Apple iPhone 17 Pro melhores lojas para comprar no Brasil" or "O Boticario Botik serum vitamina C onde comprar". The behavior splits. For a stable skincare product, the agent behaves similarly to product_exact and cites stores. For a recent electronic, the knowledge cutoff kills the result before PDP quality even comes into play. When we queried about the iPhone 17 Pro, Gemini answered that it had not been launched yet.

For generic, the query is category-level with no brand anchor: "melhor serum vitamina C antienvelhecimento pele mista" or "melhor smartphone premium ate R$12.000 para comprar em 2026". The agent stops trying to ground in real-time data and runs almost entirely on parametric memory. It recommends brands it learned during training. In our tests, none of the seven SKUs we monitor appeared in generic query results. The agent cited Garnier, Cerave, and other established brands instead, regardless of the PDP quality of the pages we were tracking.

The battle for generic queries is won or lost before the page even loads.

To prove this, we need to look at the data. In our EDA phase, we parsed the JSON responses from the Gemini API and loaded them into a Pandas dataframe to calculate the citation matrix. Here is a simplified version of the aggregation:

```python
import pandas as pd

# Grouping by query type to calculate citation rates
citation_matrix = df.groupby('query_type').agg(
    total_queries=('query_id', 'count'),
    retailer_citations=('retailer_mentioned', 'sum'),
    brand_only_citations=('brand_only_mentioned', 'sum')
).reset_index()

citation_matrix['retailer_citation_rate'] = (
    citation_matrix['retailer_citations'] / citation_matrix['total_queries']
).apply(lambda x: f"{x:.0%}")

print(citation_matrix.to_markdown(index=False))
```

And here is the resulting matrix from our initial sample of 49 validated interactions (excluding API timeouts and extraction errors):

| query_type    | total_queries | retailer_citations | brand_only_citations | retailer_citation_rate |
|:--------------|:--------------|:-------------------|:---------------------|:-----------------------|
| product_exact | 21            | 12                 | 2                    | 57%                    |
| brand         | 14            | 9                  | 4                    | 64%                    |
| generic       | 14            | 0                  | 14                   | 0%                     |

The numbers are structural. When testing `product_exact` or `brand` queries (for stable products), the agent successfully grounded the response and cited retailers like Magalu or Kabum in 57% and 64% of the interactions, respectively. But as soon as the query shifts to `generic`, the citation rate for e-commerce product pages drops to absolute zero. The agent cited global brands 100% of the time, bypassing the retail layer entirely.

A critical methodological caveat must be made here. Our API calls to Gemini via Vertex AI were explicitly routed through the `us-central1` region. In a real-world scenario, a consumer searching from São Paulo passes implicit geo-IP context to the agent, which might force it to ground the response locally. By querying from a US server, we inadvertently tested the agent's "pure" parametric memory stripped of geographic bias. And without that local anchor, it defaulted to global brands, entirely ignoring the Brazilian retailers we were tracking.

### Beyond the Numbers: Sycophancy, Zero-Clicks, and Passive Discovery

The first thing that stands out is what the literature calls sycophancy. When a user asks about the iPhone 17 Pro, the model does not always say "I don't have reliable data on this." More often it tries to be helpful anyway, and the result can be very messy. It pulls from parametric memory, generates a plausible-sounding answer, and fills in the blanks. In the case of the iPhone 17 Pro, Gemini confidently told us the phone had not been released yet. For a moment, I even thought I had the dates wrong. But the model was not lying in bad faith. It was simply doing what LLMs do when real-time grounding is absent, blocked, or overridden by the algorithm: they fall back on their training weights and default to what they think they know. For retailers and product managers, this means that the model can become a confident source of misinformation about your own product.

The second result is the one that should concern anyone working in e-commerce strategy. It is the zero-click problem. When the agent gives a complete answer inside the interface, the user has no reason to click through to the retailer's page. No click means no session, no attribution, no revenue tracking, and no remarketing data. The traffic that traditional SEO optimized for simply does not happen. The agent absorbed the demand and resolved it without sending the user anywhere.

This is not a future problem. It is happening now, in every generic query we tested.

The third thing this data highlights is the gap between our approach and the current focus of academic literature on Answer Engines. Foundational studies—such as the benchmark work by Baeza-Yates et al. (2024)—focus on evaluating the quality of the AI's response. They audit factual accuracy, citation fidelity, and whether the response is one-sided. In short, the literature is heavily focused on auditing the *output*. While they rely on different types of queries, these studies provide an essential baseline for understanding the end-user experience.

What we are measuring with the Agent-Readiness Score (ARS) is the input side. We are measuring whether the product detail page is structurally prepared to be read, indexed, and cited by the agent. Schema completeness, crawlability, performance, and structured data coverage. The two frameworks are complementary, not competing. But they answer very different questions.

Finally, what this entire exercise is pointing to is the shift from active to passive product discovery. In traditional search, the user was hunting. They typed a query, scanned results, and clicked. In generative search, the user describes a need and the model decides what to surface. The retailer is no longer in a world where good SEO guarantees a chance to compete. The agent decides before the user ever sees the shelf.

That is the real structural change this research is trying to quantify.

More data coming as I get closer to thesis defense. If you are running these tests in your own stack, I would love to compare notes.

### References
1. Baeza-Yates, R., et al. (2024). *Search Engines in an AI Era: The false promise of factual and verifiable source-cited responses.* arXiv preprint arXiv:2410.22349.
2. Cheng, M., et al. (2025). *Sycophantic AI Decreases Prosocial Intentions and Promotes Dependence.* arXiv preprint arXiv:2510.01395.
3. Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* Advances in Neural Information Processing Systems (NeurIPS). arXiv preprint arXiv:2005.11401.
4. Mallen, A., et al. (2023). *When Not to Trust Language Models: Investigating Effectiveness of Parametric and Non-Parametric Memories.* Association for Computational Linguistics (ACL). arXiv preprint arXiv:2212.10511.

#GenerativeAI #EcommerceStrategy #SEO #ProductManagement #DataScience #LLM #RetailTech
