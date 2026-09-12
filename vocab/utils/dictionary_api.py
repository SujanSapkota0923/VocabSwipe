import requests
import time
from typing import List, Optional, Dict


class DictionaryAPI:
    """
    Wrapper for Free Dictionary API (https://dictionaryapi.dev/)
    No API key required - completely free to use
    Includes retry logic for rate limiting
    """

    BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

    @staticmethod
    def fetch_word_details(word: str, max_retries: int = 3) -> Dict:
        """
        Fetch full details for a word (meanings, examples, audio) from the Free Dictionary API.
        """
        word = word.strip().lower()
        if not word:
            return {}

        for attempt in range(max_retries):
            try:
                response = requests.get(f"{DictionaryAPI.BASE_URL}{word}", timeout=10)
                if response.status_code == 404:
                    return {}
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** (attempt + 1))
                        continue
                    return {}

                response.raise_for_status()
                data = response.json()

                result = {"meanings": [], "example": None, "audio_url": None}

                if isinstance(data, list) and len(data) > 0:
                    # Extract audio (find first valid audio link)
                    for entry in data:
                        if "phonetics" in entry:
                            for phonetic in entry["phonetics"]:
                                if phonetic.get("audio"):
                                    result["audio_url"] = phonetic["audio"]
                                    if not result["audio_url"].startswith("http"):
                                        if result["audio_url"].startswith("//"):
                                            result["audio_url"] = (
                                                "https:" + result["audio_url"]
                                            )
                                    break
                        if result["audio_url"]:
                            break

                    # Extract meanings and examples
                    for entry in data:
                        if "meanings" in entry:
                            for meaning_obj in entry["meanings"]:
                                pos = meaning_obj.get("partOfSpeech", "")
                                if "definitions" in meaning_obj:
                                    for definition in meaning_obj["definitions"]:
                                        if "definition" in definition:
                                            def_text = definition["definition"]
                                            if pos:
                                                def_text = f"({pos}) {def_text}"
                                            result["meanings"].append(def_text)

                                        if not result["example"] and definition.get(
                                            "example"
                                        ):
                                            result["example"] = definition["example"]

                return result

            except Exception as e:
                print(f"Error fetching details for '{word}': {e}")
                return {}
        return {}

    @staticmethod
    def fetch_meanings(
        word: str, max_meanings: int = 3, max_retries: int = 3
    ) -> List[str]:
        """
        Backward compatible method for fetching meanings only.
        """
        details = DictionaryAPI.fetch_word_details(word, max_retries)
        return details.get("meanings", [])[:max_meanings]

    @staticmethod
    def fetch_meanings_batch(
        words: List[str], delay: float = 1.5
    ) -> Dict[str, List[str]]:
        """
        Fetch meanings for multiple words with rate limiting.

        Args:
            words: List of words to look up
            delay: Delay between requests in seconds (default: 1.5 to avoid rate limits)

        Returns:
            Dictionary mapping words to their meanings
        """
        results = {}
        total = len(words)

        for i, word in enumerate(words, 1):
            # Show progress for large batches
            if total > 10 and i % 50 == 0:
                print(f"Progress: {i}/{total} words processed...")

            meanings = DictionaryAPI.fetch_meanings(word)
            results[word] = meanings

            # Add delay between requests to avoid rate limiting
            # Skip delay for the last word
            if i < total and delay > 0:
                time.sleep(delay)

        return results
