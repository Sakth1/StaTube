from wordcloud import WordCloud, STOPWORDS
from PIL import Image
# ... (WordCloudAnalyzer class definition from previous turn remains here) ...

class WordCloudAnalyzer:
    """
    A class to generate a word cloud image from a list of strings.
    ... (docstring and methods as defined previously) ...
    """
    def __init__(self, width=800, height=400, background_color="white", max_words=200):
        """
        Initializes the WordCloudAnalyzer with specified parameters for the visualization.
        ...
        """
        self.width = width
        self.height = height
        self.background_color = background_color
        self.max_words = max_words
        self.stopwords = set(STOPWORDS)

    def generate_wordcloud(self, text_list: list[str]) -> Image.Image:
        """
        Generates the word cloud image from a list of strings.
        ...
        :returns: A PIL.Image.Image object of the generated word cloud.
        """
        if not isinstance(text_list, list):
            raise TypeError("Input must be a list of strings.")
        if not text_list:
            raise ValueError("Input list cannot be empty.")

        text_corpus = " ".join(text_list)
        
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
        image_object = wordcloud.to_image()

        return image_object

# --- Example Usage for Testing (Non-GUI Display) ---
if __name__ == '__main__':
    # Sample data
    data = [
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


    print("Starting word cloud generation...")
    try:
        # 1. Create an instance of the analyzer
        analyzer = WordCloudAnalyzer(width=800, height=300, max_words=50, background_color="white")

        # 2. Generate the word cloud image object
        wordcloud_img = analyzer.generate_wordcloud(data)
        
        print(f"Word cloud image generated successfully: {wordcloud_img}")
        print("-" * 40)
        
        # 3. Use the PIL .show() method to display the image for non-GUI testing
        # This will save a temporary file and open it with your system's default image viewer.
        print("Opening image in default system viewer for testing...")
        wordcloud_img.show() 

    except Exception as e:
        print(f"An error occurred during generation or display: {e}")