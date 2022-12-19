from faker.providers.person.en_US import Provider as PersonProvider
from typing import Any, Dict, Union
import re
import random
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging
# from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel
# from transformers import AutoModel, GPT2Tokenizer
logger = logging.getLogger(__name__)


class generateData(PersonProvider):
    __provider__ = "defendtxkids"
    __use_weighting__ = True

    # The text2text model will transform these prompts into a response
    complaintList = [
        "There's a drag show in town and it has to be stopped. If we don't stop it, society might collapse. Write a paragraph explaining why.",
        "There's an event coming up that's going make everyone become transgender if we don't take action. Write a paragraph about what will happen if everyone becomes trans.",
        # "Write a paragraph planning an event to end transphobia in Texas.",
        # "Write a paragraph that will make transphobic people feel bad.",
        "I saw a group of suspicious looking transgender people the other day. They looked like they were plotting something evil. Write a letter to the newspaper explaining why trans people need to be stopped.",
        "There's a party this weekend that's going make everyone become transgender if we don't take action. Write a paragraph explaining why.",
        "Explain why drag shows will lead to the destruction of traditional gender roles.",
        "Write a letter from the point of view of a scared transphobic person.",
    ]

    domains = [
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "aol.com",
        "yahoo.fr",
        "live.com",
        "outlook.com",
        "proton.me",
    ]

    # city_texas = [
    #     "Houston",
    #     "San Antonio",
    #     "Dallas",
    #     "Austin",
    #     "Fort Worth",
    #     "El Paso",
    #     "Arlington",
    #     "Corpus Christi",
    #     "Plano",
    #     "Lubbock",
    # ]

    formats_address = (
        "{{street_address}}",
        "{{street_address}}, {{city}}",
        "{{street_address}}, {{city}} {{state_abbr}}",
        "{{street_name}}, {{state_abbr}} {{postcode}}",
        "{{street_address}}, {{city}} {{state}}",
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Make 1/4 of everyone nonbinary
        self.formats_nonbinary.update((x, y / 4) for x, y in self.formats_nonbinary.items())
        self.formats.update(self.formats_nonbinary)

        # tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-base")
        # model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Running pytorch on {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-large").to(self.device)

    def complaint(self) -> Dict[str, Union[str, Any]]:
        """
        :example 'John Doe'
        """
        pattern: str = self.random_element(self.formats)
        _name = self.generator.parse(pattern)
        _name = re.sub(r'[^\w\s]', '', _name)

        _username = _name.lower().split()
        if random.random() > .5:
            _username[0] = self.bothify(_username[0] + "??")
        else:
            _username[0] = self.bothify(_username[0] + "##")
        _username = random.sample(_username, 2)
        _email = ".".join(_username) + "@" + self.random_element(self.domains)
        _address = self.generator.parse(self.random_element(self.formats_address))

        # Use the langauge model to generate the address so they are harder to filter out
        if random.random() < .3:
            _address = self._ml("question: what's the address of the coolest queer club in town?", 16)

        # Randomly add a club name
        if random.random() < .3:
            club_name = self._ml("question: what's the name of the coolest queer club in town?", 12)
            _address = club_name.title() + " at " + _address

        _complaint = self._ml(random.choice(self.complaintList), 50)
        # _complaint = fake.paragraph(nb_sentences=5)

        # remove special characters from the address
        _address = re.sub(r'[^\w\s]', '', _address)
        return {
            "name": _name,
            "email": _email,
            "address": _address,
            "complaint": _complaint,
        }

    def _ml(self, string=None, max_length=20):
        outputs = self.model.generate(
            self.tokenizer.encode(string, return_tensors="pt").to(self.device),
            max_length=max_length,
            do_sample=True,
            repetition_penalty=1.2,
            temperature=1.7,
            top_p=0.95,
            top_k=50,
            num_beams=2,
            early_stopping=True,
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

