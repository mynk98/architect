from ddgs import DDGS

def web_search(query):
    try:
        results = []
        with DDGS() as ddgs:
            # 1. Text search - use query as first positional argument for ddgs 9.10.0
            try:
                search_results = list(ddgs.text(query, max_results=8))
                if search_results:
                    for r in search_results:
                        results.append(f"Title: {r.get('title')}\nLink: {r.get('href')}\nSnippet: {r.get('body')}\n")
            except Exception as e:
                print(f"DEBUG: Text search failed: {e}")
            
            # 2. News search
            try:
                news_results = list(ddgs.news(query, max_results=5))
                if news_results:
                    for r in news_results:
                        results.append(f"Title: {r.get('title')}\nLink: {r.get('url') or r.get('href')}\nSnippet: {r.get('body')}\nSource: {r.get('source')}\n")
            except Exception as e:
                print(f"DEBUG: News search failed: {e}")

        if not results:
            return f"No results found for: {query}. Try a different query."
            
        return "\n---\n".join(results[:12])
    except Exception as e:
        return f"Error searching the web: {str(e)}"
