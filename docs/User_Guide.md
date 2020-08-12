# How to Use the System

## Get Started
 * Create the parameter files you'll need:
   * `analyzer.par` for Analyzer class if you want it
   * `new_jurisdiction.par` for the JurisdictionPrepper() class
   * `run_time.par` if you will be using DataLoader class to look in detail at one file/jurisdiction/munger
   * `multi.par` if you will be batch loading data. In this case the directory with your results file will need a `.par` file for each results file. See the `results.par` template
   
 * In a python interpreter, import the `election_anomaly` module and create a DataLoader() instance.
```
>>> import election_anomaly as ea
>>> dl = ea.DataLoader()
```
## Create or Repair a Munger
If the munger given in `run_time.par` does not exist, `DataLoader()` will create a folder for that munger, with template files and record the error. Then `check_error()` will show the errors. E.g.
```
>>> import election_anomaly as ea
>>> dl = ea.DataLoader(); dl.check_errors()
(None, None, None, None, {'newly_created': '/path/to/src/mungers/xx_general2018, cdf_elements.txt, format.txt'})
>>> 
```
Before proceeding, edit the munger files appropriately for your data file. The system may detect errors in your munger. E.g.
```
>>> dl=ea.DataLoader();dl.check_errors()
(None, None, None, None, {'format.txt': {'format_problems': 'Wrong number of rows in format.txt. \nFirst column must be exactly:\nheader_row_count\nfield_name_row\ncount_columns\nfile_type\nencoding\nthousands_separator'}})
>>> 
```
When all errors are fixed, your munger should be able to interpret your data file.

## Create or Improve a Jurisdiction
### Order of operations
1. Choose (or create) the munger for the results file.
1. Prepare your new_jurisdiction.par file, following the template. (`src/templates/parameter_file_templates/new_jurisdiction.par`)
2. Initialize a JurisdictionPrepper.
3. Call new_juris_files(), which will create the necessary files in the jurisdiction directory, as well as a starter dictionary file (`XX_starter_dictionary.txt`) in the current directory.
4. Insert any additional CandidateContests you care about into `CandidateContest.txt`, and the corresponding Offices into `Office.txt`. Note that every CandidateContest must have an Office, and that Office must be in `Office.txt`.
5. Revise `XX_starter_dictionary.txt` so that the raw_identifier_value entries match what will be munged from your datafile via the formulas in `cdf_elements.txt`. 
13. Move `XX_starter_dictionary.txt` from the current directory and to the jurisdiction's directory, and rename it to `dictionary.txt` (or append the entries of `XX_starter_dictionary.txt` to `dictionary.txt` and dedupe). 
5. Apply the formula from the munger's `cdf_elements.txt` to the results file to identify raw identifiers for the CandidateContests you care about, and modify the corresponding rows in `dictionary.txt`. 
6. If your munger is already set up you can use 

         `add_elements_from_results_file(<file_path>,<munger_name>,['Party','ReportingUnit','CandidateContest','Candidate,'BallotMeasureContest'])`
         
 to enter elements from the file into the jurisdiction files (including `dictionary.txt`). You may have to alter the resulting rows in both files to make sure the internal database names obey any conventions.
6. Otherwise, add any missing Parties to `Party.txt`. Modify or create the corresponding rows in `dictionary.txt` to match the party names that will be munged from the file.
8. Add all necessary ReportingUnits to `ReportingUnit.txt` (without creating duplicates). You MUST use the naming conventions with semicolons to indicate nesting of reporting units. The jurisdiction itself (e.g., `North Carolina`) and the districts for the standard district contests will be created by `new_juris_files()`. Typically -- even if you used `add_elements_from_results_file()` -- you will need to add:
    2. counties (e.g., `North Carolina;Alamance County`)
    4. any reporting units used in your results file, often precincts, nested within counties (e.g., `North Carolina;Alamance County;Precinct 064`). 
  and if you haven't used `add_elements_from_results_file()`, you will need to add:
    1. the jurisdiction itself (e.g., `North Carolina`)
    2. ElectionDistricts corresponding to Offices or BallotMeasureContests.
  
        Note: as of 8/2020, the system does not yet handle nesting of precincts inside contest districts.
    9. If you did not use `add_elements_from_results_file` in the previous step, modify or create the corresponding rows in `dictionary.txt`. (Note: you can omit ReportingUnits such as contest districts from `dictionary.txt` if they aren't needed to specify the vote count in the results file.)
10. If necessary, add the relevant election to `Election.txt`.
11. Add any BallotMeasureContests you care about to `BallotMeasureContest.txt` and `dictionary.txt`. 
    1. Choose raw identifiers for the BallotMeasureContests and modify `dictionary.txt` accordingly.
    1. Specify the ElectionDistrict, which must be in the `ReportingUnit.txt` file. (If you don't know the ElectionDistrict, nothing will break if you assign it the entire jurisdiction as ElectionDistrict.)
12. Add Candidates from the contests you care about to `Candidate.txt` and `dictionary.txt`.
    1. Choose raw identifiers for the Candidates and modify `dictionary.txt`
12. Add all CountItemTypes to `dictionary.txt`. 
13. Add any useful info about the jurisdiction (such as the sources for the data) to `remark.txt`.

### The JurisdictionPrepper class details
There are routines in the `JurisdictionPrepper()` class to help prepare a jurisdiction.
 * `JurisdictionPrepper()` reads parameters from the file (`new_jurisdiction.par`) to create the directories and basic necessary files. 
 * `new_juris_files()` builds a directory for the jurisdiction, including starter files with the standard contests. It calls some methods that may be independently useful:
   * `add_standard_contests()` creates records in `CandidateContest.txt` corresponding to contests that appear in many or most jurisdictions, including all federal offices as well as state house and senate offices. 
   * `add_primary_contests()` creates a record in `CandidateContest.txt` for every CandidateContest-Party pair that can be created from `CandidateContest.txt` entries with no assigned PrimaryParty and `Party.txt` entries. (Note: records for non-existent primary contests will not break anything.) 
   * `starter_dictionary()` creates a `starter_dictionary.txt` file in the current directory. Lines in this starter dictionary will *not* have the correct `raw_identifier_value` entries. Assigning the correct raw identifier values must be done by hand before proceeding.
 * `add_primaries_to_dict()` creates an entry in `dictionary.txt` for every CandidateContest-Party pair that can be created from the CandidateContests and Parties already in `dictioary.txt`. (Note: entries in `dictionary.txt` that never occur in your results file won't break anything.)
 * `add_elements_from_results_file(result_file,munger,element`) pulls raw identifiers for all instances of the element from the datafile and inserts corresponding rows in `<element>.txt` and `dictionary.txt`. These rows may have to be edited by hand to make sure the internal database names match any conventions (e.g., for ReportingUnits or CandidateContests, but maybe not for Candidates or BallotMeasureContests.)
 * `add_sub_county_rus_from_datafile(error)` is useful when:
     * county names can be munged from the rows
     * precinct (or other sub-county reporting unit) names can be munged from the rows
     * all counties are already in `dictionary.txt`
   
   can be read from _rows_ of the datafile. The method adds a record for each precinct to `ReportingUnit.txt` and `dictionary.txt`, with internal db name obeying the semicolon convention. For instance, if:
     * `ReportingUnit\tFlorida;Alachua County\tAlachua` is in `dictionary.txt
     * County name `Alachua` and precinct name `Precinct 1` can both be munged from the same row of the results file
     
     then:
     * `Florida;Alachua County;Precinct 1\tprecinct` will be added to `ReportingUnit.txt`
     * `ReportingUnit\tFlorida;Alachua County;Precinct 1\tAlachua;Precinct 1` will be added to `dictionary.txt`

 
## Load Data
Some routines in the Analyzer class are useful even in the data-loading process, so  create an analyzer before you start loading data.
```
>>> an = ea.Analyzer()
>>> 
```

### Load a single file with a single munger via DataLoader()
The DataLoader class has some checking routines that are useful for ensuring the munger and jurisdiction files are working.

Create a DataLoader instance and check for errors in the Jurisdiction and Munger directories specified in `run_time.par`
```
>>> dl = ea.DataLoader();dl.check_errors()
(None, None, None, None, None)
>>> 
```
If all errors are `None`, the DataLoader initialization will have loaded information in the Jurisdiction folder (e.g, contest and candidate names) into the database. You are ready to process the results file. The five error categories are: 

 0. parameter errors 
 1. missing files or consistency errors in existing jurisdiction directory
 2. errors due to non-existent jurisdiction directory
 3. errors arising during loading of jurisdiction data to the database
 4. errors in the munger. 

Insert information about your results file into the database. 
```
>>> dl.track_results()
>>> 
```
The arguments are a shorthand name for your results file and the name of the election. The name of the election must match the name of an election already in the database. To find all available election names, use the analyzer:
```
>>> an.display_options('election')
['2018 General', 'none or unknown']
>>> 
```
Finally, load results to the database. Even on a fast laptop this may take a few minutes for, say, a 7MB file. 
```
>>> dl.load_results()
Datafile contents uploaded to database Engine(postgresql://postgres:***@localhost:5432/Combined_0608)
>>> 
```
Note that only lines with data corresponding to contests, selections and reporting units listed in the Jurisdiction directory will be processed. 

### Batch Load Data
The MultiDataLoader class allows batch uploading of all data in a given directory. That directory should contain the files to be uploaded, as well as a `.par` file for each file to be uploaded. See `templates/parameter_file_templates/results.par`. You can use `make_par_files()` to create parameter files for multiple files when they share values of the following parameters:
 * directory in which the files can be found
 * munger
 * jurisdiction
 * election
 * download_date
 * source
 * note
 * auxiliary data directory (if any)
The `load_all()` method will read each `.par` file and make the corresponding upload.
From a directory containing a `multi.par` parameter file, run
```
import election_anomaly as ea
mdl = ea.MultiDataLoader()
err = mdl.load_all()
```

## Pull Data
The Analyzer class uses parameters in the file `analyze.par`, which should be in the directory from which you are running the program.

There are two options: pulling total vote counts, or pulling vote counts by vote type. To pull totals, use `top_counts()` in the Analyzer class.
```
>>> an.top_counts('Pennsylvania;Philadelphia','ward')
Results exported to /Users/user/Documents/rollups/2018 General/Pennsylvania;Philadelphia/by_ward/TYPEall_STATUSunknown.txt
```

To pull totals by vote type, use `top_counts_by_vote_type()`
```
>>> an.top_counts_by_vote_type('Pennsylvania;Philadelphia','ward')
Results exported to /Users/singer3/Documents/rollups/2018 General/Pennsylvania;Philadelphia/by_ward/TYPEmixed_STATUSunknown.txt
>>> 
```

Results are exported to the `rollup_directory` specified in `run_time.par`.

Note that both arguments -- the name of the top reporting unit ('Pennsylvania;Philadelphia') and the reporting unit type for the breakdown of results ('ward') must be the internal database names. To see the list of options, use `display_options()`:
```
>>> an.display_options('reporting_unit_type')
['ballot-batch', 'ballot-style-area', 'borough', 'city', 'city-council', 'combined-precinct', 'congressional', 'country', 'county', 'county-council', 'drop-box', 'judicial', 'municipality', 'polling-place', 'precinct', 'school', 'special', 'split-precinct', 'state', 'state-house', 'state-senate', 'town', 'township', 'utility', 'village', 'vote-center', 'ward', 'water', 'other']
```
Lists of reporting units will be quite long, in which case searching by substring can be useful.
```
>>> counties = an.display_options('county')
>>> [x for x in counties if 'Phila' in x]
['Pennsylvania;Philadelphia']
>>> 
```
Here we have used the capability of `display_options()` to take as an argument either a general database category ('reporting unit') or a type ('county'). 

```
