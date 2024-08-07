"""
@author: amy.conroy
Adapted from Blackstone's abbreviation detector which itself was an
adaption of ScispaCy's abbreviation detector.
Updated for SpaCy version 3.0+, as well as to handle dates in both long and short form abbreviations,
and to be limited specifically to abbreviations where there are quotes in the
brackets. This prevents erroneous abbreviations being detected where brackets
are used separaetly from defining abbreviations.
Blackstone repo here -> https://github.com/ICLRandD/Blackstone
ScispaCy repo here -> https://github.com/allenai/scispacy
"""

from collections import defaultdict
from collections.abc import Iterable

from spacy.language import Language
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span


def find_abbreviation(long_form_candidate: Span, short_form_candidate: Span) -> tuple[Span, Span | None]:
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

        # ignoring dates that are part of the references to the legislation/legislation abbreviation
        abrv_date = False
        if current_char.isnumeric():
            abrv_date = True
            # adjust the index to reflect the fact that it contains a date
            contains_date += 1

        while (
            (long_index >= 0 and long_form[long_index].lower() != current_char and abrv_date is not True)
            or
            # .... or if we are checking the first character of the abbreviation, we enforce
            # to be the _starting_ character of a span.
            (short_index == 0 and long_index > 0 and long_form[long_index - 1].isalnum())
        ):
            long_index -= 1
            if long_index < 0:
                return short_form_candidate, None

        long_index -= 1
        short_index -= 1

    # If we complete the string, we end up with -1 here, but really we want all of the text.
    long_index = max(long_index, 0)

    # Converts the char index to the first token beginning after that value so a spaCy span can be returned.
    word_lengths = contains_date
    starting_index = None

    for i, word in enumerate(long_form_candidate):
        word_lengths += len(word)
        if word_lengths > long_index:
            starting_index = i
            break

    return short_form_candidate, long_form_candidate[starting_index:]


def contains(string: str, string_set: Iterable[str]) -> bool:
    """
    Check whether sequence str contains ANY of the items in set.
    Parameters
    ----------
    Str, required
    Set, required
    Returns
    -------
    A Boolean, True if str appears in set.
    """
    return any(c in string for c in string_set)


def filter_matches(matcher_output: list[tuple[int, int, int]], doc: Doc) -> list[tuple[Span, Span]]:
    """
    Filter into two cases:
    1. <Short Form> ( <Long Form> )
    2. <Long Form> (<Short Form>) [this case is most common].
    Parameters
    ----------
    matcher_output: List, required.
        List of the abbreviation match number, the start and the end position
        of the match found from the spaCy matcher.
    doc: Doc, required.
        Doc object of the judgment content.
    Returns
    -------
    List[Tuple[Span, Span]], Either short form and long form candidate
    or long form and short form candidate
    """
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
            short_form_candidate = doc[start - 3 - quote_offset : start - 1 - quote_offset]
            if short_form_filter(short_form_candidate):
                candidates.append((doc[start:end], short_form_candidate))
        else:
            # Normal case.
            # Short form is inside the parens.
            # Sum character lengths of contents of parens.
            abbreviation_length = sum([len(x) for x in doc[start:end]])
            max_words = min(abbreviation_length + 5, abbreviation_length * 2)
            # # Look up to max_words backwards
            long_form_candidate = doc[max(start - max_words - 1 - quote_offset, 0) : start - 1 - quote_offset]
            short_form = str(doc[start:end])
            word = short_form
            quote_offset_new = 0
            # Occassionally quotations at the start of the short form slips through - this is to clean that
            if (
                short_form.startswith('"')
                or short_form.startswith("“")
                or short_form.startswith("”")
                or short_form.startswith("“")
            ):
                word = short_form[1:]
                quote_offset_new = 1

            short_form_clean = word  # use the clean short form if we return the match
            first_char = short_form_clean[0]  # this is the first character of the word
            last_char = str(doc[end - 1])
            length = len(last_char)  # use the length to get the index of the last char

            # if the first character of the abbreviation is not upper case
            if first_char.isupper() is not True:
                continue
            # if the last character of the abbreviation is not upper case AND it is not a number (this is to allow years in the abbreviations)
            if last_char[length - 1].isupper() is not True and last_char[length - 1].isnumeric() is not True:
                continue

            # abbreviation must have 3 or more characters
            if len(str(doc[start:end])) >= 3:
                candidates.append((long_form_candidate, doc[start + quote_offset_new : end]))

            continue

    return candidates


def short_form_filter(span: Span) -> bool:
    """
    Abbreviation is checked to ensure it satisfies two constraints:
        1. Length is between 2 and 10
        2. Contains alpha numeric character
    Parameters
    ----------
    span: Span, required.
        Span of abbreviation
    Returns
    -------
    Boolean, True if abbreviation passes both constraints
    """
    # All words are between length 2 and 10
    if not all(2 < len(x) < 10 for x in span):
        return False
    # At least one word is alpha numeric
    if not any(x.is_alpha for x in span):
        return False

    return True


def verify_match_format(matcher_output: list[tuple[int, int, int]], doc: Doc) -> list[tuple[Span, Span]]:
    """
    Verify that the matches appear in a form where such as ("abbrv") or ("long_form") with quotes
    and brackets as the first two and final two characters
    Parameters
    ----------
    matcher_output: List, required.
        List of the abbreviation match number, the start and the end position
        of the match found from the spaCy matcher.
    doc: Doc, required.
        Doc object of the judgment content.
    Returns
    -------
    List[Tuple[Span, Span]], List of match start and end position
    """
    for match in matcher_output:
        QUOTES = ['"', "'", "‘", "’", "“", "”"]
        BRACKETS = ["(", ")"]
        start = match[1]
        end = match[2] - 1

        if end - start > 8:
            matcher_output.remove(match)

        # verify that the match is wrapped in quotes and brackets
        elif (
            not contains(str(doc[start + 1]), QUOTES)
            or not contains(str(doc[end - 1]), QUOTES)
            or not contains(str(doc[start]), BRACKETS)
            or not contains(str(doc[end]), BRACKETS)
        ):
            print(str(doc[start:end]))
            matcher_output.remove(match)
    return None  # type:ignore
    # This return value is depended on elsewhere in the code, but previously
    # it did not exist at all. Understanding how the abbreviation code is
    # meant to work is a task for the future.
    # TODO: https://trello.com/c/horD3P3F/693-enrichment-pipeline-abbreviations-not-functional


class AbbreviationDetector:
    """
    Detects abbreviations using the algorithm in "A simple algorithm for identifying
    abbreviation definitions in biomedical text.", (Schwartz & Hearst, 2003).
    This class sets the `._.abbreviations` attribute on spaCy Doc.
    The abbreviations attribute is a `List[Span]` where each Span has the `Span._.long_form`
    attribute set to the long form definition of the abbreviation.
    Note that this class does not replace the spans, or merge them.
    """

    def __init__(self, nlp: Language) -> None:
        """
        Initialises the patterns and vocabulary to be used by spaCy's matcher
        Parameters
        ----------
        nlp: construct a Doc object via spaCy's nlp object
        """
        Doc.set_extension("abbreviations", default=[], force=True)
        Span.set_extension("long_form", default=None, force=True)

        self.matcher = Matcher(nlp.vocab)
        patterns = [[{"ORTH": "("}, {"OP": "+"}, {"ORTH": ")"}]]
        self.matcher.add("parenthesis", patterns)
        self.global_matcher = Matcher(nlp.vocab)

    def find(self, span: Span, doc: Doc) -> tuple[Span, set[Span]]:
        """
        Functional version of calling the matcher for a single span.
        This method is helpful if you already have an abbreviation which
        you want to find a definition for.
        Parameters
        ----------
        span: Span, required
        doc: Doc, required
            Doc object of the judgment content.
        Returns
        -------
        Tuple[Span, Set[Span]], Abbreviation and long form
        """
        dummy_matches = [(-1, int(span.start), int(span.end))]
        filtered = filter_matches(dummy_matches, doc)

        abbreviations = self.find_matches_for(filtered, doc)

        if not abbreviations:
            return span, set()
        else:
            return abbreviations[0]

    def __call__(self, doc: Doc) -> Doc:
        """
        This function sets the `._.abbreviations` attribute on spaCy Doc. Abbreviations are identified,
        their format verified, constraints on matches tested and position in the document identified.
        Parameters
        ----------
        doc: Doc, required
            Doc object of the judgment content.
        Returns
        -------
        Doc, Doc object of the judgment content.
        """
        matches = self.matcher(doc)

        matches_brackets = [(x[0], x[1], x[2]) for x in matches]

        matcher_output = verify_match_format(matches_brackets, doc)
        # verify_match_format returns None, which is incorrect and means this section can not
        # have been run in it's current format.
        print(matcher_output)
        if matcher_output:
            matches_no_brackets = [
                (x[0], x[1] + 1, x[2] - 1)  # type:ignore
                for x in matcher_output
            ]
            filtered = filter_matches(matches_no_brackets, doc)
            occurrences = self.find_matches_for(filtered, doc)

            for long_form, short_forms in occurrences:
                for short in short_forms:
                    short._.long_form = long_form
                    doc._.abbreviations.append(short)

        return doc

    def find_matches_for(self, filtered: list[tuple[Span, Span]], doc: Doc) -> list[tuple[Span, set[Span]]]:
        """
        Function to return all start and end positions of an abbreviation found in the judgment content.
        Parameters
        ----------
        filtered: List[Tuple[Span, Span]], required
            Abbreviations found and passed through the filter_matches function
        doc: Doc, required
            Doc object of the judgment content.
        Returns
        -------
        List[Tuple[Span, Set[Span]]], for all short form and long form candidates found after filtering,
        list of the match and every occurance of the match in the judgment body
        """
        rules = {}
        all_occurences: dict[Span, set[Span]] = defaultdict(set)
        already_seen_long: set[str] = set()
        already_seen_short: set[str] = set()
        for long_candidate, short_candidate in filtered:
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
                self.global_matcher.add(long.text, [[{"ORTH": x.text} for x in short]])
        to_remove = set()
        global_matches = self.global_matcher(doc)
        for match, start, end in global_matches:
            string_key = self.global_matcher.vocab.strings[match]
            to_remove.add(string_key)
            all_occurences[rules[string_key]].add(doc[start:end])
        for key in to_remove:
            # Clean up the global matcher.
            self.global_matcher.remove(key)

        return list(all_occurences.items())
