"""
A slightly modified version of scispaCy's AbbreviationDetector. The only minor
modification has been to handle common instances in legal text in which short form
abbreviations are bounded by quote marks, like so:

Section 1 of the Human Rights Act 1998 ("HRA") provides...

Save for this minor modification, the code has been untouched.

ScispaCy repo here -> https://github.com/allenai/scispacy
"""

from curses.ascii import isalnum
from typing import Tuple, List, Optional, Set, Dict
from collections import defaultdict
from spacy.language import Language
from spacy.tokens import Span, Doc
from spacy.matcher import Matcher


def find_abbreviation(
    long_form_candidate: Span, short_form_candidate: Span
) -> Tuple[Span, Optional[Span]]:
    """
    Implements the abbreviation detection algorithm in "A simple algorithm
    for identifying abbreviation definitions in biomedical text.", (Schwartz & Hearst, 2003).

    The algorithm works by enumerating the characters in the short form of the abbreviation,
    checking that they can be matched against characters in a candidate text for the long form
    in order, as well as requiring that the first letter of the abbreviated form matches the
    _beginning_ letter of a word.

    Parameters
    ----------
    long_form_candidate: Span, required.
        The spaCy span for the long form candidate of the definition.
    short_form_candidate: Span, required.
        The spaCy span for the abbreviation candidate.

    Returns
    -------
    A Tuple[Span, Optional[Span]], representing the short form abbreviation and the
    span corresponding to the long form expansion, or None if a match is not found.
    """
    long_form = " ".join([x.text for x in long_form_candidate])
    short_form = " ".join([x.text for x in short_form_candidate])

    long_index = len(long_form) - 1
    short_index = len(short_form) - 1
    contains_date = 0
    while short_index >= 0:
        current_char = short_form[short_index].lower()
        # We don't check non alpha-numeric characters.
        if not current_char.isalnum():
            short_index -= 1
            continue

            # Does the character match at this position? ...

        # ignoring dates that are part of the references to the legislation/legislation abbreviation 
        abrv_date = False
        if current_char.isnumeric():
            abrv_date = True
            contains_date += 1
           

        while (  
            (long_index >= 0 and long_form[long_index].lower() != current_char and abrv_date != True)
            or
            # .... or if we are checking the first character of the abbreviation, we enforce
            # to be the _starting_ character of a span.
            (
                short_index == 0
                and long_index > 0
                and long_form[long_index - 1].isalnum()
            )
        ):
             
            
            long_index -= 1
            
            if long_index < 0:

                return short_form_candidate, None

        long_index -= 1
        short_index -= 1

    # If we complete the string, we end up with -1 here,
    # but really we want all of the text.
    
    long_index = max(long_index, 0)


    # Now we know the character index of the start of the character span,
    # here we just translate that to the first token beginning after that
    # value, so we can return a spaCy span instead.
    word_lengths = contains_date
    starting_index = None
    

    for i, word in enumerate(long_form_candidate):
        word_lengths += len(word)
        if word_lengths > long_index:
            starting_index = i
        
            break

    return short_form_candidate, long_form_candidate[starting_index:]


def contains(str, set: Set[str]):
    """ Check whether sequence str contains ANY of the items in set. """
    return any([c in str for c in set])


def filter_matches(
    matcher_output: List[Tuple[int, int, int]], doc: Doc
) -> List[Tuple[Span, Span]]:
    # Filter into two cases:
    # 1. <Short Form> ( <Long Form> )
    # 2. <Long Form> (<Short Form>) [this case is most common].
    candidates = []
    for match in matcher_output:
        QUOTES = ['"', "'", "‘", "’", "“", "”"]

        start = match[1]
        end = match[2]
        quote_offset = 0
        
        # Adjust indexes where match is enclosed in quotation marks.
        if contains(doc[start:end].text, QUOTES):
            start = match[1] + 1
            end = match[2] - 1
            quote_offset = 1
        else: 
            continue
        # Ignore spans with more than 8 words in.
        if end - start > 8:
            continue
        if end - start > 3:
            # Long form is inside the parens.
            # Take two words before.
            short_form_candidate = doc[
                start - 3 - quote_offset : start - 1 - quote_offset
            ]
            if not contains(short_form_candidate.text, QUOTES): 
                continue
            if short_form_filter(short_form_candidate):
                candidates.append((doc[start:end], short_form_candidate))
        else:
            # Normal case.
            # Short form is inside the parens.
            # Sum character lengths of contents of parens.
            short_string = str(doc[start:end])
            quote_counter = 0
            # Ensures that the short form is wrapped in quotations
            for c in short_string: 
                if c in QUOTES: 
                    quote_counter += 1 
            if not quote_counter >= 2: 
                continue
            else:
                abbreviation_length = sum([len(x) for x in doc[start:end]])
                max_words = min(abbreviation_length + 5, abbreviation_length * 2)
                # # Look up to max_words backwards
                long_form_candidate = doc[
                    max(start - max_words - 1 - quote_offset, 0) : start - 1 - quote_offset
                ]

                candidates.append((long_form_candidate, doc[start:end]))
                continue
    return candidates


def short_form_filter(span: Span) -> bool:
    # All words are between length 2 and 10
    if not all([2 < len(x) < 10 for x in span]):
        return False
    # At least one word is alpha numeric
    if not any([x.is_alpha for x in span]):
        return False
    

    return True



class AbbreviationDetector():
    """
    Detects abbreviations using the algorithm in "A simple algorithm for identifying
    abbreviation definitions in biomedical text.", (Schwartz & Hearst, 2003).

    This class sets the `._.abbreviations` attribute on spaCy Doc.

    The abbreviations attribute is a `List[Span]` where each Span has the `Span._.long_form`
    attribute set to the long form definition of the abbreviation.

    Note that this class does not replace the spans, or merge them.
    """

    def __init__(self, nlp: Language) -> None:
        Doc.set_extension("abbreviations", default=[], force=True)
        Span.set_extension("long_form", default=None, force=True)

        self.matcher = Matcher(nlp.vocab)
        patterns = [[{"ORTH": "("}, {"OP": "+"}, {"ORTH": ")"}]]
        self.matcher.add(
            "parenthesis", patterns
        )
        self.global_matcher = Matcher(nlp.vocab)

        

    def find(self, span: Span, doc: Doc) -> Tuple[Span, Set[Span]]:
        """
        Functional version of calling the matcher for a single span.
        This method is helpful if you already have an abbreviation which
        you want to find a definition for.
        """
        dummy_matches = [(-1, int(span.start), int(span.end))]
        filtered = filter_matches(dummy_matches, doc)
        
        abbreviations = self.find_matches_for(filtered, doc)

        if not abbreviations:
            return span, set()
        else:
            return abbreviations[0]
   

    def __call__(self, doc: Doc) -> Doc:
        matches = self.matcher(doc)
        matches_no_brackets = [(x[0], x[1] + 1, x[2] - 1) for x in matches]
        filtered = filter_matches(matches_no_brackets, doc)

        occurences = self.find_matches_for(filtered, doc)
        
        for (long_form, short_forms) in occurences:
            for short in short_forms:
                short._.long_form = long_form
                doc._.abbreviations.append(short)
        
        return doc

    def find_matches_for(
        self, filtered: List[Tuple[Span, Span]], doc: Doc
    ) -> List[Tuple[Span, Set[Span]]]:
        rules = {}
        all_occurences: Dict[Span, Set[Span]] = defaultdict(set)
        already_seen_long: Set[str] = set()
        already_seen_short: Set[str] = set()
        for (long_candidate, short_candidate) in filtered:
            short, long = find_abbreviation(long_candidate, short_candidate)
       
            # We need the long and short form definitions to be unique, because we need
            # to store them so we can look them up later. This is a bit of a
            # pathalogical case also, as it would mean an abbreviation had been
            # defined twice in a document. There's not much we can do about this,
            # but at least the case which is discarded will be picked up below by
            # the global matcher. So it's likely that things will work out ok most of the time.
            new_long = long.text not in already_seen_long if long else False
            new_short = short.text not in already_seen_short
            if long is not None and new_long and new_short:
                already_seen_long.add(long.text)
                already_seen_short.add(short.text)
                all_occurences[long].add(short)
                rules[long.text] = long
                # Add a rule to a matcher to find exactly this substring.
                self.global_matcher.add(
                    long.text, [[{"ORTH": x.text} for x in short]]
                )
        to_remove = set()
        global_matches = self.global_matcher(doc)
        for match, start, end in global_matches:
            string_key = self.global_matcher.vocab.strings[match]
            to_remove.add(string_key)
            all_occurences[rules[string_key]].add(doc[start:end])
        for key in to_remove:
            # Clean up the global matcher.
            self.global_matcher.remove(key)

        return [(k, v) for k, v in all_occurences.items()]
