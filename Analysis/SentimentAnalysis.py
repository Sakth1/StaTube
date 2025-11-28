"""
sentiment_summary_renderer.py

Integrated sentiment analysis + PySide6 renderer.
Call:
    img = run_sentiment_summary(sentences)

This:
    - Ensures VADER is available
    - Runs sentiment analysis
    - Counts positive / neutral / negative
    - Renders the final summary card (QImage)
"""

import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

from PySide6.QtGui import (
    QImage, QPainter, QColor, QFont, Qt
)
from PySide6.QtCore import QRectF


# ---------------------------------------------------------
# Setup VADER Sentiment
# ---------------------------------------------------------
def ensure_vader():
    """Ensure the VADER lexicon is installed."""
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon")


# ---------------------------------------------------------
# Sentiment Renderer Class
# ---------------------------------------------------------
class SentimentSummaryRenderer:

    def __init__(self, width=900, height=300, radius=25):
        self.width = width
        self.height = height
        self.radius = radius

        # Theme colors
        self.bg_color = QColor(255, 255, 255)
        self.card_shadow = QColor(0, 0, 0, 30)

        self.positive_color = QColor("#4CAF50")
        self.neutral_color = QColor("#FFC107")
        self.negative_color = QColor("#F44336")

    def compute_label(self, p, n, u):
        total = p + n + u
        if total == 0:
            return "No Data"

        score = (p - n) / total

        if score > 0.6: return "Overwhelmingly Positive"
        if score > 0.3: return "Positive"
        if score > 0.05: return "Slightly Positive"
        if score > -0.05: return "Neutral"
        if score > -0.3: return "Negative"
        if score > -0.6: return "Strongly Negative"
        return "Overwhelmingly Negative"

    # ---------------------------------------------------------
    # Render Sentiment Summary → returns QImage
    # ---------------------------------------------------------
    def render_summary(self, positive: int, neutral: int, negative: int) -> QImage:
        img = QImage(self.width, self.height, QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)

        # Card shadow
        shadow_rect = QRectF(10, 10, self.width - 20, self.height - 20)
        painter.setBrush(self.card_shadow)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(shadow_rect, self.radius, self.radius)

        # Card background
        bg_rect = QRectF(0, 0, self.width - 20, self.height - 20)
        painter.setBrush(self.bg_color)
        painter.drawRoundedRect(bg_rect, self.radius, self.radius)

        # Title
        painter.setPen(QColor(120, 120, 120))
        painter.setFont(QFont("Segoe UI", 14))
        painter.drawText(30, 45, "COMMUNITY SENTIMENT")

        # Main label
        label = self.compute_label(positive, negative, neutral)
        painter.setPen(QColor(20, 20, 20))
        painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
        painter.drawText(30, 90, label)

        # Sentiment bar
        total = max(positive + neutral + negative, 1)

        bar_x = 30
        bar_y = 120
        bar_width = self.width - 80
        bar_height = 30

        neg_w = bar_width * (negative / total)
        neu_w = bar_width * (neutral / total)
        pos_w = bar_width * (positive / total)

        # Negative
        painter.setBrush(self.negative_color)
        painter.drawRoundedRect(QRectF(bar_x, bar_y, neg_w, bar_height), 10, 10)

        # Neutral (flat bar)
        painter.setBrush(self.neutral_color)
        painter.drawRect(QRectF(bar_x + neg_w, bar_y, neu_w, bar_height))

        # Positive
        painter.setBrush(self.positive_color)
        painter.drawRoundedRect(
            QRectF(bar_x + neg_w + neu_w, bar_y, pos_w, bar_height),
            10, 10
        )

        # Bottom text
        painter.setFont(QFont("Segoe UI", 14))

        painter.setPen(self.negative_color)
        painter.drawText(bar_x, bar_y + 80, f"😡 Negative: {negative}")

        painter.setPen(self.neutral_color)
        painter.drawText(bar_x + 250, bar_y + 80, f"😐 Neutral: {neutral}")

        painter.setPen(self.positive_color)
        painter.drawText(bar_x + 500, bar_y + 80, f"😊 Positive: {positive}")

        painter.end()
        return img


# ---------------------------------------------------------
# 🔥 Integrated Function — Call Only This
# ---------------------------------------------------------
def run_sentiment_summary(sentences) -> QImage:
    """
    Full pipeline:
        - ensure VADER lexicon
        - run VADER sentiment
        - count positive/neutral/negative
        - render QImage summary card
    """
    ensure_vader()
    vader = SentimentIntensityAnalyzer()

    positive = neutral = negative = 0

    for s in sentences:
        score = vader.polarity_scores(s)["compound"]
        if score >= 0.05:
            positive += 1
        elif score <= -0.05:
            negative += 1
        else:
            neutral += 1

    renderer = SentimentSummaryRenderer()
    return renderer.render_summary(positive, neutral, negative)
