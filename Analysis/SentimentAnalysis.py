import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from typing import List, Dict, Union, Tuple

# Ensure VADER lexicon is downloaded (run 'nltk.download('vader_lexicon')' once)

class SentimentAnalyzer:
    """
    A class to perform sentiment analysis on a list of text strings 
    using the NLTK VADER (Valence Aware Dictionary and sEntiment Reasoner) model.
    
    VADER is specifically attuned to sentiments expressed in social media.
    """

    def __init__(self):
        """
        Initializes the SentimentAnalyzer and loads the VADER model.
        """
        # Load the VADER sentiment intensity analyzer
        self.sid = SentimentIntensityAnalyzer()
        
    def get_sentence_sentiment(self, text: str) -> Dict[str, float]:
        """
        Calculates the sentiment scores for a single piece of text.

        :param text: The input string to analyze.
        :type text: str
        :returns: A dictionary containing 'neg', 'neu', 'pos', and 'compound' scores.
                  - 'compound' is a normalized, weighted composite score.
        :rtype: Dict[str, float]
        """
        # Polarity scores include negative, neutral, positive, and compound scores
        return self.sid.polarity_scores(text)

    def analyze_list(self, text_list: List[str]) -> Dict[str, Union[List[Dict], Tuple[str, float]]]:
        """
        Performs sentiment analysis on a list of strings and aggregates the results.

        :param text_list: A list of text strings (e.g., reviews, tweets, sentences).
        :type text_list: List[str]
        :raises TypeError: If the input is not a list of strings.
        :raises ValueError: If the input list is empty.
        :returns: A dictionary containing:
                  - 'individual_scores': A list of dictionaries, one for each input text.
                  - 'overall_compound': The average compound score across all texts.
                  - 'overall_sentiment': The derived overall sentiment ('Positive', 'Neutral', or 'Negative').
        :rtype: Dict[str, Union[List[Dict], Tuple[str, float]]]
        """
        if not isinstance(text_list, list) or not all(isinstance(t, str) for t in text_list):
            raise TypeError("Input must be a list of strings.")
        if not text_list:
            raise ValueError("Input list cannot be empty.")
            
        individual_scores = []
        compound_scores = []

        for text in text_list:
            # 1. Get the sentiment scores for the current text
            scores = self.get_sentence_sentiment(text)
            
            # 2. Store the detailed results
            individual_scores.append({
                'text': text,
                'scores': scores,
                'sentiment': self._determine_label(scores['compound'])
            })
            
            # 3. Collect compound score for overall aggregation
            compound_scores.append(scores['compound'])

        # 4. Calculate the average compound score
        if compound_scores:
            avg_compound = sum(compound_scores) / len(compound_scores)
        else:
            avg_compound = 0.0
            
        # 5. Determine the overall sentiment label
        overall_sentiment_label = self._determine_label(avg_compound)
        
        # 6. Return the structured results
        return {
            'individual_scores': individual_scores,
            'overall_compound': avg_compound,
            'overall_sentiment': overall_sentiment_label
        }

    def _determine_label(self, compound_score: float) -> str:
        """
        Helper method to classify a compound score into a simple sentiment label.
        
        Uses common VADER thresholds: >0.05 for positive, <-0.05 for negative.
        """
        if compound_score >= 0.05:
            return "Positive"
        elif compound_score <= -0.05:
            return "Negative"
        else:
            return "Neutral"

# --- Example Usage (Non-GUI Console Output) ---
if __name__ == '__main__':
    # Sample data with varied sentiments
    comments = [
        "I absolutely loved the experience and would do it again."  # positive
        "The product exceeded all my expectations."  # positive
        "She was thrilled with the results of her hard work."  # positive
        "The weather was perfect for a nice long walk."  # positive
        "He felt proud after completing the difficult task."  # positive
        "The team celebrated their victory with excitement."  # positive
        "I enjoyed every moment of the event."  # positive
        "The delicious meal made my day even better."  # positive
        "The new update works flawlessly and is very intuitive."  # positive
        "His performance was outstanding and inspiring."  # positive

        "I am disappointed with the quality of the service."  # negative
        "The experience was terrible and not worth the money."  # negative
        "She regretted buying the product after using it once."  # negative
        "He was frustrated with the slow customer support."  # negative
        "The movie was boring and a complete waste of time."  # negative
        "The food tasted awful and was poorly prepared."  # negative
        "The sudden cancellation ruined my entire plan."  # negative
        "They were upset due to the shipment delay."  # negative
        "The new software update caused more problems than before."  # negative
        "The room was dirty and smelled very bad."  # negative

        "The meeting was held as scheduled."  # neutral
        "He walked to the store to buy groceries."  # neutral
        "The device needs to be charged before use."  # neutral
        "She placed the book on the wooden shelf."  # neutral
        "The data was recorded and stored in the database."  # neutral
        "He typed the report and sent it to his manager."  # neutral
        "The bus arrived at the station on time."  # neutral
        "She turned off the lights before leaving."  # neutral
        "The file was moved to a different folder."  # neutral
        "He switched on the computer and logged in."  # neutral

        "I’m really happy that my efforts finally paid off."  # positive
        "The host made us feel extremely welcome."  # positive
        "The design is clean, simple, and beautiful."  # positive
        "He received great feedback from his clients."  # positive
        "The journey was peaceful and refreshing."  # positive

        "I can’t believe how bad the service was today."  # negative
        "The experience left me feeling very disappointed."  # negative
        "The product broke after only one day of use."  # negative
        "He felt completely ignored by the staff."  # negative
        "This is the worst decision I have ever made."  # negative

        "She checked the time and continued her work."  # neutral
        "The report was updated earlier this morning."  # neutral
        "He opened the door and walked inside."  # neutral
        "The instructions were printed on the back of the box."  # neutral
        "The website loaded after a few seconds."  # neutral

        "The support team was incredibly helpful."  # positive
        "I’m delighted with how smooth everything went."  # positive
        "She smiled after hearing the good news."  # positive

        "The solution failed completely during testing."  # negative
        "He felt anxious throughout the meeting."  # negative
        "The constant errors made the system unusable."  # negative

        "He wrote down the notes during the lecture."  # neutral
        "She saved the document before closing the app."  # neutral
        "The box was placed neatly on the table."  # neutral
    ]


    print("--- Sentiment Analysis Starting ---")
    try:
        # Create an instance of the analyzer
        analyzer = SentimentAnalyzer()

        # Perform the analysis
        analysis_result = analyzer.analyze_list(comments)
        
        print("\n## 📊 Analysis Summary")
        print(f"Overall Compound Score: {analysis_result['overall_compound']:.4f}")
        print(f"Overall Sentiment: **{analysis_result['overall_sentiment']}**")
        print("-" * 30)

    except Exception as e:
        print(f"An error occurred: {e}")