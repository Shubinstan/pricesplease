import re

class TitleNormalizer:
    """
    Engine for normalizing game titles.
    Cleans strings from garbage, trademarks, and edition names.
    """
    
    # Filler words that stores like to add to titles
    STOP_WORDS = [
        "edition", "premium", "deluxe", "standard", "ultimate",
        "goty", "game of the year", "director's cut",
        "ps4", "ps5", "xbox one", "xbox series x", "pc",
        "friend's pass"
    ]

    @classmethod
    def normalize(cls, raw_title: str) -> str:
        # 1. Convert to lowercase
        title = raw_title.lower()
        
        # 2. Remove trademarks and copyrights (™, ®, ©)
        title = re.sub(r'[\u2122\u00ae\u00a9]', '', title)
        
        # 3. Remove filler words
        for word in cls.STOP_WORDS:
            # Use regex with word boundaries (\b) to avoid removing parts of normal words
            title = re.sub(rf'\b{word}\b', '', title)
            
        # 4. Remove everything except letters, numbers, and spaces (replace punctuation with spaces)
        title = re.sub(r'[^a-z0-9\s]', ' ', title)
        
        # 5. Remove extra spaces that might remain after removing words
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title

# Block for manual testing (will run if this file is executed directly)
if __name__ == "__main__":
    test_titles = [
        "It Takes Two™",
        "It Takes Two - PS4 & PS5",
        "A Way Out: Friend's Pass",
        "The Witcher® 3: Wild Hunt - Game of the Year Edition"
    ]
    
    print("--- Normalizer Testing ---")
    for raw in test_titles:
        clean = TitleNormalizer.normalize(raw)
        print(f"Original: '{raw}'\nCleaned:  '{clean}'\n")