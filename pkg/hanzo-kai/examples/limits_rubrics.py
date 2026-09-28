"""Score rubrics no suite measured: four hotels, four aspects, each an expected level from 0 to 3."""

from hanzo_kai import Kai, RetryPolicy, Score

RUBRICS = {
    "quiet": Score(instructions="How quiet are the rooms at night, going by the reviews?",
                   criteria=["noisy most nights", "noisy on some nights", "quiet with rare noise", "silent"]),
    "transit": Score(instructions="How close is public transport, going by the reviews?",
                     criteria=["far or not mentioned", "a long walk", "a short walk", "at the door"]),
    "family": Score(instructions="How well does the hotel suit children, going by the reviews?",
                    criteria=["unsuitable for children", "tolerates children", "welcomes children", "built for families"]),
    "clean": Score(instructions="How clean are the rooms, going by the reviews?",
                   criteria=["dirty", "some problems", "clean", "spotless"]),
}
HOTELS = {
    "Harbor Point": ["Two minutes from the central station, which made my early train easy.",
                     "Street noise until 2 a.m. on Friday and Saturday; the earplugs on the pillow are there for a reason.",
                     "Spotless room, and the desk was big enough to work at."],
    "Linden Court": ["Our kids spent every afternoon in the pool, and the staff set up a cot without being asked.",
                     "It is a 25-minute walk to the nearest tram stop, so we took taxis everywhere.",
                     "Very quiet at night. We heard nothing through the walls."],
    "The Meridian": ["The metro entrance is across the street.",
                     "Silent rooms and heavy curtains; I slept better than at home.",
                     "No cots and no children's menu. This is a hotel for adults."],
    "Canal House": ["The family room had bunk beds and the children loved watching the canal boats.",
                    "The bar downstairs is loud on weekends but fine during the week.",
                    "Mould in the shower grout and a stained carpet.",
                    "The tram stop is a five-minute walk."],
}

with Kai(retry=RetryPolicy(max_retries=8)) as kai:
    print(f"{'':<13}" + "".join(f"{name:>9}" for name in RUBRICS))
    for hotel, reviews in HOTELS.items():
        d = kai.decide(state={"hotel": hotel, "reviews": reviews}, questions=RUBRICS)
        print(f"{hotel:<13}" + "".join(f"{d.scores[name].score:>9.2f}" for name in RUBRICS))
