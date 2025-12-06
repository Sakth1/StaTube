import io
from wordcloud import WordCloud, STOPWORDS
from PySide6.QtGui import QImage

from utils.Logger import logger


class WordCloudAnalyzer:
    """
    Returns QImage word cloud. Defaults chosen for high-res natural-size display.
    """

    def __init__(self, width=2800, height=1680, background_color="white", max_words=200):
        self.width = int(width)
        self.height = int(height)
        self.background_color = background_color
        self.max_words = max_words
        self.stopwords = set(STOPWORDS)

    def generate_wordcloud(self, text_list: list[str], width: int | None = None, height: int | None = None) -> QImage:
        if not isinstance(text_list, list):
            logger.error("WordCloudAnalyzer: text_list must be a list of strings")
            raise TypeError("Input must be a list of strings.")

        if not text_list:
            logger.error("WordCloudAnalyzer: Input text list is empty")
            raise ValueError("Input list cannot be empty.")

        use_w = int(width) if width is not None else self.width
        use_h = int(height) if height is not None else self.height

        logger.debug(f"WordCloudAnalyzer: generating wordcloud with {len(text_list)} items at {use_w}x{use_h}")

        try:
            text_corpus = " ".join(text_list)

            wordcloud = WordCloud(
                width=use_w,
                height=use_h,
                background_color=self.background_color,
                max_words=self.max_words,
                stopwords=self.stopwords,
                scale=1,
                collocations=False
            )
            wordcloud.generate(text_corpus)

            pil_image = wordcloud.to_image()
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format="PNG")
            qimage = QImage()
            qimage.loadFromData(img_buffer.getvalue())
            return qimage

        except Exception as e:
            logger.error(f"WordCloudAnalyzer: Error generating wordcloud: {e}")
            raise
