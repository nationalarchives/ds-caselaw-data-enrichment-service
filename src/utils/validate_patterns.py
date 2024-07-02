import json

import pandas as pd
import spacy


def test_manifest(df: pd.DataFrame) -> None:
    """
    Test for the rules manifest: given a dataframe of the CSV file, and the patterns
    (which are also derived directly from that CSV file), check that the number of
    reponses are equal to the number of items searched for.
    (This doesn't sound very reliable)
    """
    nlp = spacy.load(
        "en_core_web_sm", exclude=["tok2vec", "attribute_ruler", "lemmatizer", "ner"]
    )
    nlp.max_length = 2500000
    patterns = [json.loads(s) for s in df["pattern"]]

    citation_ruler = nlp.add_pipe("entity_ruler")
    citation_ruler.add_patterns(patterns)

    examples = df["match_example"].tolist()

    MATCHED_IDS = []

    for example in examples:
        doc = nlp(example)
        ent = [str(ent.ent_id_) for ent in doc.ents][0]
        MATCHED_IDS.append(ent)

    MATCHED_IDS = list(set(MATCHED_IDS))
    print(len(MATCHED_IDS), df.shape[0])
    assert len(MATCHED_IDS) == df.shape[0]
