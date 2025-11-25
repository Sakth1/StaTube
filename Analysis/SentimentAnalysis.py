"""
sentiment_summary_renderer.py

Pure PySide6 sentiment summary renderer.
Creates a modern card-style sentiment visualization and returns QImage.

Test block at bottom:
    - Runs VADER on a list of sentences
    - Counts positive/neutral/negative
    - Renders summary card
    - Saves output as 'sentiment_preview.png'
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
    # Render the Sentiment Card → returns QImage
    # ---------------------------------------------------------
    def render_summary(self, positive: int, neutral: int, negative: int) -> QImage:
        img = QImage(self.width, self.height, QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)

        # ---------------------------
        # Card shadow
        # ---------------------------
        shadow_rect = QRectF(10, 10, self.width - 20, self.height - 20)
        painter.setBrush(self.card_shadow)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(shadow_rect, self.radius, self.radius)

        # ---------------------------
        # Card background
        # ---------------------------
        bg_rect = QRectF(0, 0, self.width - 20, self.height - 20)
        painter.setBrush(self.bg_color)
        painter.drawRoundedRect(bg_rect, self.radius, self.radius)

        # ---------------------------
        # Title
        # ---------------------------
        painter.setPen(QColor(120, 120, 120))
        painter.setFont(QFont("Segoe UI", 14))
        painter.drawText(30, 45, "COMMUNITY SENTIMENT")

        # ---------------------------
        # Main label
        # ---------------------------
        label = self.compute_label(positive, negative, neutral)
        painter.setPen(QColor(20, 20, 20))
        painter.setFont(QFont("Segoe UI", 24, QFont.Bold))
        painter.drawText(30, 90, label)

        # ---------------------------
        # Sentiment bar
        # ---------------------------
        total = max(positive + neutral + negative, 1)

        bar_x = 30
        bar_y = 120
        bar_width = self.width - 80
        bar_height = 30

        neg_w = bar_width * (negative / total)
        neu_w = bar_width * (neutral / total)
        pos_w = bar_width * (positive / total)

        # Negative bar
        painter.setBrush(self.negative_color)
        painter.drawRoundedRect(QRectF(bar_x, bar_y, neg_w, bar_height), 10, 10)

        # Neutral bar (flat)
        painter.setBrush(self.neutral_color)
        painter.drawRect(QRectF(bar_x + neg_w, bar_y, neu_w, bar_height))

        # Positive bar
        painter.setBrush(self.positive_color)
        painter.drawRoundedRect(
            QRectF(bar_x + neg_w + neu_w, bar_y, pos_w, bar_height), 10, 10
        )

        # ---------------------------
        # Bottom text counts
        # ---------------------------
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
# 🔥 TEST BLOCK — generate summary from list of sentences
# ---------------------------------------------------------
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    # Needed for QPainter/QFont to work
    app = QApplication(sys.argv)

    ensure_vader()
    vader = SentimentIntensityAnalyzer()

    sentences = [
        "The sun dipped below the horizon leaving a warm glow.",
        "Technology is evolving faster than ever before.",
        "Cats often sleep for more than twelve hours a day.",
        "The sound of rain on the rooftop was calming.",
        "He opened the old book and dust filled the air.",
        "The startup launched a new innovative product.",
        "Music festivals attract thousands of enthusiastic fans.",
        "The mountain peaks were covered in a blanket of snow.",
        "Artificial intelligence is transforming industries.",
        "She brewed a cup of coffee to start her morning.",
        "The waves crashed gently along the shoreline.",
        "Traveling helps people discover new cultures.",
        "The city lights sparkled brilliantly at night.",
        "He found a rare coin buried in the garden.",
        "The chef prepared a delicious five-course meal.",
        "Birds chirped loudly as the sun rose.",
        "The library was silent except for turning pages.",
        "A gentle breeze rustled the leaves.",
        "Innovation drives economic growth worldwide.",
        "The dog wagged its tail excitedly.",
        "She wrote her thoughts in a leather journal.",
        "The conference attracted global business leaders.",
        "Fresh flowers brightened the entire room.",
        "He solved the puzzle after several attempts.",
        "The river flowed calmly through the valley.",
        "The team celebrated their unexpected victory.",
        "Healthy habits improve overall well-being.",
        "The old bridge creaked as cars passed.",
        "She painted a landscape filled with vibrant colors.",
        "Clouds gathered signaling an approaching storm.",
        "The market saw a sudden surge in demand.",
        "He planted a tree in his backyard.",
        "The classroom buzzed with lively discussions.",
        "Digital marketing strategies are constantly evolving.",
        "Snowflakes fell softly onto the frozen ground.",
        "She whispered a wish into the night sky.",
        "The robot performed tasks with precision.",
        "The bakery sold out of fresh bread quickly.",
        "He captured stunning photos of the sunset.",
        "The festival showcased traditional dance forms.",
        "A cup of tea can be incredibly comforting.",
        "The stock market experienced a minor correction.",
        "Children played joyfully in the park.",
        "The scientist conducted a groundbreaking experiment.",
        "The aroma of spices filled the kitchen.",
        "The garden bloomed with colorful flowers.",
        "He trained for months before running the marathon.",
        "Online learning platforms have become widely popular.",
        "The forest trail was peaceful and quiet.",
        "She discovered a hidden path behind the cabin.",
        "He enjoys reading books about ancient civilizations.",
        "The airport was crowded with holiday travelers.",
        "The innovation hub hosted various technology startups.",
        "The night sky was filled with shining stars.",
        "She cooked a meal using farm-fresh ingredients.",
        "The artist sketched portraits with remarkable detail.",
        "The rainfall cooled the hot summer day.",
        "He found inspiration in everyday moments.",
        "The technology conference introduced new software tools.",
        "Farmers worked tirelessly during the harvest season.",
        "The lighthouse guided ships through the dark.",
        "She decorated her room with minimalistic designs.",
        "The athlete broke a national record.",
        "Nature photography requires patience and precision.",
        "The museum showcased ancient artifacts.",
        "Digital transformation is reshaping workplaces.",
        "He enjoyed a peaceful walk by the lake.",
        "The classroom embraced collaborative learning.",
        "The startup secured funding for expansion.",
        "She bought handmade crafts from local artisans.",
        "The river reflected the clear blue sky.",
        "The company implemented new sustainability initiatives.",
        "He listened to calming instrumental music.",
        "The storm passed leaving behind a rainbow.",
        "She captured memories through her travel vlog.",
        "The organization hosted a charity marathon.",
        "He studied data trends to make predictions.",
        "The bookstore offered rare and vintage novels.",
        "The wind carried the scent of jasmine flowers.",
        "He developed a mobile app for fitness tracking.",
        "The team brainstormed creative solutions.",
        "She enjoyed hiking on challenging trails.",
        "The village celebrated a cultural festival.",
        "He analyzed customer behavior using analytics tools.",
        "The sound of the waterfall echoed through the valley.",
        "Her artwork was displayed in the exhibition.",
        "The new café became popular among students.",
        "He conducted a survey to gather feedback.",
        "The beach was filled with tourists during summer.",
        "She practiced yoga to relax her mind.",
        "The researchers published an interesting study.",
        "He explored the historic streets of the town.",
        "The company celebrated a decade of success.",
        "She adopted a puppy from the shelter.",
        "The algorithm improved accuracy significantly.",
        "He enjoyed a warm bowl of soup on a cold day.",
        "The team used data visualization for insights.",
        "She watched the sunrise with quiet admiration.",
        "The car sped down the empty highway.",
        "He learned new skills through online courses."
    ]

    positive = neutral = negative = 0

    for s in sentences:
        score = vader.polarity_scores(s)["compound"]
        if score >= 0.05:
            positive += 1
        elif score <= -0.05:
            negative += 1
        else:
            neutral += 1

    print(f"POS={positive}, NEU={neutral}, NEG={negative}")

    renderer = SentimentSummaryRenderer()
    img = renderer.render_summary(positive, neutral, negative)

    # Save output preview
    img.save("sentiment_preview.png")
    print("Saved: sentiment_preview.png")

    # Exit Qt cleanly
    sys.exit()
