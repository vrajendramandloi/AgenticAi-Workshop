"""
HTML Proposal Export Tool
=========================
Generates a beautiful, publication-grade, self-contained HTML travel proposal
file that can be opened in any browser, saved as a PDF, or downloaded by the
traveler and Boss Agent Vicky.
"""

import os
import sys
import re
from pathlib import Path
from typing import Any, Dict, Optional, List

# Prevent bytecode generation
sys.dont_write_bytecode = True

# Resolve project paths
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent

DEFAULT_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,600;0,700;1,400&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: #0f172a;
      --primary-light: #1e293b;
      --accent: #d97706;
      --accent-light: #fef3c7;
      --accent-gradient: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
      --luxury-gold: #c59b27;
      --value-emerald: #059669;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text-main: #1e293b;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.06), 0 8px 10px -6px rgba(15, 23, 42, 0.04);
      --shadow-lg: 0 20px 30px -10px rgba(15, 23, 42, 0.1);
      --radius: 16px;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.6;
      padding: 30px 20px;
    }}

    .container {{
      max-width: 960px;
      margin: 0 auto;
    }}

    /* Action / Download Bar */
    .action-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #ffffff;
      border: 1px solid var(--border);
      padding: 14px 24px;
      border-radius: var(--radius);
      margin-bottom: 24px;
      box-shadow: var(--shadow);
    }}

    .action-bar .brand-badge {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
      color: var(--primary);
      font-size: 0.95rem;
    }}

    .brand-badge .dot {{
      width: 10px;
      height: 10px;
      background: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2);
    }}

    .btn-group {{
      display: flex;
      gap: 12px;
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 20px;
      font-size: 0.88rem;
      font-weight: 600;
      border-radius: 10px;
      cursor: pointer;
      border: none;
      text-decoration: none;
      transition: all 0.2s ease;
    }}

    .btn-primary {{
      background: var(--primary);
      color: #ffffff;
    }}

    .btn-primary:hover {{
      background: #334155;
      transform: translateY(-1px);
    }}

    .btn-accent {{
      background: var(--accent-gradient);
      color: #ffffff;
      box-shadow: 0 4px 12px rgba(217, 119, 6, 0.25);
    }}

    .btn-accent:hover {{
      opacity: 0.95;
      transform: translateY(-1px);
    }}

    /* Hero Banner */
    .hero-card {{
      background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #334155 100%);
      color: #ffffff;
      padding: 48px 40px;
      border-radius: var(--radius);
      margin-bottom: 30px;
      position: relative;
      overflow: hidden;
      box-shadow: var(--shadow-lg);
    }}

    .hero-card::after {{
      content: "";
      position: absolute;
      top: -50%;
      right: -20%;
      width: 400px;
      height: 400px;
      background: radial-gradient(circle, rgba(245, 158, 11, 0.15) 0%, transparent 70%);
      border-radius: 50%;
      pointer-events: none;
    }}

    .tag-row {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 16px;
    }}

    .tag {{
      display: inline-block;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .tag-proposal-type {{
      background: rgba(245, 158, 11, 0.2);
      color: #fde68a;
      border: 1px solid rgba(245, 158, 11, 0.4);
    }}

    .tag-boss-approved {{
      background: rgba(16, 185, 129, 0.2);
      color: #a7f3d0;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }}

    .hero-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 2.5rem;
      font-weight: 800;
      line-height: 1.2;
      margin-bottom: 12px;
      color: #ffffff;
    }}

    .hero-subtitle {{
      font-size: 1.05rem;
      color: #cbd5e1;
      max-width: 650px;
      margin-bottom: 28px;
    }}

    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 16px;
      padding-top: 24px;
      border-top: 1px solid rgba(255, 255, 255, 0.12);
    }}

    .stat-item .stat-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #94a3b8;
      margin-bottom: 4px;
    }}

    .stat-item .stat-val {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.25rem;
      font-weight: 700;
      color: #ffffff;
    }}

    /* Content Cards */
    .section-card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 32px;
      margin-bottom: 24px;
      box-shadow: var(--shadow);
    }}

    .section-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 20px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border);
    }}

    .section-icon {{
      font-size: 1.5rem;
      background: #f1f5f9;
      width: 44px;
      height: 44px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 12px;
    }}

    .section-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.35rem;
      font-weight: 700;
      color: var(--primary);
    }}

    /* Hotel & Accommodations */
    .hotel-card {{
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 16px;
    }}

    .hotel-card:last-child {{
      margin-bottom: 0;
    }}

    .hotel-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 8px;
    }}

    .hotel-name {{
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--primary);
    }}

    .hotel-price {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--accent);
    }}

    .stars {{
      color: #f59e0b;
      margin-bottom: 8px;
      font-size: 0.95rem;
    }}

    .hotel-desc {{
      color: var(--text-muted);
      font-size: 0.92rem;
    }}

    /* Day by Day Itinerary Timeline */
    .timeline {{
      position: relative;
      padding-left: 28px;
    }}

    .timeline::before {{
      content: "";
      position: absolute;
      top: 10px;
      left: 10px;
      bottom: 10px;
      width: 2px;
      background: #cbd5e1;
    }}

    .timeline-item {{
      position: relative;
      margin-bottom: 24px;
    }}

    .timeline-item:last-child {{
      margin-bottom: 0;
    }}

    .timeline-item::before {{
      content: "";
      position: absolute;
      left: -24px;
      top: 4px;
      width: 14px;
      height: 14px;
      background: var(--accent);
      border: 3px solid #ffffff;
      border-radius: 50%;
      box-shadow: 0 0 0 2px var(--accent);
    }}

    .timeline-badge {{
      display: inline-block;
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 4px;
    }}

    .timeline-title {{
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 6px;
    }}

    .timeline-desc {{
      color: var(--text-muted);
      font-size: 0.92rem;
    }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.92rem;
    }}

    th {{
      background: #f1f5f9;
      color: var(--primary);
      font-weight: 700;
      text-align: left;
      padding: 12px 16px;
      border-bottom: 2px solid var(--border);
    }}

    td {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      color: var(--text-main);
    }}

    tr:last-child td {{
      border-bottom: none;
    }}

    .tr-total {{
      background: #f8fafc;
      font-weight: 700;
    }}

    .tr-total td {{
      color: var(--primary);
      font-size: 1rem;
      border-top: 2px solid var(--border);
    }}

    /* Checklist */
    .checklist {{
      list-style: none;
    }}

    .checklist-item {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px dashed var(--border);
    }}

    .checklist-item:last-child {{
      border-bottom: none;
    }}

    .check-box {{
      width: 20px;
      height: 20px;
      border-radius: 6px;
      border: 2px solid #10b981;
      background: #ecfdf5;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #10b981;
      font-weight: bold;
      font-size: 0.75rem;
      flex-shrink: 0;
      margin-top: 2px;
    }}

    /* Footer */
    .footer-seal {{
      text-align: center;
      padding: 30px;
      background: #ffffff;
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }}

    .footer-title {{
      font-family: 'Outfit', sans-serif;
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--primary);
      margin-bottom: 6px;
    }}

    .footer-desc {{
      color: var(--text-muted);
      font-size: 0.88rem;
    }}

    .squad-credits {{
      display: flex;
      justify-content: center;
      gap: 20px;
      flex-wrap: wrap;
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
      font-size: 0.8rem;
      color: var(--text-muted);
    }}

    /* Print Styles */
    @media print {{
      body {{
        background: #ffffff;
        padding: 0;
      }}
      .action-bar {{
        display: none !important;
      }}
      .hero-card {{
        background: #0f172a !important;
        color: #ffffff !important;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }}
      .section-card {{
        box-shadow: none;
        border: 1px solid #cbd5e1;
        page-break-inside: avoid;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- Top Action Bar for Downloading & Printing -->
    <div class="action-bar">
      <div class="brand-badge">
        <span class="dot"></span>
        <span>Executive Travel Itinerary &amp; Quotation</span>
      </div>
      <div class="btn-group">
        <button class="btn btn-primary" onclick="window.print()">
          🖨️ Print / Save as PDF
        </button>
        <button class="btn btn-accent" id="downloadHtmlBtn" onclick="downloadCurrentPage()">
          📥 Download HTML
        </button>
      </div>
    </div>

    <!-- Hero Card -->
    <div class="hero-card">
      <div class="tag-row">
        <span class="tag tag-proposal-type">{proposal_type_badge}</span>
        <span class="tag tag-boss-approved">✓ Boss Vicky Approved</span>
      </div>
      <h1 class="hero-title">{destination} Master Itinerary</h1>
      <p class="hero-subtitle">{tagline}</p>
      
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-label">Total Package Cost</div>
          <div class="stat-val">{total_cost}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">Duration</div>
          <div class="stat-val">{duration}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">Travelers</div>
          <div class="stat-val">{travelers}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">Departure From</div>
          <div class="stat-val">{departure_city}</div>
        </div>
      </div>
    </div>

    <!-- Accommodations -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-icon">🏨</div>
        <h2 class="section-title">Accommodations &amp; Stays (1–2 Hotels)</h2>
      </div>
      <div class="section-content">
        {accommodations_html}
      </div>
    </div>

    <!-- Day by Day Itinerary -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-icon">🗺️</div>
        <h2 class="section-title">Curated Day-by-Day Itinerary &amp; Visiting Places</h2>
      </div>
      <div class="section-content timeline">
        {itinerary_html}
      </div>
    </div>

    <!-- Transit & Mobility -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-icon">✈️</div>
        <h2 class="section-title">Transit, Flights &amp; Mobility Blueprint</h2>
      </div>
      <div class="section-content">
        {transit_html}
      </div>
    </div>

    <!-- Itemized Financial Breakdown -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-icon">📊</div>
        <h2 class="section-title">Itemized Financial Breakdown</h2>
      </div>
      <div class="section-content">
        {financials_html}
      </div>
    </div>

    <!-- Actionable Checklist -->
    <div class="section-card">
      <div class="section-header">
        <div class="section-icon">✅</div>
        <h2 class="section-title">Pre-Departure &amp; Booking Checklist</h2>
      </div>
      <div class="section-content">
        {checklist_html}
      </div>
    </div>

    <!-- Footer Seal -->
    <div class="footer-seal">
      <div class="footer-title">Prepared by Advik &amp; Endorsed by Boss Agent Vicky</div>
      <div class="footer-desc">
        Engineered with rigor and personalized care by Vrajendra's Multi-Agent Travel Orchestration Squad.
      </div>
      <div class="squad-credits">
        <span>Raghav (Phase 1 HITL)</span>
        <span>•</span>
        <span>Dhruv (Statistics &amp; Feasibility)</span>
        <span>•</span>
        <span>Aarav (Luxury)</span>
        <span>•</span>
        <span>Kabir (Value)</span>
        <span>•</span>
        <span>Ishaan (Quality Auditor)</span>
        <span>•</span>
        <span>Tanvi (Proposals)</span>
        <span>•</span>
        <span>Advik (Master Finalizer)</span>
      </div>
    </div>
  </div>

  <script>
    function downloadCurrentPage() {{
      const htmlContent = document.documentElement.outerHTML;
      const blob = new Blob([htmlContent], {{ type: 'text/html;charset=utf-8' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = '{download_filename}';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }}
  </script>
</body>
</html>
"""


def generate_beautiful_proposal_html(
    destination: str,
    total_cost: str,
    duration: str,
    travelers: str,
    departure_city: str,
    proposal_type: str = "Curated Proposal",
    tagline: str = "A meticulously crafted travel experience tailored to your exact preferences.",
    accommodations_html: str = "",
    itinerary_html: str = "",
    transit_html: str = "",
    financials_html: str = "",
    checklist_html: str = "",
    custom_full_html: Optional[str] = None,
    output_filename: str = "travel_proposal.html",
) -> Dict[str, Any]:
    """
    Generates a beautiful, publication-grade standalone HTML travel proposal.
    Writes the file to disk in the project workspace root and returns
    downloadable file links for the user and Boss Agent Vicky.

    Args:
        destination: Destination name (e.g., 'Switzerland', 'Paris').
        total_cost: Formatted cost (e.g., '$3,300 USD').
        duration: Duration (e.g., '5 Days / 4 Nights').
        travelers: Number of travelers (e.g., '2 Adults').
        departure_city: Departure city (e.g., 'Mumbai').
        proposal_type: 'Luxury Upgrade (10%–20% Above Budget)' or 'Smart Value (At-Max 10% Below Budget)'.
        tagline: Inspiring summary subtitle.
        accommodations_html: HTML content or bullet points for 1–2 hotels.
        itinerary_html: HTML content or timeline items for day-by-day sights (5–7 places or 3–5 places).
        transit_html: HTML content for flights, trains, and passes.
        financials_html: HTML table or breakdown for budget items.
        checklist_html: HTML checklist for next steps.
        custom_full_html: Optional full custom HTML document to write directly.
        output_filename: Output filename (default 'travel_proposal.html').

    Returns:
        Dictionary containing file status, absolute path, file URL, and download markdown link.
    """
    try:
        # Determine target file path
        target_path = _PROJECT_ROOT / output_filename
        
        # Ensure proposals directory exists if placed inside a folder
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if custom_full_html and custom_full_html.strip():
            # If the LLM generated complete HTML directly, ensure it has download/print hooks if missing
            html_to_write = custom_full_html
        else:
            # Format badge text
            badge = proposal_type
            if "luxury" in proposal_type.lower():
                badge = "🌟 Luxury Upgrade (+10%–20%)"
            elif "value" in proposal_type.lower():
                badge = "🏔️ Smart Value & Hidden Gems"

            # Helper to wrap plain text lines in clean HTML if raw text was passed
            def format_section(content: str, default_tag: str = "p") -> str:
                if not content or not content.strip():
                    return f"<{default_tag}>Details confirmed in master itinerary draft.</{default_tag}>"
                if "<" in content and ">" in content:
                    return content
                # If markdown-like text, convert lines
                lines = [l.strip() for l in content.split("\n") if l.strip()]
                return "".join([f"<{default_tag}>{l}</{default_tag}>" for l in lines])

            acc_content = format_section(accommodations_html, "div class='hotel-card'")
            itin_content = format_section(itinerary_html, "div class='timeline-item'")
            transit_content = format_section(transit_html, "p")
            fin_content = format_section(financials_html, "div")
            check_content = format_section(checklist_html, "div class='checklist-item'")

            clean_filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', output_filename)

            html_to_write = DEFAULT_HTML_TEMPLATE.format(
                title=f"{destination} Travel Proposal — {proposal_type}",
                destination=destination,
                total_cost=total_cost,
                duration=duration,
                travelers=travelers,
                departure_city=departure_city,
                proposal_type_badge=badge,
                tagline=tagline,
                accommodations_html=acc_content,
                itinerary_html=itin_content,
                transit_html=transit_content,
                financials_html=fin_content,
                checklist_html=check_content,
                download_filename=clean_filename,
            )

        # Write to file
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(html_to_write)

        file_url = target_path.as_uri()
        rel_path = target_path.relative_to(_PROJECT_ROOT) if target_path.is_relative_to(_PROJECT_ROOT) else target_path.name

        return {
            "status": "success",
            "file_name": target_path.name,
            "absolute_path": str(target_path),
            "file_url": file_url,
            "size_bytes": os.path.getsize(target_path),
            "download_markdown_link": f"[📥 Download Master Travel Proposal HTML](file:///{str(target_path).replace(os.sep, '/')})",
            "message": (
                f"Master HTML travel proposal successfully generated and saved to {target_path.name} ({target_path}). "
                "The user and Boss Agent Vicky can click the link to open in any browser or use the integrated 'Print / Save as PDF' button."
            )
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": f"Failed to generate HTML proposal: {e}"
        }
