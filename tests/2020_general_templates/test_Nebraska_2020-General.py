import election_data_analysis as e

#NE20g test

def data_exists(dbname):
    assert e.data_exists("2020 General","Nebraska",dbname=dbname)

def test_presidential(dbname):
    assert(e.contest_total(
        "2020 General",
        "Nebraska",
        "US President (NE)",
        dbname=dbname,
        )
        == -1
    )

def test_congressional_totals(dbname):
    assert ( e.contest_total(
        "2020 General",
        "Nebraska",
        "congressional",
        dbname=dbname,
        )
        == -1
    )

def test_state_senate_totals(dbname):
    assert ( e.contest_total(
        "2020 General",
        "Nebraska",
        "state-senate",
        dbname=dbname,
        )
        == -1
    )

def test_state_house_totals(dbname):
    assert ( e.contest_total(
        "2020 General",
        "Nebraska",
        "state-house",
        dbname=dbname,
        )
        == -1
    )

