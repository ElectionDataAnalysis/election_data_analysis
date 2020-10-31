import election_data_analysis as e


def test_ga_presidential_18(dbname):
    # no presidential contests in 2018
    assert True == True


def test_ga_statewide_totals_18(dbname):
    assert (
        not e.data_exists("2018 General", "Georgia", dbname=dbname)
        or e.contest_total(
            "2018 General",
            "Georgia",
            "GA Governor",
            dbname=dbname,
        )
        == 3939328
    )


def test_ga_senate_totals_18(dbname):
    assert (
        not e.data_exists("2018 General", "Georgia", dbname=dbname)
        or e.contest_total(
            "2018 General",
            "Georgia",
            "GA Senate District 5",
            dbname=dbname,
        )
        == 34429
    )


def test_ga_house_totals_18(dbname):
    assert (
        not e.data_exists("2018 General", "Georgia", dbname=dbname)
        or e.contest_total(
            "2018 General",
            "Georgia",
            "US House GA District 2",
            dbname=dbname,
        )
        == 229171
    )


def test_ga_contest_by_vote_type_18(dbname):
    assert (
        not e.data_exists("2018 General", "Georgia", dbname=dbname)
        or e.count_type_total(
            "2018 General",
            "Georgia",
            "GA Senate District 5",
            "absentee-mail",
            dbname=dbname,
        )
        == 2335
    )


def test_ga_totals_match_vote_type_18(dbname):
    assert (
        not e.data_exists("2018 General", "Georgia", dbname=dbname)
        or e.check_totals_match_vote_types("2018 General", "Georgia", dbname=dbname)
        == True
    )
