Findings


I hope this article finds you well this monday.

Before talking about my findings on my search for the truth (I want to believe) on gemini I want to address some points because a friend just threw tomatoes at me for my mistake or misunderstood in the previous article. 

In this previous article I talked about paradoxes in Gemini. Maybe I don’t clarify that the paradox is from the user point of view. Google builds that using a design that you can open the sidebar, from google is a deliberated design decision, then from an architectural standpoint we don’t have paradox - the chat use the parametric memory + RAG web search and sidebar consumes shopping graph api + merchant center in a deterministic way - for the user maybe it is a little confusing.

These two independent subsystems running different search mechanics… I guess the user got conflicting recommendations and the retailer is wondering which surface to optimize and we have a lot of guesses about improving AI recommendations results and just one certainty that is we don’t know what is really happening. 

Well let’s go see what we have here.

The commercial LLMs are a bunch of black boxes. We don't know exactly what happens there, we just can infer and collect data, analyze data, hallucinate like them, and just think about what are the rules, guidance etc. 

Let's look, again, at Magalu. In my last article, I showed that Magazine Luiza had six inconsistent entries inside the Shopping Graph for the same query. We had three different snapshots of the same product, captured at different times, with varying shipping prices and delivery estimates. 

At the same time if we look at the Google Shopping result for the query: "iPhone 17 Pro laranja 256GB", Magalu disappeared from the results, just vanished, no result refers to Magalu. If you run the query today, competitors like iPlace, Fast Shop, Mercado Livre, and Carrefour are occupying the top slots. In fact, if I check Google Shopping right now, Magalu does not even appear on the first shelf for me.

![Screenshot](media/screenshot.png)

Why did they vanish? 

We have two main hypotheses for this:

First, it could be the integration of content controls like `data-nosnippet` or Google Merchant Center attributes like `pause: all`. Retailers can use `data-nosnippet` to exclude text from snippets, while the `pause` attribute with the value `all` temporarily excludes products from Google Shopping ads and free listings. If Magalu (or Google, automatically, due to bot validation issues) triggered these controls, the items would still reside in the backend database (the Shopping Graph) but would immediately vanish from the frontend Google Shopping interface. 

Second, it could be the natural rotation of the Shopping Graph. The graph is dynamic. Those inconsistent snapshots we documented in the last article are a sign of a feed that Google cannot reliably validate. If the system detects conflicting data points (like different delivery rates for the same product id), the algorithm rotates the options, penalizing the inconsistent merchant and pushing them down the rankings.

Is this an internal corporate silo issue, or is it an external Google algorithm shift? Genuinely, I don't know and I won't risk to give a guess. But it shows how fragile visibility is when security, feed health, and search engine updates collide without coordination.

I'm not sure what is more surprising, the fact that this happens, or the fact that this is happening live it looks like 'Google Magic' in action. 

### The Data Behind the Friction: 1,595 Ingestions

For this analysis, we cut our dataset at 1,595 total content extractions. We tracked seven specific PDPs across different stores, three times a day, using a crawler to retrieve content, schema markup, and pagespeed data, while CrUX metrics were collected 28 days apart. Although we focus on seven core pages, this is a longitudinal study where the real scale lies in the frequency of these extractions and the query responses. our database at USP tracks these 1,595 content extractions to analyze how Brazilian e-commerce sites handle search engine crawlers.

As we saw earlier, some retailers block bots completely. Magazine Luiza, Vivo, and Cosmetis have a 100% block rate in our tests. Mercado Livre is close behind at 99.6%, and Fastshop blocks 89.8% of crawlers. If the security team implements strict anti-bot measures, the crawlers never get to read the page.

On the other end, companies like Apple Brasil, Kabum, Natura, Americanas, and Boticário D2C have a 0% block rate. Their pages are fully accessible to crawlers, allowing search bots to parse schema data, verify prices, and validate stock in real-time.

Out of our 1,595 total content extractions, only about 783 were actually readable. The rest were blocked at the door.

When we look at the results, the connection is visible. If a retailer blocks bots at a 100% rate, the crawler cannot validate the page. If the search engine cannot validate the page, it has to rely on cached, potentially inconsistent snapshots in the Shopping Graph. And if the feed becomes too inconsistent, the algorithm rotates the options, penalizing the inconsistent merchant and pushing them down the rankings.

At least, that's what the data is suggesting.

But first, let's verify if we don't got a false positive with this 100%. How? We can verify if I got all the content and the schema from the pdp. I could got a 200 status code, but at the same time I just retrieve the menu or the PDP's header. From the list of 100% access-friendly we got a bad surprise from Americanas but I wonderful result from Kabum. The answer for the why is for another article. 

Let's see the queries results. I have some queries running and I analyzed the results. Remember that I use a query type parameter to control the behavior of the search engine. I have three types: `product_exact`, `brand`, and `generic`.

For `product_exact`, the query is the exact product name and model, for example: "iPhone 17 Pro 256GB preto titanio". In this case, the agent tries to search the web and cite specific stores. This is where PDP quality and crawlability actually matter for whether a store gets recommended or not.

For `brand`, the query is the brand name and category, for example: "iPhone 17 Pro" or "Boticario vitamina C". The behavior here splits depending on whether the product is recent or stable. For a stable skincare product, the agent behaves similarly to product_exact and cites stores. For a recent electronic, the knowledge cutoff kills the result before PDP quality even comes into play.

For `generic`, the query is category-level with no brand anchor, for example: "best vitamin C serum 2025" or "best smartphone camera 2025". Here something interesting happens. The agent stops trying to ground in real-time data and runs almost entirely on parametric memory. It recommends brands it learned during training. In our tests, none of the seven SKUs we monitor appeared in generic queries. The agent cited Garnier, Cerave, and other established brands instead, regardless of the PDP quality of the pages we were tracking.

This means that if your product is a generic category play without brand authority baked into the model's training data, no amount of schema optimization will make you visible to an AI agent running a generic query. The battle for generic queries is won or lost before the page even loads.
