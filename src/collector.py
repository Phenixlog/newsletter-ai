import os
import json
import time
from enum import Enum
from typing import List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
from anthropic import Anthropic
from pydantic import BaseModel, Field, validator
from duckduckgo_search import DDGS

# Load env vars
load_dotenv()

class NewsCategory(str, Enum):
    HIGHLIGHT = "highlight"
    FRANCE = "france"
    INTERNATIONAL = "international"
    TOOL = "tool"
    UNKNOWN = "unknown"

class NewsItem(BaseModel):
    category: NewsCategory = Field(default=NewsCategory.UNKNOWN)
    name: str = Field(description="Titre accrocheur", alias="title")
    description: str = Field(description="Résumé court")
    url: Optional[str] = Field(None, description="Lien source", alias="link")
    so_what: str = Field(description="Pourquoi c'est important", alias="impact")
    application: str = Field(description="Actionnable", alias="action")
    source_name: Optional[str] = Field(None, description="Nom de la source")
    date_published: Optional[str] = Field(None, description="Date de publication trouvée")

    class Config:
        populate_by_name = True

class NewsletterContent(BaseModel):
    week_number: int
    date_start: str
    date_end: str
    highlight: NewsItem
    france_news: List[NewsItem]
    international_news: List[NewsItem]
    tool_of_the_week: NewsItem
    take_away: str = Field(description="La phrase clé")

    @validator('highlight')
    def set_highlight_cat(cls, v):
        v.category = NewsCategory.HIGHLIGHT
        return v
        
    @validator('france_news', each_item=True)
    def set_france_cat(cls, v):
        v.category = NewsCategory.FRANCE
        return v
        
    @validator('international_news', each_item=True)
    def set_intl_cat(cls, v):
        v.category = NewsCategory.INTERNATIONAL
        return v

    @validator('tool_of_the_week')
    def set_tool_cat(cls, v):
        v.category = NewsCategory.TOOL
        return v

class AINewsCollector:
    def __init__(self, config: dict = None):
        """
        Initialize the collector with optional newsletter config.
        Config can contain: theme, keywords, tone, language, name
        """
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
        self.model = "claude-sonnet-4-5-20250929"
        self.ddgs = DDGS()
        
        # Dynamic config with defaults
        self.config = config or {}
        self.theme = self.config.get('theme', 'Intelligence Artificielle, Machine Learning, LLM')
        self.keywords = self.config.get('keywords', ['IA', 'intelligence artificielle', 'OpenAI', 'Anthropic'])
        self.tone = self.config.get('tone', 'professionnel')
        self.language = self.config.get('language', 'fr')
        self.newsletter_name = self.config.get('name', 'IA Hebdo')

    def get_date_range(self):
        """Calculates the date range: Monday of previous week to Monday of current week."""
        today = datetime.now()
        days_since_monday = today.weekday()
        current_monday = today - timedelta(days=days_since_monday)
        previous_monday = current_monday - timedelta(days=7)
        return previous_monday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    def build_search_queries(self, start_date: str, end_date: str) -> List[str]:
        """Build search queries based on newsletter config."""
        base_keywords = ' '.join(self.keywords[:4])  # Use first 4 keywords
        queries = [
            f"actualités {base_keywords} France business {start_date}..{end_date}",
            f"nouvelles {base_keywords} impact business",
            f"nouveaux outils productivité {self.keywords[0]} business"
        ]
        return queries

    def search_web(self, queries: List[str], max_results=10) -> str:
        context = ""
        for query in queries:
            print(f"🔎 Searching: {query}...")
            try:
                results = self.ddgs.news(keywords=query, max_results=max_results, safesearch='off', region="fr-fr", timelimit='w')
                if results:
                    context += f"\n=== RÉSULTATS '{query}' ===\n"
                    for res in results:
                        context += f"- TITRE: {res.get('title')} | SOURCE: {res.get('source')} | DATE: {res.get('date')}\n"
                        context += f"  INFOS: {res.get('body')}\n  URL: {res.get('url')}\n\n"
                time.sleep(10)
            except Exception as e:
                print(f"⚠️ Error: {e}")
        return context

    def collect_and_analyze(self) -> NewsletterContent:
        start_date, end_date = self.get_date_range()
        start_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_obj = datetime.strptime(end_date, "%Y-%m-%d")
        
        print(f"🚀 [{self.newsletter_name}] Filtering News between {start_date} and {end_date}")
        print(f"📌 Theme: {self.theme}")

        queries = self.build_search_queries(start_date, end_date)

        raw_context = self.search_web(queries)
        if not raw_context:
            raise Exception("No fresh results found via DuckDuckGo.")
        
        print(f"🧠 [{self.newsletter_name}] Analyzing data with Claude 4.5 Sonnet...")
        
        # Dynamic system prompt based on config
        tone_instruction = {
            'professionnel': 'Utilise un ton professionnel et factuel.',
            'casual': 'Utilise un ton décontracté et accessible.',
            'technique': 'Utilise un ton technique avec des détails précis.'
        }.get(self.tone, 'Utilise un ton professionnel.')

        system_prompt = f"""
        Tu es un analyste Senior spécialisé en {self.theme}. Nous sommes le {datetime.now().strftime('%d/%m/%Y')}.
        Génère le contenu de la newsletter "{self.newsletter_name}" pour la période du {start_obj.strftime('%d/%m/%Y')} au {end_obj.strftime('%d/%m/%Y')}.
        
        THÉMATIQUE: {self.theme}
        TON: {tone_instruction}
        LANGUE: {'Français' if self.language == 'fr' else 'English'}

        RÈGLES DE SÉLECTION STRICTES :
        - Les infos DOIVENT être publiées après le {start_obj.strftime('%d/%m/%Y')}.
        - IGNORE toute news historique (ex: Mistral sept 2025).
        - Sois précis sur les dates.

        RÈGLE SPÉCIALE POUR "tool_of_the_week" :
        - Ce doit être un VRAI OUTIL IA (SaaS, app, API, extension).
        - Le champ "link" DOIT être l'URL OFFICIELLE du site de l'outil (ex: https://outil.com), PAS un article de blog qui en parle.
        - Exemples valides: Perplexity, Notion AI, Cursor, v0.dev, Claude, Midjourney, etc.
        - Si tu trouves un outil mentionné dans un article, donne le lien DIRECT vers le site de l'outil.

        FORMAT JSON REQUIS (STRICT) :
        {{
            "week_number": int,
            "date_start": "string",
            "date_end": "string",
            "highlight": {{
                "title": "nom",
                "description": "résumé",
                "link": "url article source",
                "impact": "so what",
                "action": "application",
                "source_name": "nom source",
                "date_published": "date"
            }},
            "france_news": [ {{ ... same fields ... }} ],
            "international_news": [ {{ ... same fields ... }} ],
            "tool_of_the_week": {{
                "title": "Nom de l'outil",
                "description": "Ce que fait l'outil",
                "link": "URL OFFICIELLE du site de l'outil (PAS un article)",
                "impact": "Pourquoi c'est utile",
                "action": "Comment l'utiliser en entreprise"
            }},
            "take_away": "string"
        }}
        """

        user_prompt = f"RÉSULTATS DE VEILLE FRAIS :\n{raw_context}\n\nGénère le contenu JSON."

        if not self.client:
           raise ValueError("API Key missing.")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        response_text = message.content[0].text
        
        try:
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            else:
                start = response_text.find("{")
                end = response_text.rfind("}")
                if start != -1 and end != -1:
                    response_text = response_text[start:end+1]
        except Exception:
            pass
        
        try:
            return NewsletterContent(**json.loads(response_text))
        except Exception as e:
            print(f"❌ Validation Error: {e}")
            with open("error_payload.json", "w") as f:
                f.write(response_text)
            raise

if __name__ == "__main__":
    c = AINewsCollector()
    res = c.collect_and_analyze()
    print(res.model_dump_json(indent=2))
