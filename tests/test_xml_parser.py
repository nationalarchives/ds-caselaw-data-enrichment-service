import unittest
import sys
sys.path.append("./")
from utils.helper import parse_file
from spacy.lang.en import English


"""
    Testing the xml parser to ensure that information is extracted as expected. 
"""

def set_up():
    nlp = English()
    nlp.max_length = 1500000
    nlp.add_pipe("entity_ruler").from_disk("rules/citation_patterns.jsonl")
    # TODO: change this to a mock db?
    return nlp


class TestXmlParser(unittest.TestCase): 
    def SetUp(self): 
        self.nlp = set_up()

    def testXMLStrings(self): 
        text = "<paragraph> \
            <num style=\"font-style:normal;font-weight:normal;text-decoration:none;vertical-align:baseline;font-family:'Times New Roman';font-size:12pt;color:#000000;background-color:auto;margin-left:0.50in;text-indent:-0.50in\">36.</num>\
            <content> \
                <p style=\"margin-left:0.50in;margin-right:0.00in\">This passage was approved by the House of Lords in <span style=\"font-style:italic\">Three Rivers District Council v Bank of England (No.6)</span> [2004] UKHL 48, [2005] 1 AC 610 at [38] (Lord Scott), [58] to [60] (Lord Rodger) [62] (Lady Hale) and [111] (Lord Carswell) and has been applied in many cases since (e.g. <span style=\"font-style:italic\">Director of the Serious Fraud Office v Eurasian Natural Resources Corpn Ltd</span> [2018] EWCA Civ 2006, [2019] 1 WLR 791 at [65]).  </p>\
            </content>\
            </paragraph>"

        judgment_content_text = parse_file(text)
        assert judgment_content_text == "This passage was approved by the House of Lords in Three Rivers District Council v Bank of England (No.6) [2004] UKHL 48, [2005] 1 AC 610 at [38] (Lord Scott), [58] to [60] (Lord Rodger) [62] (Lady Hale) and [111] (Lord Carswell) and has been applied in many cases since (e.g. Director of the Serious Fraud Office v Eurasian Natural Resources Corpn Ltd [2018] EWCA Civ 2006, [2019] 1 WLR 791 at [65])."
    
        text = "<content>\
                <p style=\"margin-left:0.80in;margin-right:0.03in;text-indent:0.00in\">in accordance with CPR Rule 22.1 and PD 22.\” </p>\
            </content>"

        judgment_content_text = parse_file(text)
        assert judgment_content_text == "in accordance with CPR Rule 22.1 and PD 22.\”"


        text = "<content>\
                <p class=\"Heading2\" style=\"margin-left:-0.00in;text-indent:-0.01in\">CONCLUSION</p>\
            </content>"

        judgment_content_text = parse_file(text)
        assert judgment_content_text == "CONCLUSION"

        text = "<paragraph>\
                <num style=\"font-style:normal;font-weight:normal;text-decoration:none;vertical-align:baseline;font-family:'Times New Roman';font-size:12pt;color:#000000;background-color:auto;margin-left:0.50in\">114.</num>\
                <content>\
                    <p style=\"margin-left:0.50in;margin-right:0.00in;text-indent:0.5in\">The present case is different.  The Sellers had a single obligation to provide and maintain the capacity to deliver gas from the Reservoirs at 130% of the TRDQ, whatever that was at the time.  They had no discretion as to how much daily gas they had to deliver.  As already noted, and the distinction is a subtle one, the power to change an obligation is not a discretion as to how to perform it.  Accordingly, once the obligation is identified and the breach established, the only remaining question is what if any loss has flowed from the breach.  There is no uncertainty about definition of the loss, though its quantification may be complex, depending on the circumstances.   </p>\
                </content>\
                </paragraph>\
                <paragraph>\
                <num style=\"font-style:normal;font-weight:normal;text-decoration:none;vertical-align:baseline;font-family:'Times New Roman';font-size:12pt;color:#000000;background-color:auto;margin-left:0.50in\">115.</num>\
                <content>\
                    <p style=\"margin-left:0.50in;margin-right:0.00in;text-indent:0.5in\">I would therefore also allow the cross-appeal.  I am conscious that we are differing from the judge not once but twice, but that is no reflection on his judgment, which dealt clearly and succinctly with three difficult issues.  It should also be noted that his undisturbed finding on the third issue (no implied term) has had a decisive effect on the outcome and that his decision and ours have by different routes arrived at the same destination.  </p>\
                </content>"
        
        judgment_content_text = parse_file(text)
        assert judgment_content_text == "The present case is different.  The Sellers had a single obligation to provide and maintain the capacity to deliver gas from the Reservoirs at 130% of the TRDQ, whatever that was at the time.  They had no discretion as to how much daily gas they had to deliver.  As already noted, and the distinction is a subtle one, the power to change an obligation is not a discretion as to how to perform it.  Accordingly, once the obligation is identified and the breach established, the only remaining question is what if any loss has flowed from the breach.  There is no uncertainty about definition of the loss, though its quantification may be complex, depending on the circumstances. I would therefore also allow the cross-appeal.  I am conscious that we are differing from the judge not once but twice, but that is no reflection on his judgment, which dealt clearly and succinctly with three difficult issues.  It should also be noted that his undisturbed finding on the third issue (no implied term) has had a decisive effect on the outcome and that his decision and ours have by different routes arrived at the same destination."

if __name__ == '__main__':
    unittest.main()