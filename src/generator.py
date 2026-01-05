import json
import os
from datetime import datetime
from src.collector import NewsletterContent

def generate_html(content: NewsletterContent) -> str:
    """Generates the HTML email content from NewsletterContent object."""
    
    # 🎨 STYLES & CSS
    # Using inline CSS for best email client compatibility
    font_family = "'Helvetica Neue', Helvetica, Arial, sans-serif"
    bg_color = "#f4f4f5"
    card_bg = "#ffffff"
    text_color = "#1f2937"
    accent_color = "#2563eb" # Blue
    accent_subtle = "#eff6ff"
    border_color = "#e5e7eb"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IA Newsletter - Semaine {content.week_number}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: {bg_color}; font-family: {font_family}; color: {text_color};">
        
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: {bg_color}; padding: 20px;">
            <tr>
                <td align="center">
                    
                    <!-- 📨 CONTAINER PRINCIPAL -->
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: {card_bg}; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                        
                        <!-- 🏷️ HEADER -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #111827; color: #ffffff; text-align: center;">
                                <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px;">🤖 IA HEBDOMADAIRE</h1>
                                <p style="margin: 10px 0 0 0; opacity: 0.8; font-size: 14px;">Semaine {content.week_number} • {content.date_start} - {content.date_end}</p>
                            </td>
                        </tr>

                        <!-- 🔥 HIGHLIGHT -->
                        <tr>
                            <td style="padding: 40px 40px 20px 40px; border-bottom: 1px solid {border_color};">
                                <span style="background-color: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 99px; font-size: 12px; font-weight: 700; text-transform: uppercase;">🔥 Le Game Changer</span>
                                <h2 style="margin: 15px 0 10px 0; font-size: 22px; color: #111827;">{content.highlight.name}</h2>
                                <p style="margin: 0 0 15px 0; line-height: 1.6; color: #4b5563;">{content.highlight.description}</p>
                                
                                <div style="background-color: {accent_subtle}; padding: 15px; border-radius: 8px; border-left: 4px solid {accent_color}; margin-top: 20px;">
                                    <p style="margin: 0 0 5px 0; font-weight: 700; color: {accent_color}; font-size: 13px;">💪 Impact Business</p>
                                    <p style="margin: 0; font-size: 14px;">{content.highlight.so_what}</p>
                                </div>
                            </td>
                        </tr>

                        <!-- 🇫🇷 FRANCE NEWS -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #ffffff;">
                                <h3 style="margin: 0 0 20px 0; font-size: 18px; border-bottom: 2px solid #ef4444; display: inline-block; padding-bottom: 5px;">🇫🇷 Focus France</h3>
    """
    
    for news in content.france_news:
        html += f"""
                                <div style="margin-bottom: 25px;">
                                    <h4 style="margin: 0 0 8px 0; font-size: 16px; color: #111827;">
                                        <a href="{news.url}" style="text-decoration: none; color: #111827; hover:text-decoration: underline;">{news.name} ↗</a>
                                    </h4>
                                    <p style="margin: 0 0 10px 0; font-size: 14px; color: #6b7280; line-height: 1.5;">{news.description}</p>
                                    <p style="margin: 0; font-size: 13px; color: #059669;"><strong>🎯 Action :</strong> {news.application}</p>
                                </div>
        """

    html += f"""
                            </td>
                        </tr>

                        <!-- 🌍 INTERNATIONAL -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f9fafb; border-top: 1px solid {border_color}; border-bottom: 1px solid {border_color};">
                                <h3 style="margin: 0 0 20px 0; font-size: 18px; color: #4b5563;">🌍 Radar International</h3>
                                <ul style="margin: 0; padding-left: 20px; color: #4b5563;">
    """
    
    for news in content.international_news:
        html += f"""
                                    <li style="margin-bottom: 10px; font-size: 14px; line-height: 1.5;">
                                        <strong>{news.name}</strong> : {news.description}
                                        <a href="{news.url}" style="color: {accent_color}; text-decoration: none; font-size: 12px; margin-left: 5px;">Lire ›</a>
                                    </li>
        """

    html += f"""
                                </ul>
                            </td>
                        </tr>

                        <!-- 🛠️ TOOL -->
                        <tr>
                            <td style="padding: 30px 40px;">
                                <div style="background-color: #1e1b4b; border-radius: 12px; padding: 25px; color: #ffffff;">
                                    <span style="background-color: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 600;">🛠️ L'Outil de la semaine</span>
                                    <h3 style="margin: 15px 0 10px 0; font-size: 20px;">{content.tool_of_the_week.name}</h3>
                                    <p style="margin: 0 0 20px 0; font-size: 14px; opacity: 0.9; line-height: 1.5;">{content.tool_of_the_week.description}</p>
                                    
                                    <div style="background-color: rgba(0,0,0,0.2); padding: 12px; border-radius: 6px; margin-bottom: 20px;">
                                        <p style="margin: 0; font-size: 13px;">💡 <strong>Cas d'usage :</strong> {content.tool_of_the_week.application}</p>
                                    </div>
                                    
                                    <center>
                                        <a href="{content.tool_of_the_week.url}" style="display: inline-block; background-color: #ffffff; color: #1e1b4b; padding: 12px 25px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 14px;">Essayer l'outil →</a>
                                    </center>
                                </div>
                            </td>
                        </tr>

                        <!-- 💡 TAKE AWAY -->
                        <tr>
                            <td style="padding: 30px 40px; text-align: center; border-top: 1px solid {border_color};">
                                <p style="margin: 0; font-size: 18px; font-style: italic; font-weight: 500; color: #4b5563;">" {content.take_away} "</p>
                            </td>
                        </tr>

                        <!-- FOOTER -->
                        <tr>
                            <td style="padding: 20px; background-color: #f3f4f6; text-align: center; font-size: 12px; color: #9ca3af;">
                                <p style="margin: 0;">Généré automatiquement par votre Agent IA Préféré ❤️</p>
                            </td>
                        </tr>
                        
                    </table>
                    
                </td>
            </tr>
        </table>
        
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    # Test with mock data
    try:
        with open("mock_data.json", "r") as f:
            data = json.load(f)
            # Conversion en objet NewsletterContent pour validation
            content = NewsletterContent(**data)
            
        html_output = generate_html(content)
        
        with open("preview.html", "w", encoding="utf-8") as f:
            f.write(html_output)
            
        print("✅ HTML Preview generated: preview.html")
    except Exception as e:
        print(f"❌ Error: {e}")
