"""Stop words for Hindi, Hinglish and English (Lecture: Term vocabulary - stop words).

Stop words are very frequent words that carry little meaning for retrieval
(का, की, है, ka, hai, the ...). Question words (कौन, क्या, kaun, kya ...) are
included too, because the queries are questions and the answers rarely
contain these words.

I keep stop words out of ranked retrieval, but I still count their positions,
so phrase queries keep the right gaps between words.
The experiment in scripts/corpus_stats.py compares this list with a list
built from document frequency (the most common words in the corpus).
"""
from lipisetu.text.normalize import normalize

HINDI_STOP_WORDS = """
का की के है हैं में और से को पर यह ये वह वे था थी थे एक लिए किया गया गई गए
कि जो भी तो ही इस उस इन उन कर ने हो होता होती होते होना नहीं या अपने अपना अपनी
उनके उसके उसकी उनकी उसका उनका तक साथ बाद द्वारा जैसे कुछ कई किसी सभी अब जब तब
रहा रही रहे करने करते करता करती हुआ हुई हुए होने वाले वाली वाला दिया दी
कौन क्या कब कहाँ कहां कैसे कैसा कैसी किस क्यों कितना कितने कितनी किसने किसको किसका किसकी किसके कौनसा कौनसी कोनसा कोनसी
""".split()

HINGLISH_STOP_WORDS = """
ka ki ke hai hain h mein men me main aur or se ko par pe yah yeh ye vah woh wo ve tha thi the
ek liye kiya gaya gayi gaye ki jo bhi to toh hi is us in un kar ne ho hota hoti hote
nahi nahin ya apne apna apni tak sath saath baad dwara jaise kuch kai kisi sabhi ab jab tab
kaun kon kya kab kahan kaha kaise kaisa kaisi kis kyon kyu kyun kitna kitne kitni kisne kisko kiska kiski kiske
konsa konsi kaunsa kaunsi
hua hui hue raha rahi rahe karna karne karte karta karti hona hone wala wali wale vala vali vale
diya di liya gai gae
""".split()

ENGLISH_STOP_WORDS = """
a an the of in on at to for from by with and or is are was were be been being
what who whom which when where why how does do did has have had it its this that these those
as about into than then there their they he she his her i you we
""".split()


def build_stop_set():
    """Build one set with all stop words, normalised the same way as the text."""
    stop_set = set()
    for word in HINDI_STOP_WORDS + HINGLISH_STOP_WORDS + ENGLISH_STOP_WORDS:
        stop_set.add(normalize(word))
    return stop_set


STOP_WORDS = build_stop_set()


def is_stop_word(token):
    return token in STOP_WORDS
