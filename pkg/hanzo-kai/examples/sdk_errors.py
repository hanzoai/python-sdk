from hanzo_kai import AuthenticationError, BadRequestError, Kai, Noul

QUESTIONS = {
    "refund": Noul(
        instructions="The customer asks for money back.",
        criteria={"true": "the ticket asks for a refund", "false": "the ticket asks for something else"},
    )
}

with Kai() as kai:
    try:
        kai.decide("Please refund the duplicate charge.", QUESTIONS, model="no-such-model")
    except BadRequestError as error:
        print(type(error).__name__, error.status, error.code, error.message)
        print(error.request_id is not None, error.body)

with Kai(api_key="sk-no-such-key") as kai:
    try:
        kai.decide("Please refund the duplicate charge.", QUESTIONS)
    except AuthenticationError as error:
        print(type(error).__name__, error.status, error.message)
