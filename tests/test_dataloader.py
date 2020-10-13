from election_data_analysis import database as db
from election_data_analysis import user_interface as ui
from election_data_analysis import Analyzer
import pandas as pd
import os
from psycopg2 import sql
import pytest

def get_analyzer(p_path: str = None):
    one_up = os.path.dirname(os.getcwd())
    if p_path:
        param_file = p_path
    else:
        param_file = os.path.join(one_up, "src", "run_time.ini")
    a = Analyzer(param_file)
    return a


def aggregate_results(election, jurisdiction, contest_type, by_vote_type):
    # using the analyzer gives us access to DB session
    empty_df_with_good_cols = pd.DataFrame(columns=['contest','count'])
    a = get_analyzer()
    election_id = db.name_to_id(a.session, "Election", election)
    if not election_id:
        return empty_df_with_good_cols
    connection = a.session.bind.raw_connection()
    cursor = connection.cursor()

    datafile_list, e = db.data_file_list(cursor, election_id, by="Id")
    if e:
        print(e)
        return empty_df_with_good_cols
    if len(datafile_list) == 0:
        print(f"No datafiles found for Election_Id {election_id}")
        return empty_df_with_good_cols

    df, err_str = db.export_rollup_from_db(
        cursor,
        jurisdiction,
        "county",
        contest_type,
        datafile_list,
        by="Id",
        exclude_total=True,
        by_vote_type=True,
    )
    if df.empty:
        # TODO better logic? This is like throwing spaghetti at the wall
        # try without excluding total
        df, err_str = db.export_rollup_from_db(
            cursor,
            jurisdiction,
            "county",
            contest_type,
            datafile_list,
            by="Id",
            exclude_total=False,
            by_vote_type=True,
        )
    if err_str:
        return empty_df_with_good_cols
    return df


def data_exists(election, jurisdiction, p_path=None):
    a = get_analyzer(p_path=p_path)
    election_id = db.name_to_id(a.session, "Election", election)
    jurisdiction_id = db.name_to_id(a.session, "ReportingUnit", jurisdiction)
    con = a.session.bind.raw_connection()
    cur = con.cursor()
    q = sql.SQL('SELECT "Id" FROM _datafile WHERE "Election_Id" = %s AND "ReportingUnit_Id" = %s')
    cur.execute(q,(election_id,jurisdiction_id))

    answer = cur.fetchall()
    if len(answer) > 0:
        return True
    else:
        return False


def check_totals_match_vote_types(election, jurisdiction):
    df_candidate = aggregate_results(election, jurisdiction, "Candidate", False)
    df_ballot = aggregate_results(election, jurisdiction, "BallotMeasure", False)
    df_by_ttl = pd.concat([df_candidate, df_ballot])

    df_candidate = aggregate_results(election, jurisdiction, "Candidate", True)
    df_ballot = aggregate_results(election, jurisdiction, "BallotMeasure", True)
    df_by_type = pd.concat([df_candidate, df_ballot])
    return df_by_ttl["count"].sum() == df_by_type["count"].sum()


# A couple random contests
def check_contest_totals(election, jurisdiction, contest):
    df_candidate = aggregate_results(election, jurisdiction, "Candidate", False)
    df_ballot = aggregate_results(election, jurisdiction, "BallotMeasure", False)
    df = pd.concat([df_candidate, df_ballot])
    df = df[df["contest"] == contest]
    return df["count"].sum()


def check_count_type_totals(election, jurisdiction, contest, count_item_type):
    df_candidate = aggregate_results(election, jurisdiction, "Candidate", False)
    df_ballot = aggregate_results(election, jurisdiction, "BallotMeasure", False)
    df = pd.concat([df_candidate, df_ballot])
    df = df[df["contest"] == contest]
    df = df[df["count_item_type"] == count_item_type]
    return df["count"].sum()


# #### Tests start below #### #
# For each state, run at least 6 tests:
# 1. Presidential
# 2. One statewide chosen at random
# 3. One senate
# 4. One rep
# 5. If vote type is available, slice one of the above by vote type
# 6. If vote type is available, check that totals match vote type sums


### North Carolina Data Loading Tests ###
#constants
ok = {
    "nc16g": data_exists('2016 General','North Carolina'),
    "nc18g": data_exists('2018 General','North Carolina'),
    "nc20p": data_exists('2020 Primary','North Carolina'),
    "fl16g": data_exists('2016 General','Florida'),
    "fl18g": data_exists('2018 General','Florida'),
    "fl20p": data_exists('2020 Primary','Florida'),
    "pa16g": data_exists('2016 General','Pennsylvania'),
    "pa18g": data_exists('2018 General','Pennsylvania'),
    "pa20p": data_exists('2020 Primary','Pennsylvania'),
    "ga16g": data_exists('2016 General','Georgia'),
    "ga18g": data_exists('2018 General','Georgia'),
    "sc20ppp": data_exists('2020 President Preference Primary','South Carolina'),
    "in16g": data_exists('2016 General','Indiana'),
    "in18g": data_exists('2018 General','Indiana'),
    "in20p": data_exists('2020 Primary','Indiana'),
    "ar18g": data_exists('2018 General','Arkansas'),
    "mi16g": data_exists('2016 General','Michigan'),
    "mi18g": data_exists('2018 General','Michigan'),
    "mi20p": data_exists('2020 Primary','Michigan'),
    "mi20ppp": data_exists('2020 President Preference Primary','Michigan'),
    "de20ppp": data_exists('2020 Presidential Preference Primary','Delaware'),
    "de20pri": data_exists('2020 Primary','Delaware'),
    "oh16g": data_exists('2016 General','Ohio'),
    "oh18g": data_exists('2018 General','Ohio'),
    "il16g": data_exists('2016 General','Illinois'),
    "il18g": data_exists('2018 General','Illinois'),
    "il20p": data_exists('2020 Primary','Illinois'),
    "ca16g": data_exists('2016 General','California'),
    "ca18g": data_exists('2018 General','California'),
    "ca20p": data_exists('2020 Primary','California'),
    "ca20ppp": data_exists('2020 President Preference Primary','California'),
    "co16g": data_exists('2016 General','Colorado'),
    "co18g": data_exists('2018 General','Colorado'),
    "co20p": data_exists('2020 Primary','Colorado'),
    "co20ppp": data_exists('2020 President Preference Primary','Colorado'),
}

print(ok)
"""
### NC dataloading tests ###
#NC16 tests
@pytest.mark.skipif(not ok["nc16g"], reason="No NC 2016 General data")
def test_nc_presidential_16():
    assert(
        check_contest_totals(
            "2016 General",
            "North Carolina",
            "US President (NC)",
        )
        == 4741564
    )

@pytest.mark.skipif(not ok["nc16g"], reason="No NC 2016 General data")
def test_nc_statewide_totals_16():
    assert(
        check_contest_totals(
            "2016 General",
            "North Carolina",
            "NC Treasurer",
        )
        == 4502784
    )

@pytest.mark.skipif(not ok["nc16g"], reason="No NC 2016 General data")
def test_nc_senate_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "North Carolina",
            "US Senate NC",
        )
        == 4691133
    )

@pytest.mark.skipif(not ok["nc16g"], reason="No NC 2016 General data")
def test_nc_rep_16():
    assert (
        check_contest_totals(
            "2016 General",
            "North Carolina",
            "US House NC District 4",
        )
        == 409541
    )

@pytest.mark.skipif(not ok["nc16g"], reason="No NC 2016 General data")
def test_nc_contest_by_vote_type_16():
    assert (
        check_count_type_totals(
            "2016 General",
            "North Carolina",
            "US House NC District 4",
            "absentee-mail",
        )
        == 20881
    )

@pytest.mark.skipif(not ok["nc16g"], reason="No NC 2016 General data")
def test_nc_totals_match_vote_type_16():
    assert check_totals_match_vote_types("2016 General", "North Carolina") == True


#NC18 tests
@pytest.mark.skipif(not ok["nc18g"], reason="No NC 2018 General data")
def test_nc_presidential_18():
    # No presidential contests in 2018
    assert True == True


@pytest.mark.skipif(not ok["nc18g"], reason="No NC 2018 General data")
def test_nc_statewide_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "North Carolina",
            "US House NC District 3",
        )
        == 187901
    )


@pytest.mark.skipif(not ok["nc18g"], reason="No NC 2018 General data")
def test_nc_senate_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "North Carolina",
            "NC Senate District 15",
        )
        == 83175
    )


@pytest.mark.skipif(not ok["nc18g"], reason="No NC 2018 General data")
def test_nc_house_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "North Carolina",
            "NC House District 1",
        )
        == 27775
    )


@pytest.mark.skipif(not ok["nc18g"], reason="No NC 2018 General data")
def test_nc_contest_by_vote_type_18():
    assert (
        check_count_type_totals(
            "2018 General",
            "North Carolina",
            "US House NC District 4",
            "absentee-mail",
        )
        == 10778
    )

@pytest.mark.skipif(not ok["nc18g"], reason="No NC 2018 General data")
def test_nc_totals_match_vote_type_18():
    assert check_totals_match_vote_types("2018 General", "North Carolina") == True


#NC20 Tests
@pytest.mark.skipif(not ok["nc20p"], reason="No NC 2020 Primary data")
def test_nc_presidential_20():
    assert(
        check_contest_totals(
            "2020 Primary",
            "North Carolina",
            "US President (NC) (Democratic Party)",
        )
        == 1331366
    )

@pytest.mark.skipif(not ok["nc20p"], reason="No NC 2020 Primary data")
def test_nc_statewide_totals_20():
    assert(
        check_contest_totals(
            "2020 Primary",
            "North Carolina",
            "NC Governor (Democratic Party)",
        )
        == 1293652
    )

@pytest.mark.skipif(not ok["nc20p"], reason="No NC 2020 Primary data")
def test_nc_senate_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "North Carolina",
            "US Senate NC (Democratic Party)",
        )
        == 1260090
    )

@pytest.mark.skipif(not ok["nc20p"], reason="No NC 2020 Primary data")
def test_nc_rep_20_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "North Carolina",
            "US House NC District 4 (Republican Party)",
        )
        == 36096
    )

@pytest.mark.skipif(not ok["nc20p"], reason="No NC 2020 Primary data")
def test_nc_contest_by_vote_type_20():
    assert (
        check_count_type_totals(
            "2020 Primary",
            "North Carolina",
            "US House NC District 4 (Republican Party)",
            "absentee-mail",
        )
        == 426
    )

@pytest.mark.skipif(not ok["nc20p"], reason="No NC 2020 Primary data")
def test_nc_totals_match_vote_type_20():
    assert check_totals_match_vote_types("2020 General", "North Carolina") == True



### Florida Data Loading Tests ###
#FL16 test
@pytest.mark.skipif(not ok["fl16g"], reason="No FL 2016 General data")
def test_fl_presidential():
    assert (
        check_contest_totals(
            "2016 General",
            "Florida",
            "US President (FL)",
        )
        == 9420039
    )

@pytest.mark.skipif(not ok["fl16g"], reason="No FL 2016 General data")
def test_fl_statewide_totals():
    assert (
        check_contest_totals(
            "2016 General",
            "Florida",
            "US Senate FL",
        )
        == 9301820
    )

@pytest.mark.skipif(not ok["fl16g"], reason="No FL 2016 General data")
def test_fl_senate_totals():
    assert (
        check_contest_totals(
            "2016 General",
            "Florida",
            "FL Senate District 3",
        )
        == 236480
    )

@pytest.mark.skipif(not ok["fl16g"], reason="No FL 2016 General data")
def test_fl_house_totals():
    assert (
        check_contest_totals(
            "2016 General",
            "Florida",
            "US House FL District 10",
        )
        == 305989
    )

@pytest.mark.skipif(not ok["fl16g"], reason="No FL 2016 General data")
def test_fl_contest_by_vote_type():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["fl16g"], reason="No FL 2016 General data")
def test_fl_totals_match_vote_type():
    # Vote type not available
    assert True == True



#FL20 test
@pytest.mark.skipif(not ok["fl20p"], reason="No FL 2020 Primary data")
def test_fl_presidential_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Florida",
            "US President (FL)",
        )
        == 5958306
    )

@pytest.mark.skipif(not ok["fl20p"], reason="No FL 2020 Primary data")
def test_fl_statewide_totals_20():
    assert True == True

@pytest.mark.skipif(not ok["fl20p"], reason="No FL 2020 Primary data")
def test_fl_senate_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Florida",
            "FL Senate District 21",
    20
        == 54988
    )

@pytest.mark.skipif(not ok["fl20p"], reason="No FL 2020 Primary data")
def test_fl_house_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Florida",
            "US House FL District 11",
        )
        == 17445
    )

@pytest.mark.skipif(not ok["fl20p"], reason="No FL 2020 Primary data")
def test_fl_contest_by_vote_type_20():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["fl20p"], reason="No FL 2020 Primary data")
def test_fl_totals_match_vote_type_20():
    # Vote type not available
    assert True == True

### Pennsylvania Data Loading Tests ###
#PA16 tests
@pytest.mark.skipif(not ok["pa16g"], reason="No PA 2016 General data")
def test_pa_presidential_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Pennsylvania",
            "US President (PA)",
        )
        == 6115402
    )

@pytest.mark.skipif(not ok["pa16g"], reason="No PA 2016 General data")
def test_pa_statewide_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Pennsylvania",
            "PA Auditor General",
        )
        == 5916931
    )

@pytest.mark.skipif(not ok["pa16g"], reason="No PA 2016 General data")
def test_pa_senate_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Pennsylvania",
            "PA Senate District 41",
        )
        == 112283
    )

@pytest.mark.skipif(not ok["pa16g"], reason="No PA 2016 General data")
def test_pa_house_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Pennsylvania",
            "PA House District 21",
        )
        == 26453
    )

@pytest.mark.skipif(not ok["pa16g"], reason="No PA 2016 General data")
def test_pa_contest_by_vote_type_16():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["pa16g"], reason="No PA 2016 General data")
def test_pa_totals_match_vote_type_16():
    # Vote type not available
    assert True == True


#PA18 test
@pytest.mark.skipif(not ok["pa18g"], reason="No PA 2018 General data")
def test_pa_presidential_18():
    assert True == True

@pytest.mark.skipif(not ok["pa18g"], reason="No PA 2018 General data")
def test_pa_statewide_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Pennsylvania",
            "PA Governor",
        )
        == 5012555
    )

@pytest.mark.skipif(not ok["pa18g"], reason="No PA 2018 General data")
def test_pa_senate_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Pennsylvania",
            "PA Senate District 20",
        )
        == 81817
    )

@pytest.mark.skipif(not ok["pa18g"], reason="No PA 2018 General data")
def test_pa_house_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Pennsylvania",
            "PA House District 103",
        )
        == 18363
    )

@pytest.mark.skipif(not ok["pa18g"], reason="No PA 2018 General data")
def test_pa_contest_by_vote_type_18():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["pa18g"], reason="No PA 2018 General data")
def test_pa_totals_match_vote_type_18():
    # Vote type not available
    assert True == True

#PA20
@pytest.mark.skipif(not ok["pa20p"], reason="No PA 2020 Primary data")
def test_pa_presidential_20():
    assert (
        check_contest_totals(
            "2020 General",
            "Pennsylvania",
            "US President (PA)",
        )
        == 2739007
    )

@pytest.mark.skipif(not ok["pa20p"], reason="No PA 2020 Primary data")
def test_pa_statewide_totals_20():
    assert (
        check_contest_totals(
            "2020 General",
            "Pennsylvania",
            "PA Governor",
        )
        == 2484582
    )

@pytest.mark.skipif(not ok["pa20p"], reason="No PA 2020 Primary data")
def test_pa_senate_totals_20():
    assert (
        check_contest_totals(
            "2020 General",
            "Pennsylvania",
            "PA Senate District 20",
        )
        == 67898
    )

@pytest.mark.skipif(not ok["pa20p"], reason="No PA 2020 Primary data")
def test_pa_house_totals_20():
    assert (
        check_contest_totals(
            "2020 General",
            "Pennsylvania",
            "PA House District 100",
        )
        == 6327
    )

@pytest.mark.skipif(not ok["pa20p"], reason="No PA 2020 Primary data")
def test_pa_contest_by_vote_type_20():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["pa20p"], reason="No PA 2020 Primary data")
def test_pa_totals_match_vote_type_20():
    # Vote type not available
    assert True == True


### Georgia Data Loading Tests ###
#GA16
@pytest.mark.skipif(not ok["ga16g"], reason="No GA 2016 General data")
def test_ga_presidential_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Georgie",
            "US President (GA)",
        )
        == 2739007
    )

#GA18
@pytest.mark.skipif(not ok["ga18g"], reason="No GA 2018 General data")
def test_ga_presidential_18():
    #no presidential contests in 2018
    assert True == True

@pytest.mark.skipif(not ok["ga18g"], reason="No GA 2018 General data")
def test_ga_statewide_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Georgia",
            "GA Governor",
        )
        == 3939328
    )

@pytest.mark.skipif(not ok["ga18g"], reason="No GA 2018 General data")
def test_ga_senate_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Georgia",
            "GA Senate District 5",
        )
        == 34429
    )

@pytest.mark.skipif(not ok["ga18g"], reason="No GA 2018 General data")
def test_ga_house_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Georgia",
            "US House GA District 2",
        )
        == 229171
    )

@pytest.mark.skipif(not ok["ga18g"], reason="No GA 2018 General data")
def test_ga_contest_by_vote_type_18():
    assert (
        check_count_type_totals(
            "2018 General",
            "Georgia",
            "GA Senate District 5",
            "absentee-mail",
        )
        == 2335
    )

@pytest.mark.skipif(not ok["ga18g"], reason="No GA 2018 General data")
def test_ga_totals_match_vote_type_18():
    assert check_totals_match_vote_types("2018 General", "Georgia") == True



### South Carolina Data Loading Tests ###
@pytest.mark.skipif(not ok["sc20ppp"], reason="No SC PPP data")
def test_sc_presidential():
    #only 2020 democratic presidental primary results loaded
    assert True == True

@pytest.mark.skipif(not ok["sc20ppp"], reason="No SC PPP data")
def test_sc_statewide_totals():
    #only 2020 democratic presidental primary results loaded
    assert True == True

@pytest.mark.skipif(not ok["sc20ppp"], reason="No SC PPP data")
def test_sc_senate_totals():
    #only 2020 democratic presidental primary results loaded
    assert True == True

@pytest.mark.skipif(not ok["sc20ppp"], reason="No SC PPP data")
def test_sc_house_totals():
    #only 2020 democratic presidental primary results loaded
    assert True == True

@pytest.mark.skipif(not ok["sc20ppp"], reason="No SC PPP data")
def test_sc_contest_by_vote_type():
    #only 2020 democratic presidental primary results loaded
    assert True == True

@pytest.mark.skipif(not ok["sc20ppp"], reason="No SC PPP data")
def test_sc_totals_match_vote_type():
    #only 2020 democratic presidental primary results loaded
    assert True == True


### Indiana Data Loading Tests ###
#IN16 test
@pytest.mark.skipif(not ok["in16g"], reason="No IN 2016 General data")
def test_in_presidential_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Indiana",
            "US President (IN)",
        )
        == 2728138
    )

@pytest.mark.skipif(not ok["in16g"], reason="No IN 2016 General data")
def test_in_statewide_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Indiana",
            "IN Attorney General",
        )
        == 2635832
    )

@pytest.mark.skipif(not ok["in16g"], reason="No IN 2016 General data")
def test_in_senate_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Indiana",
            "IN Senate District 7",
        )
        == 50622
    )

@pytest.mark.skipif(not ok["in16g"], reason="No IN 2016 General data")
def test_in_house_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Indiana",
            "IN House District 13",
        )
        == 26712
    )

@pytest.mark.skipif(not ok["in16g"], reason="No IN 2016 General data")
def test_in_contest_by_vote_type_16():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["in16g"], reason="No IN 2016 General data")
def test_in_totals_match_vote_type_16():
    # Vote type not available
    assert True == True

#IN18 test
@pytest.mark.skipif(not ok["in18g"], reason="No IN 2018 General data")
def test_in_presidential_18():
    assert True == True

@pytest.mark.skipif(not ok["in18g"], reason="No IN 2018 General data")
def test_in_statewide_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Indiana",
            "US Senate IN",
        )
        == 2282565
    )

@pytest.mark.skipif(not ok["in18g"], reason="No IN 2018 General data")
def test_in_senate_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Indiana",
            "IN Senate District 14",
        )
        == 34542
    )

@pytest.mark.skipif(not ok["in18g"], reason="No IN 2018 General data")
def test_in_house_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Indiana",
            "IN House District 27",
        )
        == 12238
    )

@pytest.mark.skipif(not ok["in18g"], reason="No IN 2018 General data")
def test_in_contest_by_vote_type_18():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["in18g"], reason="No IN 2018 General data")
def test_in_totals_match_vote_type_18():
    # Vote type not available
    assert True == True

#IN20 test
@pytest.mark.skipif(not ok["in20p"], reason="No IN 2020 Primary data")
def test_in_presidential_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Indiana",
            "US President (IN)",
        )
        == 1047173
    )

@pytest.mark.skipif(not ok["in20p"], reason="No IN 2020 Primary data")
def test_in_statewide_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Indiana",
            "IN Governor",
        )
        == 932726
    )

@pytest.mark.skipif(not ok["in20p"], reason="No IN 2020 Primary data")
def test_in_senate_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Indiana",
            "IN Senate District 50",
        )
        == 6860
    )

@pytest.mark.skipif(not ok["in20p"], reason="No IN 2020 Primary data")
def test_in_house_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Indiana",
            "IN House District 3",
        )
        == 7975
    )

@pytest.mark.skipif(not ok["in20p"], reason="No IN 2020 Primary data")
def test_in_contest_by_vote_type_20():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["in20p"], reason="No IN 2020 Primary data")
def test_in_totals_match_vote_type_20():
    # Vote type not available
    assert True == True


### Arkansas Data Loading Tests ###
@pytest.mark.skipif(not ok["ar18g"], reason="No AR 2018 General data")
def test_ar_presidential():
    #no presidential contests in 2018
    assert True == True

@pytest.mark.skipif(not ok["ar18g"], reason="No AR 2018 General data")
def test_ar_statewide_totals():
    assert (
        check_contest_totals(
            "2018 General",
            "Arkansas",
            "AR Governor",
        )
        == 891509
    )

@pytest.mark.skipif(not ok["ar18g"], reason="No AR 2018 General data")
def test_ar_senate_totals():
    assert (
        check_contest_totals(
            "2018 General",
            "Arkansas",
            "AR Senate District 5",
        )
        == 27047
    )

@pytest.mark.skipif(not ok["ar18g"], reason="No AR 2018 General data")
def test_ar_house_totals():
    assert (
        check_contest_totals(
            "2018 General",
            "Arkansas",
            "AR House District 19",
        )
        == 7927
    )

@pytest.mark.skipif(not ok["ar18g"], reason="No AR 2018 General data")
def test_ar_contest_by_vote_type():
    assert (
        check_count_type_totals(
            "2018 General",
            "Arkansas",
            "AR Senate District 5",
            "absentee",
        )
        == 453
    )

@pytest.mark.skipif(not ok["ar18g"], reason="No AR 2018 General data")
def test_ar_totals_match_vote_type():
    assert check_totals_match_vote_types("2018 General", "Arkansas") == True


### Michigan Data Loading Tests ###
#MI16 test
@pytest.mark.skipif(not ok["mi16g"], reason="No MI 2016 General data")
def test_mi_presidential_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Michigan",
            "US President (MI)",
        )
        == 4799284
    )

@pytest.mark.skipif(not ok["mi16g"], reason="No MI 2016 General data")
def test_mi_statewide_totals_16():
    assert True == True

@pytest.mark.skipif(not ok["mi16g"], reason="No MI 2016 General data")
def test_mi_us_rep_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Michigan",
            "US House MI District 4",
        )
        == 315751
    )
@pytest.mark.skipif(not ok["mi16g"], reason="No MI 2016 General data")
def test_mi_house_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Michigan",
            "MI House District 8",
        )
        == 34742
    )

@pytest.mark.skipif(not ok["mi16g"], reason="No MI 2016 General data")
def test_mi_contest_by_vote_type_16():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["mi16g"], reason="No MI 2016 General data")
def test_mi_totals_match_vote_type_16():
    # Vote type not available
    assert True == True

#MI18 test
@pytest.mark.skipif(not ok["mi18g"], reason="No MI 2018 General data")
def test_mi_presidential_18():
    #no presidential contests in 2018
    assert True == True

@pytest.mark.skipif(not ok["mi18g"], reason="No MI 2018 General data")
def test_mi_statewide_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Michigan",
            "MI Governor",
        )
        == 4250585
    )

@pytest.mark.skipif(not ok["mi18g"], reason="No MI 2018 General data")
def test_mi_senate_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Michigan",
            "MI Senate District 37",
        )
        == 124414
    )
@pytest.mark.skipif(not ok["mi18g"], reason="No MI 2018 General data")
def test_mi_house_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Michigan",
            "MI House District 8",
        )
        == 28017
    )

@pytest.mark.skipif(not ok["mi18g"], reason="No MI 2018 General data")
def test_mi_contest_by_vote_type_18():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["mi18g"], reason="No MI 2018 General data")
def test_mi_totals_match_vote_type_18():
    # Vote type not available
    assert True == True

#MI20 test
@pytest.mark.skipif(not ok["mi20p"], reason="No MI 2020 Primary data")
def test_mi_statewide_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Michigan",
            "US Senate MI (Democratic Party)",
        )
        == 1180780
    )

@pytest.mark.skipif(not ok["mi20p"], reason="No MI 2020 Primary data")
def test_mi_us_rep_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Michigan",
            "US House MI District 9 (Democratic Party)",
        )
        == 103202
    )

@pytest.mark.skipif(not ok["mi20p"], reason="No MI 2020 Primary data")
def test_mi_state_rep_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Michigan",
            "MI House District 37 (Republican Party)",
        )
        == 6669
    )

@pytest.mark.skipif(not ok["mi20p"], reason="No MI 2020 Primary data")
def test_mi_contest_by_vote_type_20():
    # Vote type not available
    assert True == True

@pytest.mark.skipif(not ok["mi20p"], reason="No MI 2020 Primary data")
def test_mi_totals_match_vote_type_20():
    # Vote type not available
    assert True == True


@pytest.mark.skipif(not ok["mi20ppp"], reason="No MI 2020 PPP data")
def test_mi_presidential_20ppp():
    assert (
        check_contest_totals(
            #"2020 Primary",
            "2020 Presidential Preference Primary",
            "Michigan",
            "US President (MI) (Democratic Party)",
        )
        == 4250585
    )


### Delaware 2020 Primary Data Loading Tests ###
@pytest.mark.skipif(not ok["de20pri"], reason="No DE 2020 Primary data")
def test_de_statewide_totals():
    assert (
            check_contest_totals(
                "2020 Primary",
                "Delaware",
                "DE Governor (Republican Party)",
            )
            == 55447
    )

@pytest.mark.skipif(not ok["de20pri"], reason="No DE 2020 Primary data")
def test_de_senate_totals():
    assert (
            check_contest_totals(
                "2020 Primary",
                "Delaware",
                "DE Senate District 13 (Democratic Party)",
            )
            == 5940
    )

@pytest.mark.skipif(not ok["de20pri"], reason="No DE 2020 Primary data")
def test_de_house_totals():
    assert (
            check_contest_totals(
                "2020 Primary",
                "Delaware",
                "DE House District 26 (Democratic Party)",
            )
            == 2990
    )

@pytest.mark.skipif(not ok["de20pri"], reason="No DE 2020 Primary data")
def test_de_contest_by_vote_type():
    assert (
        check_count_type_totals(
            "2020 Primary",
            "Delaware",
            "DE Senate District 14 (Republican Party)",
            "absentee",
        )
        == 559
    )

@pytest.mark.skipif(not ok["de20ppp"], reason="No DE 2020 Presidential Preference Primary data")
def test_de_presidential():
    assert (
        check_contest_totals(
            "2020 Presidential Preference Primary",
            "Delaware",
            "US President (DE) (Democratic Party)",
        )
        == 91682
    )

@pytest.mark.skipif(not ok["de20ppp"], reason="No DE 2020 Presidential Preference Primary data")
def test_de_totals_match_vote_type():
    assert check_totals_match_vote_types("2020 Presidential Preference Primary", "Delaware") == True


### Ohio Data Loading Tests ###
## oh 2016g tests
@pytest.mark.skipif(not ok["oh16g"], reason="No OH 2016 General data")
def test_oh_statewide():
    # No tracked statewide contests other than president,
    assert True == True


@pytest.mark.skipif(not ok["oh16g"], reason="No OH 2016 General data")
def test_oh_presidential():
    assert (
        check_contest_totals(
            "2016 General",
            "Ohio",
            "US President (OH)",
        )
        == 5496487
    )


@pytest.mark.skipif(not ok["oh16g"], reason="No OH 2016 General data")
def test_oh_senate_totals():
    assert (
        check_contest_totals(
            "2016 General",
            "Ohio",
            "OH Senate District 16",
        )
        == 185531
    )


@pytest.mark.skipif(not ok["oh16g"], reason="No OH 2016 General data")
def test_oh_house_totals():
    assert (
        check_contest_totals(
            "2016 General",
            "Ohio",
            "OH House District 2",
        )
        == 51931
    )


@pytest.mark.skipif(not ok["oh16g"], reason="No OH 2016 General data")
def test_oh_contest_by_vote_type():
    assert (
        check_count_type_totals(
            "2016 General",
            "Ohio",
            "US House OH District 5",
            "total",
        )
        == 344991
    )


@pytest.mark.skipif(not ok["oh16g"], reason="No OH 2016 General data")
def test_oh_totals_match_vote_type():
    assert check_totals_match_vote_types("2016 General", "Ohio") == True

#OH18 test
@pytest.mark.skipif(not ok["oh18g"], reason="No OH 2018 General data")
def test_oh_presidential():
    assert True == True

@pytest.mark.skipif(not ok["oh16g"], reason="No OH 2016 General data")
def test_oh_statewide():
    assert (
        check_contest_totals(
            "2016 General",
            "Ohio",
            "US President (OH)",
        )
        == 5496487
    )


### Illinois Data Loading Tests ###
@pytest.mark.skipif(not ok["il16g"], reason="No IL 2016 General data")
def test_il_presidential_16():
    assert(
        check_contest_totals(
            "2016 General",
            "Illinois",
            "US President (IL)",
        )
        == 5536424
    )

@pytest.mark.skipif(not ok["il16g"], reason="No IL 2016 General data")
def test_il_statewide_totals_16():
    assert(
        check_contest_totals(
            "2016 General",
            "Illinois",
            "IL Comptroller",
        )
        == 5412543
    )

@pytest.mark.skipif(not ok["il16g"], reason="No IL 2016 General data")
def test_il_senate_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Illinois",
            "US Senate IL",
        )
        == 5491878
    )

@pytest.mark.skipif(not ok["il16g"], reason="No IL 2016 General data")
def test_il_rep_16():
    assert (
        check_contest_totals(
            "2016 General",
            "Illinois",
            "IL Senate District 14",
        )
        == 79949
    )

@pytest.mark.skipif(not ok["il16g"], reason="No IL 2016 General data")
def test_il_contest_by_vote_type_16():
    assert True == True

@pytest.mark.skipif(not ok["il16g"], reason="No IL 2016 General data")
def test_il_totals_match_vote_type_16():
    assert True == True

#IL18 test
@pytest.mark.skipif(not ok["il18g"], reason="No IL 2018 General data")
def test_il_presidential_18():
    assert True == True

@pytest.mark.skipif(not ok["il18g"], reason="No IL 2018 General data")
def test_il_statewide_totals_18():
    assert(
        check_contest_totals(
            "2018 General",
            "Illinois",
            "IL Governor",
        )
        == 4547657
    )

@pytest.mark.skipif(not ok["il18g"], reason="No IL 2018 General data")
def test_il_senate_totals_18():
    assert True == True

@pytest.mark.skipif(not ok["il18g"], reason="No IL 2018 General data")
def test_il_rep_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Illinois",
            "IL House District 10",
        )
        == 31649
    )

@pytest.mark.skipif(not ok["il18g"], reason="No IL 2018 General data")
def test_il_contest_by_vote_type_18():
    assert True == True

@pytest.mark.skipif(not ok["il18g"], reason="No IL 2018 General data")
def test_il_totals_match_vote_type_18():
    assert True == True

#IL20 test
@pytest.mark.skipif(not ok["il20p"], reason="No IL 2020 Primary data")
def test_il_presidential_20():
    assert(
        check_contest_totals(
            "2020 Primary",
            "Illinois",
            "US President (IL)",
        )
        == 2216933
    )

@pytest.mark.skipif(not ok["il20p"], reason="No IL 2020 Primary data")
def test_il_statewide_totals_20():
    assert(
        check_contest_totals(
            "2020 Primary",
            "Illinois",
            "US Senate IL",
        )
        == 1941286
    )

@pytest.mark.skipif(not ok["il20p"], reason="No IL 2020 Primary data")
def test_il_state_senate_totals_20():
    assert(
        check_contest_totals(
            "2020 Primary",
            "Illinois",
            "IL Senate District 11",
        )
        == 22716
    )

@pytest.mark.skipif(not ok["il20p"], reason="No IL 2020 Primary data")
def test_il_state_rep_totals_20():
    assert(
        check_contest_totals(
            "2020 Primary",
            "Illinois",
            "IL House District 60",
        )
        == 8888
    )

@pytest.mark.skipif(not ok["il20p"], reason="No IL 2020 Primary data")
def test_il_contest_by_vote_type_20():
    assert True == True

@pytest.mark.skipif(not ok["il20p"], reason="No IL 2020 Primary data")
def test_il_totals_match_vote_type_20():
    assert True == True


### California Data Loading Tests ###
#CA16 test
@pytest.mark.skipif(not ok["ca16g"], reason="No ca 2016 General data")
def test_ca_presidential_16():
    assert(
        check_contest_totals(
            "2016 General",
            "California",
            "US President (CA)",
        )
        == 14181595
    )

@pytest.mark.skipif(not ok["ca16g"], reason="No CA 2016 General data")
def test_ca_statewide_totals_16():
    assert(
        check_contest_totals(
            "2016 General",
            "California",
            "US Senate CA",
        )
        == 12244170
    )

@pytest.mark.skipif(not ok["ca16g"], reason="No CA 2016 General data")
def test_ca_senate_totals_16():
    assert (
        check_contest_totals(
            "2016 General",
            "California",
            "CA Senate District 15",
        )
        == 313531
    )

@pytest.mark.skipif(not ok["ca16g"], reason="No CA 2016 General data")
def test_ca_rep_16():
    assert (
        check_contest_totals(
            "2016 General",
            "California",
            "CA House District 60",
        )
        == 142114
    )

@pytest.mark.skipif(not ok["ca16g"], reason="No CA 2016 General data")
def test_ca_contest_by_vote_type_16():
    assert True == True

@pytest.mark.skipif(not ok["ca16g"], reason="No CA 2016 General data")
def test_ca_totals_match_vote_type_16():
    assert True == True


#CA18 test
@pytest.mark.skipif(not ok["ca18g"], reason="No ca 2018 General data")
def test_ca_presidential_18():
    assert True == True

@pytest.mark.skipif(not ok["ca18g"], reason="No CA 2018 General data")
def test_ca_statewide_totals_18():
    assert(
        check_contest_totals(
            "2018 General",
            "California",
            "US Senate CA",
        )
        == 11113364
    )

@pytest.mark.skipif(not ok["ca18g"], reason="No CA 2018 General data")
def test_ca_senate_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "California",
            "CA Senate District 12",
        )
        == 203077
    )

@pytest.mark.skipif(not ok["ca18g"], reason="No CA 2018 General data")
def test_ca_rep_18():
    assert (
        check_contest_totals(
            "2018 General",
            "California",
            "CA House District 60",
        )
        == 125660
    )

@pytest.mark.skipif(not ok["ca18g"], reason="No CA 2018 General data")
def test_ca_contest_by_vote_type_18():
    assert True == True

@pytest.mark.skipif(not ok["ca18g"], reason="No CA 2018 General data")
def test_ca_totals_match_vote_type_18():
    assert True == True


#CA20 test
@pytest.mark.skipif(not ok["ca20p"], reason="No ca 2020 Primary data")
def test_ca_presidential_20():
    assert True == True

@pytest.mark.skipif(not ok["ca20p"], reason="No CA 2020 Primary data")
def test_ca_statewide_totals_20():
    assert(
        check_contest_totals(
            "2020 Primary",
            "California",
            "US Senate CA",
        )
        == 11113364
    )

@pytest.mark.skipif(not ok["ca20p"], reason="No CA 2020 Primary data")
def test_ca_senate_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "California",
            "CA Senate District 12",
        )
        == 203077
    )

@pytest.mark.skipif(not ok["ca20p"], reason="No CA 2020 Primary data")
def test_ca_rep_18():
    assert (
        check_contest_totals(
            "2020 Primary",
            "California",
            "CA House District 60",
        )
        == 125660
    )

@pytest.mark.skipif(not ok["ca20p"], reason="No CA 2020 Primary data")
def test_ca_contest_by_vote_type_20():
    assert True == True

@pytest.mark.skipif(not ok["ca20p"], reason="No CA 2020 Primary data")
def test_ca_totals_match_vote_type_20():
    assert True == True

@pytest.mark.skipif(not ok["ca20ppp"], reason="No ca 2020 PPP data")
def test_ca_presidential_20ppp():
    assert(
        check_contest_totals(
            "2020 President Preference Primary",
            "California",
            "US President (CA)",
        )
        == 2780247
    )


### Colorado Data Loading Tests ###
#CO16 test
@pytest.mark.skipif(not ok["co16g"], reason="No CO 2016 General data")
def test_co_presidential_16():
    assert(
        check_contest_totals(
            "2016 General",
            "Colorado",
            "US President (CO)",
        )
        == 2780247
    )

@pytest.mark.skipif(not ok["co20p"], reason="No CO 2020 Primary data")
def test_co_senate_totals_20():
    assert (
        check_contest_totals(
            "2020 Primary",
            "Colorado",
            "CO Senate District 14",
        )
        == 313531
    )


#CO18 test
@pytest.mark.skipif(not ok["co18g"], reason="No CO 2018 General data")
def test_co_presidential_18():
    assert True == True

@pytest.mark.skipif(not ok["co18g"], reason="No CO 2018 General data")
def test_co_statewide_totals_18():
    assert(
        check_contest_totals(
            "2018 General",
            "Colorado",
            "CO Attorney General",
        )
        == 2491954
    )

@pytest.mark.skipif(not ok["co18g"], reason="No CO 2018 General data")
def test_co_senate_totals_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Colorado",
            "CO Senate District 15",
        )
        == 313531
    )

@pytest.mark.skipif(not ok["co18g"], reason="No CO 2018 General data")
def test_co_rep_18():
    assert (
        check_contest_totals(
            "2018 General",
            "Colorado",
            "CO House District 60",
        )
        == 142114
    )

@pytest.mark.skipif(not ok["co18g"], reason="No CO 2018 General data")
def test_co_contest_by_vote_type_18():
    assert True == True

@pytest.mark.skipif(not ok["co18g"], reason="No CO 2018 General data")
def test_co_totals_match_vote_type_18():
    assert True == True
"""
