from hanzo_kai import Kai, Score

reviews = [
    ("very negative", "Arrived broken, support never answered, and the refund took six weeks. Avoid."),
    ("negative", "Not worth the price. It works, but the motor already sounds tired."),
    ("neutral", "It is fine. Nothing special, nothing wrong."),
    ("mixed", "The blender is loud and the lid cracked after a month, but it still makes a decent smoothie."),
    ("positive", "Does exactly what it says. Quiet, fast, easy to clean. I would buy it again."),
    ("very positive", "Best purchase this year. My kids love it and I use it every single morning!"),
]
questions = {
    "names": Score(
        instructions="How positive is `review`?",
        criteria=["very negative", "negative", "neutral", "positive", "very positive"],
    ),
    "sentences": Score(
        instructions="How does the writer of `review` feel about the product?",
        criteria=[
            "Very negative: angry, would warn others away.",
            "Negative: disappointed, more bad than good.",
            "Mixed or neutral: good and bad balance out, or no opinion.",
            "Positive: satisfied, more good than bad.",
            "Very positive: delighted, would recommend.",
        ],
    ),
}

with Kai() as kai:
    print("a person says   level names   sentences")
    for label, text in reviews:
        d = kai.decide(state={"review": text}, questions=questions)
        names, sentences = d.scores["names"], d.scores["sentences"]
        print(f"{label:15} {names.score:11.2f}   {sentences.score:9.2f}")
