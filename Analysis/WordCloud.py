import io
import sys
from wordcloud import WordCloud, STOPWORDS
from PIL import Image
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QLabel

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
            raise TypeError("Input must be a list of strings.")
        if not text_list:
            raise ValueError("Input list cannot be empty.")

        # 1. Join list into a single corpus
        text_corpus = " ".join(text_list)
        
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

# --- Example Usage for Testing (GUI Display) ---
if __name__ == '__main__':
    # Sample data
    data = [
        "Python is amazing for data visualization",
        "PySide6 allows building powerful GUIs",
        "WordCloud generates beautiful text representations",
        "Coding is fun and creative",
        "Artificial Intelligence is changing the world",
        "OpenAI tools help developers write better code",
        "Qt framework is robust and cross-platform",
        "Innovation drives technology forward",
        "Learning never stops in software engineering"
    ]

    print("Starting word cloud generation...")
    
    # We must create a QApplication to display anything in PySide6
    app = QApplication(sys.argv)

    try:
        # 1. Create instance
        analyzer = WordCloudAnalyzer(width=600, height=400, max_words=50, background_color="black")

        # 2. Generate QImage
        qt_image = analyzer.generate_wordcloud(data)
        print(f"Success! Generated object type: {type(qt_image)}")

        # 3. Display it
        # QImage holds the data, QPixmap is optimized for on-screen display.
        # We convert it here for the label.
        display_pixmap = QPixmap.fromImage(qt_image)
        
        label = QLabel()
        label.setWindowTitle("WordCloud Preview")
        label.setPixmap(display_pixmap)
        label.resize(display_pixmap.width(), display_pixmap.height())
        label.show()

        print("Displaying GUI window. Close the window to exit script.")
        
        # Start the GUI event loop
        sys.exit(app.exec())

    except Exception as e:
        print(f"An error occurred: {e}")