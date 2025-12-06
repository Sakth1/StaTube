import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

from PySide6.QtGui import QImage, QPainter, QColor, QFont, Qt
from PySide6.QtCore import QRectF


def ensure_vader():
    try:
        nltk.data.find("sentiment/vader_lexicon.zip")
    except LookupError:
        nltk.download("vader_lexicon")


class SentimentSummaryRenderer:

    def __init__(self, width=1600, height=520, radius=20):
        self.width = int(width)
        self.height = int(height)
        self.radius = radius

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

        if score > 0.6:
            return "Overwhelmingly Positive"
        if score > 0.3:
            return "Positive"
        if score > 0.05:
            return "Slightly Positive"
        if score > -0.05:
            return "Neutral"
        if score > -0.3:
            return "Negative"
        if score > -0.6:
            return "Strongly Negative"
        return "Overwhelmingly Negative"

    def render_summary(self, positive: int, neutral: int, negative: int) -> QImage:
        img = QImage(self.width, self.height, QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)

        # shadow
        shadow_rect = QRectF(10, 10, self.width - 20, self.height - 20)
        painter.setBrush(self.card_shadow)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(shadow_rect, self.radius, self.radius)

        # background card
        bg_rect = QRectF(0, 0, self.width - 20, self.height - 20)
        painter.setBrush(self.bg_color)
        painter.drawRoundedRect(bg_rect, self.radius, self.radius)

        # Title
        painter.setPen(QColor(120, 120, 120))
        painter.setFont(QFont("Segoe UI", max(12, int(self.width * 0.012))))
        painter.drawText(30, int(self.height * 0.09), "COMMUNITY SENTIMENT")

        # Label
        label = self.compute_label(positive, negative, neutral)
        painter.setPen(QColor(20, 20, 20))
        painter.setFont(QFont("Segoe UI", max(18, int(self.width * 0.026)), QFont.Bold))
        painter.drawText(30, int(self.height * 0.20), label)

        # bar
        total = max(positive + neutral + negative, 1)

        bar_x = 30
        bar_y = int(self.height * 0.30)
        bar_width = self.width - 80
        bar_height = int(self.height * 0.12)

        neg_w = bar_width * (negative / total)
        neu_w = bar_width * (neutral / total)
        pos_w = bar_width * (positive / total)

        painter.setBrush(self.negative_color)
        painter.drawRoundedRect(QRectF(bar_x, bar_y, neg_w, bar_height), 10, 10)

        painter.setBrush(self.neutral_color)
        painter.drawRect(QRectF(bar_x + neg_w, bar_y, neu_w, bar_height))

        painter.setBrush(self.positive_color)
        painter.drawRoundedRect(QRectF(bar_x + neg_w + neu_w, bar_y, pos_w, bar_height), 10, 10)

        # bottom labels
        painter.setFont(QFont("Segoe UI", max(12, int(self.width * 0.012))))

        painter.setPen(self.negative_color)
        painter.drawText(bar_x, bar_y + int(self.height * 0.30), f"😡 Negative: {negative}")

        painter.setPen(self.neutral_color)
        painter.drawText(bar_x + int(self.width * 0.28), bar_y + int(self.height * 0.30), f"😐 Neutral: {neutral}")

        painter.setPen(self.positive_color)
        painter.drawText(bar_x + int(self.width * 0.56), bar_y + int(self.height * 0.30), f"😊 Positive: {positive}")

        painter.end()
        return img


def run_sentiment_summary(sentences, width: int | None = None, height: int | None = None):
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

    if width is None:
        width = 1600
    if height is None:
        height = int(width * 0.33)

    renderer = SentimentSummaryRenderer(width=width, height=height)
    return renderer.render_summary(positive, neutral, negative)
