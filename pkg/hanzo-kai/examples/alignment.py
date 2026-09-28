"""Decide which listings from two supplier catalogs are the same GPU, and which fields disagree.

Run with HANZO_API_KEY set, after `pip install hanzo-kai`.
"""

from hanzo_kai import Kai, Choice, Noul, Score, RetryPolicy

# Supplier A's listing, supplier B's, whether they are one product, and which of model, memory, form differ.
PAIRS = [
    ("NVIDIA H100 SXM5 80GB HBM3", "H100 80 GB, SXM form factor", True, (False, False, False)),
    ("NVIDIA A100 80GB PCIe", "A100 PCIe card, 80 GB HBM2e", True, (False, False, False)),
    ("NVIDIA L40S 48GB GDDR6", "L40S, 48 GB, PCIe, Ada Lovelace", True, (False, False, False)),
    ("AMD Instinct MI300X 192GB HBM3", "MI300X OAM module, 192 GB", True, (False, False, False)),
    ("NVIDIA RTX 6000 Ada Generation 48GB", "RTX 6000 Ada, 48 GB GDDR6 ECC", True, (False, False, False)),
    ("NVIDIA T4 16GB", "Tesla T4, 16 GB, low profile PCIe", True, (False, False, False)),
    ("NVIDIA H100 SXM5 80GB", "H100 PCIe, 80 GB", False, (False, False, True)),
    ("NVIDIA A100 80GB PCIe", "A100 PCIe card, 40 GB", False, (False, True, False)),
    ("NVIDIA RTX 6000 Ada Generation 48GB", "RTX A6000, 48 GB, Ampere", False, (True, False, False)),
    ("NVIDIA L40S 48GB", "L40, 48 GB", False, (True, False, False)),
    ("AMD Instinct MI300X 192GB", "MI250X OAM, 128 GB", False, (True, True, False)),
    ("NVIDIA H200 SXM 141GB", "H100 SXM, 80 GB", False, (True, True, False)),
]
FIELDS = {
    "model": ("name different GPU models", "the model names differ, not just their spelling"),
    "memory": ("give different memory sizes", "the memory sizes differ"),
    "form": ("give different form factors", "one is SXM or OAM and the other PCIe, or similar"),
}
QUESTIONS = {
    "relation": Choice(
        instructions="How does `hypothesis` relate to `premise`?",
        criteria={
            "entailment": "the premise implies the hypothesis",
            "neutral": "the premise neither implies nor contradicts the hypothesis",
            "contradiction": "the premise contradicts the hypothesis",
        },
    ),
    "same": Score(
        instructions="Do `premise` and `hypothesis` describe the same product?",
        criteria=["different products", "probably different", "probably the same", "the same product"],
    ),
    **{
        name: Noul(
            instructions=f"`premise` and `hypothesis` {what}.",
            criteria={"true": differ, "false": "they agree, or one of them does not say"},
        )
        for name, (what, differ) in FIELDS.items()
    },
}

right = {"relation": 0, "same": 0}
flags = {name: [] for name in FIELDS}
with Kai(retry=RetryPolicy(max_retries=20)) as kai:
    print(f"{'supplier A':36} {'supplier B':34} {'same':>5} {'relation':>13} {'score':>6}  differs: model memory form")
    for a, b, same, differ in PAIRS:
        state = {"premise": f"Supplier A lists the {a}.", "hypothesis": f"Supplier A lists the {b}."}
        d = kai.decide(state, QUESTIONS)
        relation, score = d.choices["relation"].choice, d.scores["same"].score
        right["relation"] += (relation == "entailment") == same
        right["same"] += (score >= 1.5) == same
        nouls = [d.nouls[name].noul for name in FIELDS]
        for name, p, truth in zip(FIELDS, nouls, differ):
            flags[name].append((p >= 0.5, truth))
        marks = "  ".join(f"{p:.2f}{'*' if t else ' '}" for p, t in zip(nouls, differ))
        print(f"{a:36} {b:34} {str(same):>5} {relation:>13} {score:>6.2f}           {marks}")

print(f"\n* marks a field that really differs.")
print(f"same product, right of {len(PAIRS)} pairs: by the relation (entailment is same) {right['relation']}, by the score (1.5 or more is same) {right['same']}")
for name, marks in flags.items():
    differ = sum(t for _, t in marks)
    print(f"{name:6} differs in {differ} of {len(marks)} pairs; its noul reached 0.5 on {sum(f and t for f, t in marks)} of those"
          f" and on {sum(f and not t for f, t in marks)} of the {len(marks) - differ} others")
