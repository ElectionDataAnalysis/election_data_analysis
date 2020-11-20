import election_data_analysis as e

# Instructions:
#   Change the constants to values from your file
#   Delete any tests for contest types your state doesn't have in 2020 (e.g., Florida has no US Senate contest)
#   (Optional) Change district numbers
#   Replace each '-1' with the correct number calculated from the results file.
#   Move this testing file to the correct jurisdiction folder in `election_data_analysis/tests`

# # # constants - CHANGE THESE!! - use internal db names
election = "2020 General"
jurisdiction = 'South Carolina'
abbr = 'SC'
total_pres_votes = 6791 + 1362142 + 1818 + 28305 + 1068220  # total of all votes for President
cd = 3  # congressional district
total_cd_votes = 236796 + 95427 + 306  # total votes in the chosen cd
shd = 1   # state house district
total_shd_votes = 17282 + 227
ssd = 5  # state senate district
total_ssd_votes = 44757 + 14007 + 39
single_vote_type = 'absentee-mail'  # pick any one from your file
pres_votes_vote_type = 984 + 154331 + 343 + 3703 + 244009
single_county = 'South Carolina;Abbeville County'  # pick any one from your file
pres_votes_county = 10 + 9 + 4 + 4306 + 3320 + 581 + 2 + 4 + 52 + 30 + 6 + 1205 + 2129 + 753 # total votes for pres of that county


def test_data_exists(dbname):
    assert e.data_exists(election, jurisdiction, dbname=dbname)


def test_presidential(dbname):
    assert(e.contest_total(
        election,
        jurisdiction,
        f"US President ({abbr})",
        dbname=dbname,
        )
        == total_pres_votes
    )


def test_congressional_totals(dbname):
    assert (e.contest_total(
        election,
        jurisdiction,
        f"US House {abbr} District {cd}",
        dbname=dbname,
        )
        == total_cd_votes
    )


def test_state_senate_totals(dbname):
    assert (e.contest_total(
        election,
        jurisdiction,
        f"{abbr} Senate District {ssd}",
        dbname=dbname,
        )
        == total_ssd_votes
    )


def test_state_house_totals(dbname):
    assert (e.contest_total(
        election,
        jurisdiction,
        f"{abbr} House District {shd}",
        dbname=dbname,
        )
        == total_shd_votes
    )

""" 
# SC has non-standard vote types failsafe and failsafe-provisional
def test_standard_vote_types(dbname):
    assert e.check_count_types_standard(election, jurisdiction, dbname=dbname)
"""

def test_vote_type_counts_consistent(dbname):
    assert e.check_totals_match_vote_types(election, jurisdiction, dbname=dbname)


def test_count_type_subtotal(dbname):
    assert (e.contest_total(
        election,
        jurisdiction,
        f"US President ({abbr})",
        dbname=dbname,
        vote_type=single_vote_type,
        )
        == pres_votes_vote_type
    )


def test_county_subtotal(dbname):
    assert (e.contest_total(
        election,
        jurisdiction,
        f"US President ({abbr})",
        dbname=dbname,
        county=single_county,
        )
        == pres_votes_county
            )
