import json
import re
import os
from typing import Optional, List

from PySide6.QtCore import Signal, QTimer, QThread
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QScrollArea, QSizePolicy
)

from Backend.ScrapeTranscription import TranscriptFetcher
from Backend.AnalysisWorker import AnalysisWorker
from UI.SplashScreen import SplashScreen
from utils.AppState import app_state
from utils.Logger import logger
from widgets.DownloadableImage import DownloadableImage


def transcript_to_sentences(transcript_list: List[dict]) -> List[str]:
    sentences = []
    for seg in transcript_list:
        text = seg.get("text")
        if isinstance(text, str) and text.strip():
            parts = re.split(r"[.!?]\s+|\n+", text.strip())
            sentences.extend([p.strip() for p in parts if p.strip()])
    return sentences


class Transcript(QWidget):
    transcript_page_scrape_transcripts_signal = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.db = app_state.db
        self.transcript_fetcher = TranscriptFetcher()
        self.transcript_page_scrape_transcripts_signal.connect(self.scrape_transcript)

        # images
        self.sentiment_image = None
        self.wordcloud_image = None

        # main layout: only a scroll area with content
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        # content widget that will hold full-size images stacked vertically
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        self.transcript_sentences: List[str] = []

        # Auto-run on load (post-init)
        QTimer.singleShot(0, self.scrape_transcript)

    def scrape_transcript(self):
        video_list = app_state.video_list
        if not video_list:
            logger.warning("TranscriptPage: No videos in app_state.video_list")
            # clear content
            for i in reversed(range(self.scroll_layout.count())):
                w = self.scroll_layout.itemAt(i).widget()
                if w:
                    w.deleteLater()
            self.scroll_layout.addWidget(QLabel("No transcript found."))
            return

        result = self.transcript_fetcher.fetch_transcripts(video_list)

        all_segments = []
        for channel_id, video_dict in result.items():
            if not isinstance(video_dict, dict):
                continue
            for video_id, meta in video_dict.items():
                filepath = None
                if isinstance(meta, dict):
                    filepath = meta.get("filepath")
                if not filepath or not os.path.exists(filepath):
                    continue
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        all_segments.extend(data)
                except Exception:
                    logger.exception("TranscriptPage: Error reading transcript file")

        self.transcript_sentences = transcript_to_sentences(all_segments)
        self._generate_and_display_images()

    def _generate_and_display_images(self):
        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        if not self.transcript_sentences:
            self.scroll_layout.addWidget(QLabel("No transcript found."))
            return

        # Sizes
        sent_w = 1600
        sent_h = int(sent_w * 0.33)
        wc_w = 2800
        wc_h = int(wc_w * 0.6)

        logger.info(f"TranscriptPage: Queuing analysis sentiment {sent_w}x{sent_h}, wordcloud {wc_w}x{wc_h}")

        self.analysis_thread = QThread()
        self.analysis_worker = AnalysisWorker(self.transcript_sentences, sentiment_size=(sent_w, sent_h), wordcloud_size=(wc_w, wc_h), max_words=120)
        self.analysis_worker.moveToThread(self.analysis_thread)

        parent_win = self.window() if hasattr(self, "window") else None
        self.splash = SplashScreen(parent=parent_win)
        self.splash.set_title("Analyzing transcripts...")
        self.splash.update_status("Preparing analysis...")
        self.splash.set_progress(0)
        self.splash.enable_runtime_mode(parent_window=parent_win, cancel_callback=self._cancel_analysis)
        self.splash.show_with_animation()

        self.analysis_thread.started.connect(self.analysis_worker.run)
        self.analysis_worker.progress_updated.connect(lambda m: (self.splash.update_status(m) if self.splash else None))
        self.analysis_worker.progress_percentage.connect(lambda p: (self.splash.set_progress(p) if self.splash else None))
        self.analysis_worker.sentiment_ready.connect(self._on_sentiment_ready)
        self.analysis_worker.wordcloud_ready.connect(self._on_wordcloud_ready)
        self.analysis_worker.finished.connect(self.analysis_thread.quit)
        self.analysis_worker.finished.connect(self.analysis_worker.deleteLater)
        self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)
        self.analysis_thread.finished.connect(lambda: (self.splash.fade_and_close(300) if self.splash else None))

        self.analysis_thread.start()

    def _cancel_analysis(self):
        if hasattr(self, "analysis_worker") and self.analysis_worker:
            try:
                self.analysis_worker.cancel()
            except Exception:
                pass
        if hasattr(self, "analysis_thread") and self.analysis_thread.isRunning():
            try:
                self.analysis_thread.requestInterruption()
                self.analysis_thread.quit()
                self.analysis_thread.wait(200)
            except Exception:
                pass

        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self.scroll_layout.addWidget(QLabel("Analysis cancelled."))

    def _on_sentiment_ready(self, qimage):
        self.sentiment_image = qimage
        channel_name = next(iter(app_state.video_list.keys()), "unknown")
        self.scroll_layout.addWidget(QLabel("<b>Sentiment Analysis</b>"))
        sent_widget = DownloadableImage(qimage, default_name=f"transcript_sentiment_{channel_name}.png")
        sent_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.scroll_layout.addWidget(sent_widget)

    def _on_wordcloud_ready(self, qimage):
        self.wordcloud_image = qimage
        self.scroll_layout.addWidget(QLabel("<b>Word Cloud</b>"))
        channel_name = next(iter(app_state.video_list.keys()), "unknown")
        wc_widget = DownloadableImage(qimage, default_name=f"transcript_wordcloud_{channel_name}.png")
        wc_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.scroll_layout.addWidget(wc_widget)
        self.scroll_layout.addStretch(1)
