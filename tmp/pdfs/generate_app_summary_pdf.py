from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf" / "readwise_app_summary.pdf"


def bullet_list(items: list[str], style: ParagraphStyle) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(item, style)) for item in items],
        bulletType="bullet",
        leftIndent=10,
        bulletFontName="Helvetica",
        bulletFontSize=8,
        bulletOffsetY=1,
        spaceBefore=0,
        spaceAfter=0,
    )


def build_pdf() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=0.48 * inch,
        rightMargin=0.48 * inch,
        topMargin=0.42 * inch,
        bottomMargin=0.42 * inch,
        title="ReadWise App Summary",
        author="OpenAI Codex",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#475569"),
        spaceAfter=6,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=0,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.4,
        leading=10.2,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=body_style,
        fontSize=8.1,
        leading=9.5,
        leftIndent=0,
        spaceBefore=0,
        spaceAfter=0.6,
    )
    mini_style = ParagraphStyle(
        "Mini",
        parent=body_style,
        fontSize=7.8,
        leading=9.1,
        textColor=colors.HexColor("#334155"),
        spaceAfter=2,
    )

    what_it_is = (
        "ReadWise is a Django web app for book discovery and recommendations. "
        "Repo docs and source show two recommendation paths: mood-based suggestions from sentiment analysis "
        "and deterministic dataset-based recommendations, plus search and category browsing."
    )

    who_its_for = (
        "Primary user: readers who want help finding books that match their current mood or interests."
    )

    features = [
        "Mood-based recommendations from free-text mood input, with optional \"improve mood\" behavior.",
        "Deterministic dataset recommender API backed by JSON datasets and inferred mood profiles.",
        "Book search across the local catalog with Google Books fallback results.",
        "Category and trending pages that merge cached local data with external book/category feeds.",
        "Book detail pages that resolve from the local database first, then Google Books by volume ID.",
        "User auth flows for signup, login/logout, Google OAuth, profile edit, and password change.",
        "REST API endpoints for categories, category books, and recommendation requests.",
    ]

    architecture = [
        "<b>Web layer:</b> <font color='#334155'>`readwise/urls.py` routes all traffic into `accounts.urls`; "
        "`accounts/views.py` serves templates and DRF API views.</font>",
        "<b>Core data:</b> <font color='#334155'>`accounts/models.py` stores books, authors, genres, and categories; "
        "local dev uses SQLite, while `DATABASE_URL` switches production to PostgreSQL.</font>",
        "<b>Recommendation services:</b> <font color='#334155'>`accounts/services/mood_recommender.py`, "
        "`dataset_recommender.py`, and sentiment modules score books from mood text and dataset metadata.</font>",
        "<b>External services:</b> <font color='#334155'>`google_books.py` calls Google Books; "
        "`external.py` pulls category/book feeds from Google Books and Open Library.</font>",
        "<b>Data flow:</b> <font color='#334155'>browser/API request -> Django view/API -> local DB and/or service module -> "
        "optional cache/external fetch -> normalized book cards or JSON response -> template/API output.</font>",
    ]

    how_to_run = [
        "Create and activate a virtual environment: `python -m venv venv` then `venv\\Scripts\\activate` on Windows.",
        "Install dependencies: `pip install -r requirements.txt`.",
        "Create `.env` from `.env.example`; required values shown there include `SECRET_KEY`, `DEBUG`, Google OAuth keys, and `DATABASE_URL`.",
        "Run migrations: `python manage.py migrate`.",
        "Start the app: `python manage.py runserver`.",
    ]

    left_story = [
        Paragraph("ReadWise", title_style),
        Paragraph("Evidence-backed one-page app summary", subtitle_style),
        Paragraph("What It Is", section_style),
        Paragraph(what_it_is, body_style),
        Paragraph("Who It's For", section_style),
        Paragraph(who_its_for, body_style),
        Paragraph("What It Does", section_style),
        bullet_list(features, bullet_style),
    ]

    right_story = [
        Paragraph("How It Works", section_style),
        bullet_list(architecture, bullet_style),
        Spacer(1, 4),
        Paragraph("How To Run", section_style),
        bullet_list(how_to_run, bullet_style),
        Spacer(1, 5),
        Paragraph(
            "Not found in repo: no explicit product owner, target organization, or formal system diagram.",
            mini_style,
        ),
    ]

    table = Table(
        [[left_story, right_story]],
        colWidths=[3.65 * inch, 3.55 * inch],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    card = Table(
        [[table]],
        colWidths=[7.36 * inch],
    )
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
                ("ROUNDEDCORNERS", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    doc.build([card])
    return OUTPUT


if __name__ == "__main__":
    print(build_pdf())
