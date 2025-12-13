# Backend/AnalysisWorker.py
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
import time

from Analysis.SentimentAnalysis import run_sentiment_summary
from Analysis.WordCloud import WordCloudAnalyzer

class AnalysisWorker(QObject):
    """
    Threaded worker to run analysis (sentiment summary + wordcloud) on a list of sentences.
    Emits progress updates for the splash and returns QImage results.
    """

    progress_updated = Signal(str)
    progress_percentage = Signal(int)
    finished = Signal()
    sentiment_ready = Signal(QImage)
    wordcloud_ready = Signal(QImage)

    def __init__(self, sentences: list[str], sentiment_size: tuple = (1600, 520),
                 wordcloud_size: tuple = (2800, 1680), max_words: int = 200):
        super().__init__()
        self.sentences = sentences or []
        self.sent_w, self.sent_h = sentiment_size
        self.wc_w, self.wc_h = wordcloud_size
        self.max_words = max_words
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self) -> None:
        try:
            total_stages = 4
            stage = 0

            # Stage 1: loading/extract count
            stage += 1
            self.progress_updated.emit("Preparing sentences for analysis...")
            self.progress_percentage.emit(int((stage/total_stages)*100 * 0.02))  # small percent

            sentences = self.sentences
            n = len(sentences)
            if self._cancelled:
                self.progress_updated.emit("Analysis cancelled.")
                self.finished.emit()
                return

            # Stage 2: Sentiment (iterate sentences — dynamic progress)
            stage += 1
            self.progress_updated.emit("Running sentiment analysis...")
            # We'll update percent dynamically across this stage (weight: 45%)
            sentiment_stage_weight = 45
            base = int(((stage-1)/total_stages) * 100)
            if n == 0:
                self.progress_percentage.emit(base + 1)
            else:
                # process in micro-batches to allow progress updates
                batch = max(1, n // 20)
                processed = 0
                # build text list chunked — run_sentiment_summary expects sentences list
                # but it's not incremental; to show progress we compute compound in loop using VADER directly would be needed.
                # For simplicity and to avoid importing internals, call run_sentiment_summary once but fake granular progress.
                # Show incremental progress while computing
                for i in range(0, n, batch):
                    if self._cancelled:
                        self.progress_updated.emit("Analysis cancelled.")
                        self.finished.emit()
                        return
                    # small sleep to let UI update if heavy
                    time.sleep(0.01)
                    processed += min(batch, n - i)
                    frac = processed / n
                    pct = base + int(frac * sentiment_stage_weight)
                    self.progress_percentage.emit(min(pct, 99))

                # Now compute final sentiment image
                sentiment_img = run_sentiment_summary(sentences, width=self.sent_w, height=self.sent_h)
                self.sentiment_ready.emit(sentiment_img)

            # Stage 3: Wordcloud (weight: 45%)
            stage += 1
            self.progress_updated.emit("Generating word cloud...")
            wc_base = int(((stage-1)/total_stages) * 100)
            # Quick progress ticks while generating
            # generate_wordcloud is blocking; show small animation ticks before/after
            for tick in range(3):
                if self._cancelled:
                    self.progress_updated.emit("Analysis cancelled.")
                    self.finished.emit()
                    return
                time.sleep(0.05)
                self.progress_percentage.emit(wc_base + int((tick+1) * (40/3)))

            wc_img = WordCloudAnalyzer(max_words=self.max_words).generate_wordcloud(sentences, width=self.wc_w, height=self.wc_h)
            self.wordcloud_ready.emit(wc_img)
            self.progress_percentage.emit(95)

            # Stage 4: Finalizing
            stage += 1
            self.progress_updated.emit("Finalizing results...")
            time.sleep(0.05)
            self.progress_percentage.emit(100)
            self.progress_updated.emit("Analysis complete.")
            self.finished.emit()

        except Exception as e:
            # best-effort error reporting
            try:
                self.progress_updated.emit(f"Analysis error: {str(e)}")
            except Exception:
                pass
            self.finished.emit()
