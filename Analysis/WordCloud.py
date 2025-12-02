import io
from wordcloud import WordCloud, STOPWORDS
from PySide6.QtGui import QImage

from utils.logger import logger

class WordCloudAnalyzer:
    """
    A class to generate a word cloud image from a list of strings.
    This module returns a QImage compatible with PySide6/Qt.
    """
    def __init__(self, width=800, height=400, background_color="white", max_words=200):
        """
        Initializes the WordCloudAnalyzer with specified parameters.
        
        :param width: Width of the canvas.
        :param height: Height of the canvas.
        :param background_color: Hex color or name (e.g., "white", "#000000").
        :param max_words: Maximum number of words to include in the cloud.
        """
        self.width = width
        self.height = height
        self.background_color = background_color
        self.max_words = max_words
        self.stopwords = set(STOPWORDS)

    def generate_wordcloud(self, text_list: list[str]) -> QImage:
        """
        Generates the word cloud and converts it to a PySide6 QImage.

        :param text_list: A list of strings to process.
        :returns: A PySide6.QtGui.QImage object.
        """
        if not isinstance(text_list, list):
            logger.error("WordCloudAnalyzer: text_list must be a list of strings")
            raise TypeError("Input must be a list of strings.")

        if not text_list:
            logger.error("WordCloudAnalyzer: Input text list is empty")
            raise ValueError("Input list cannot be empty.")
        
        logger.debug(f"WordCloudAnalyzer: generating wordcloud with {len(text_list)} items")

        # 1. Join list into a single corpus
        text_corpus = " ".join(text_list)
        
        try:
            # 2. Generate WordCloud using the library (Creates a PIL object internally)
            wordcloud = WordCloud(
                width=self.width,
                height=self.height,
                background_color=self.background_color,
                max_words=self.max_words,
                stopwords=self.stopwords,
                scale=2, 
                collocations=False
            )
            wordcloud.generate(text_corpus)
            
            # 3. Get the PIL Image
            pil_image = wordcloud.to_image()

            # 4. Convert PIL Image to PySide6 QImage
            # We use a memory buffer (BytesIO) to transfer data safely.
            # This handles format (RGB/RGBA) conversions automatically.
            img_buffer = io.BytesIO()
            pil_image.save(img_buffer, format="PNG")
            qimage = QImage()
            # Load from the internal byte data of the buffer
            qimage.loadFromData(img_buffer.getvalue())

            return qimage
        
        except Exception as e:
            logger.error(f"WordCloudAnalyzer: Error generating wordcloud: {e}")
            raise
