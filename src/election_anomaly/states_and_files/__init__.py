#!usr/bin/python3
import os.path
import db_routines as dbr
import pandas as pd
import re
import munge_routines as mr
from sqlalchemy.orm import sessionmaker
import user_interface as ui

# TODO: ReportingUnit cdf_table has CountItemStatus field, so particular precincts, counties, etc.,
#  aren't really "ReportingUnits" but rather "ReportingUnits without specified CountItemStatus". Hm.


class State:
    def create_db(self):
        # create db
        con = dbr.establish_connection()
        cur = con.cursor()
        dbr.create_database(con,cur,self.short_name)
        cur.close()
        con.close()
        return

    def add_to_context_dir(self,element,df):
        """Add the data in the dataframe <f> to the file corresponding
        to <element> in the <state>'s context folder.
        <f> must have all columns matching the columns in context/<element>.
        OK for <f> to have extra columns"""
        # TODO
        try:
            elts = pd.read_csv('{}context/{}.txt'.format(self.path_to_state_dir,element),sep='\t')
        except FileNotFoundError:
            print('File {}context/{}.txt does not exist'.format(self.path_to_state_dir,element))
            return
        else:
            for col in elts.columns:
                if col not in df.columns:
                    print('WARNING: Column {} not found, will be added with no data.'.format(col))
                    print('Be sure all necessary data is added before processing the file')
                    df.loc[:,col] = ''
            # pull and order necessary columns from <df>
            df_new = pd.concat([df[elts.columns],elts])
            df_new.to_csv('{}context/{}.txt'.format(self.path_to_state_dir,element),sep='\t',index=False)

            # TODO insert into cdf.<element>, using mr.load_context_dframe_into_cdf

            return

    def __init__(self,short_name,path_to_parent_dir):        # reporting_units,elections,parties,offices):
        """ short_name is the name of the directory containing the state info, including data,
         and is used other places as well.
         path_to_parent_dir is the parent directory of dir_name
        """
        self.short_name = short_name
        if path_to_parent_dir[-1] != '/':     # should end in /
            path_to_parent_dir += '/'
        self.path_to_state_dir = path_to_parent_dir + short_name+'/'
        assert os.path.isdir(self.path_to_state_dir), 'Error: No directory ' + self.path_to_state_dir
        assert os.path.isdir(self.path_to_state_dir+'context/'), \
            'Error: No directory ' + self.path_to_state_dir+'context/'
        # Check that context directory is missing no essential files
        context_file_list = ['Office.txt','remark.txt','ReportingUnit.txt']
        file_missing_list = [ff for ff in context_file_list
                             if not os.path.isfile(f'{self.path_to_state_dir}context/{ff}')]
        assert file_missing_list == [], \
            f'Error: Missing files in {os.path.join(self.path_to_state_dir,"context")}:\n{file_missing_list}'


class Munger:
    def office_check(self,results,state,sess):
        # TODO bug: didn't catch missing items in NC_test2 raw_identifiers

        mr.add_munged_column(results,self,'Office','Office_external')
        results_offices = results['Office_external'].unique()
        offices_ext = list(results_offices)

        mu_offices = self.raw_identifiers[self.raw_identifiers.cdf_element=='Office']
        offices_mixed = pd.DataFrame(results_offices,columns=['Office_external']).merge(mu_offices,how='left',
                                                                                        left_on='Office_external',right_on='raw_identifier_value')

        # are there offices in results file that cannot be munged?
        not_munged = offices_mixed[offices_mixed.raw_identifier_value.isnull()].loc[:,'Office_external'].to_list()
        if len(not_munged) > 0:
            print(f'Some offices in the results file cannot be interpreted by the munger {self.name}.')
            ui.show_sample(not_munged,'offices in datafile','cannot be munged',label='unmunged')
            add_to_munger = input('Would you like to add some/all of these to the munger (y/n)?\n')
            if add_to_munger == 'y':
                input(f'Edit the file {self.name}/raw_identifiers.txt. Add a line for each office you want to add,\n'
                      f'including a name to be used internally in the Common Data Format database Name field.\n'
                      f'Then edit the file {state}/context/Office.txt, adding a line for each new office.\n'
                      f'You may need to do some contextual research to fill all the fields in Office.txt')

                input('Then hit return to continue.\n')

        db_office_df = pd.read_sql_table('Office',sess.bind)
        db_offices = list(db_office_df['Name'].unique())
        # TODO allow user to stash offices not of interest in a munger file


        # are there offices recognized by munger but not in db?
        munged_offices = offices_mixed[offices_mixed.raw_identifier_value.notnull()].loc[:,'Office_external'].to_list()
        bad_set = {x for x in results_offices if x not in munged_offices}

        if len(bad_set) > 0:
            print('Results for offices missing from database will not be processed.')
            ui.show_sample(bad_set,'offices in datafile','are not in the database',label='not_in_db')
            add_to_db = input('Would you like to add some/all of these to the database (y/n)?\n')
            if add_to_db == 'y':
                context_template_path = os.path.join(
                    os.path.abspath(os.path.join(state.path_to_state_dir, os.pardir)),'context_templates')
                ru_type = pd.read_sql_table('ReportingUnitType',con,schema=schema,index_col='Id')
                standard_ru_types = set(ru_type[ru_type.Txt != 'other']['Txt'])

                ru = ui.fill_context_file(os.path.join(state.path_to_state_dir,'context'),
                                          context_template_path,
                                          'ReportingUnit',standard_ru_types,'ReportingUnitType')
                ru_list = ru['Name'].to_list()
                ui.fill_context_file(os.path.join(state.path_to_state_dir,'context'),context_template_path,
                                     'Office',ru_list,'ElectionDistrict',
                                     reportingunittype_list=standard_ru_types)
        # load new RUs and Offices to db
        # TODO will we need Party for primaries? If not here, then for CandidateContest somewhere
        for element in ['ReportingUnit','Office']:
            source_df = pd.read_csv(f'{state.path_to_state_dir}context/{element}.txt',sep='\t')
            mr.load_context_dframe_into_cdf(sess,source_df,element)

        # update munger with any new raw_identifiers
        self.raw_identifiers=pd.read_csv(os.path.join(self.path_to_munger_dir,'raw_identifiers.txt'),sep='\t')
        return

    def raw_cols_match(self,df):
        cols = self.raw_columns.name
        return set(df.columns).issubset(cols)

    def check_new_results_dataset(self,results,state,sess,contest_type):
        """<results> is a results dataframe of a single <contest_type>;
        this routine should add what's necessary to the munger to treat the dataframe,
        keeping backwards compatibility and exiting gracefully if dataframe needs different munger."""

        print(f'WARNING: All ReportingUnits in this file will be munged as type \'{self.atomic_reporting_unit_type}\'.')
        print('\tIf other behavior is desired, create or use another munger.')
        check_ru_type = input('\tProceed with munger {} (y/n)?\n'.format(self.name))
        if check_ru_type != 'y':
            print('Datafile will not be processed.')
            return

        assert self.raw_cols_match(results), \
            f"""A column in {results.columns} is missing from raw_columns.txt."""

        if contest_type == 'Candidate':
            offices_finalized = False
            while not offices_finalized:
                self.office_check(results,state,sess)

        # TODO ask for CountItemStatus for datafile (not used yet, as NIST CDF currently attaches it to ReportingUnit, yuck)
        cis_df = pd.read_sql_table('CountItemStatus',sess.bind,index_col='Id')
        cis_id,cis = ui.pick_one(cis_df,'Txt',item='status',required=True)

        # TODO how to handle Election?
        for element in ['ReportingUnit','Party']:
            # TODO: Rework, using fill_context_table
            print('Examining instances of {}'.format(element))
            # get list of columns of <f> needed to determine the raw_identifier for <element>
            p = '\<([^\>]+)\>'
            col_list = re.findall(p,self.cdf_tables.loc[element,'raw_identifier_formula'])

            # create dataframe of unique instances of <element>
            df_elts = results[col_list].drop_duplicates()

            # munge the given element into a new column of f_elts
            mr.add_munged_column(df_elts,self,element,'raw_identifier_value')

            # get any unmatched lines of f_elts
            unmatched = mu.find_unmatched(df_elts,element)

            # if some elements are unmatched:
            while unmatched.shape[0] > 0:
                # add blank column to be filled in
                unmatched.loc[:,'cdf_internal_name'] = ''
                # add cdf_element column
                unmatched.loc[:,'cdf_element'] = element
                unmatched_path = '{}unmatched_{}.txt'\
                    .format(self.path_to_munger_dir,element)

                # write unmatched lines to file and invite user to edit
                unmatched.to_csv(unmatched_path,sep='\t',index=None)
                print('\tACTION REQUIRED: fill the cdf_internal_name column in the file {}.'
                      .format(unmatched_path,element))
                input('\tEnter any key when work is complete.\n')

                # read user-edited file
                new_df_elts = pd.read_csv(unmatched_path,sep='\t')

                # restrict to lines with an internal name
                new_df_elts=new_df_elts[new_df_elts['cdf_internal_name'].notnull()]

                # add to raw_identifiers (both attribute of <self> and also the file in the munger directory)
                self.add_to_raw_identifiers(new_df_elts)

                if element != 'CandidateContest':
                    # add to state's context directory
                    # TODO what form should new_f_elts have?
                    if element == 'ReportingUnit':
                        new_df_elts.loc[:,'ReportingUnitType'] = self.atomic_reporting_unit_type
                        new_df_elts.loc[:,'CountItemStatus'] = cis  # TODO don't need this until it's uploaded to db

                    new_df_elts.rename(columns={'cdf_internal_name':'Name'},inplace=True)
                    state.add_to_context_dir(element,new_df_elts)

                # add to the cdf.<element> table
                mr.load_context_dframe_into_cdf(sess,new_df_elts,element,CDF_schema_def_dir='../CDF_schema_def_info/')

                if element == 'ReportingUnit':
                    # insert as necessary into ComposingReportingUnitJoin table
                    dbr.cruj_insert(state,new_df_elts)

                # see if anything remains to be matched
                unmatched = mu.find_unmatched(new_df_elts,element)
        # TODO
        if contest_type == 'BallotMeasure':
            print(f'WARNING: This munger assumes ballot measure style {self.ballot_measure_style}.')
            # TODO add description of ballot measure style option
            print('\tIf other behavior is desired, create or use another munger.')
            check_bms = input('\tProceed with munger {} (y/n)?\n'.format(self.name))
            if check_bms != 'y':
                print('Datafile will not be processed.')
                return

        return

    def add_to_raw_identifiers(self,df):
        """Adds rows in <df> to the raw_identifiers.txt file and to the attribute <self>.raw_identifiers"""
        for col in mu.raw_identifiers.columns:
            assert col in df.columns, 'Column {} is not found in the dataframe'.format(col)
        # restrict to columns needed, and in the right order
        df = df[mu.raw_identifiers.columns]
        # add rows to <self>.raw_identifiers
        self.raw_identifiers = pd.concat([self.raw_identifiers,df]).drop_duplicates()
        # update the external munger file
        self.raw_identifiers.to_csv(f'{self.path_to_munger_dir}raw_identifiers.txt',sep='\t',index=False)
        return

    def find_unmatched(self,f_elts,element):
        """find any instances of <element> in <f_elts> but not interpretable by <self>"""

        # identify instances that are not matched in the munger's raw_identifier table
        # limit to just the given element
        ri = self.raw_identifiers[self.raw_identifiers.cdf_element==element]

        # TODO prevent index column from getting into f_elts at next line
        f_elts = f_elts.merge(ri,on='raw_identifier_value',how='left',suffixes=['','_ri'])
        unmatched = f_elts[f_elts.cdf_internal_name.isnull()]
        unmatched = unmatched.drop(['cdf_internal_name'],axis=1)
        unmatched=unmatched.sort_values('raw_identifier_value')
        # unmatched.rename(columns={'{}_raw'.format(element):'raw_identifier_value'},inplace=True)
        return unmatched

    def __init__(self,dir_path,cdf_schema_def_dir='CDF_schema_def_info/'):
        assert os.path.isdir(dir_path),f'{dir_path} is not a directory'
        for ff in ['cdf_tables.txt','atomic_reporting_unit_type.txt','count_columns.txt']:
            assert os.path.isfile(os.path.join(dir_path,ff)),\
                f'Directory {dir_path} does not contain file {ff}'
        self.name=dir_path.split('/')[-1]    # e.g., 'nc_general'

        if dir_path[-1] != '/': # TODO use os.path.join everywhere to get rid of this
            dir_path += '/'  # make sure path ends in a slash
        self.path_to_munger_dir=dir_path

        # read raw_identifiers file into a table
        # note no natural index column
        self.raw_identifiers=pd.read_csv(os.path.join(dir_path,'raw_identifiers.txt'),sep='\t')

        # define dictionary to change any column names that match internal CDF names
        col_d = {t:f'{t}_{self.name}'
                 for t in os.listdir(os.path.join(cdf_schema_def_dir,'Tables'))}
        self.rename_column_dictionary=col_d

        # read raw columns from file (renaming if necessary)
        self.raw_columns = pd.read_csv(os.path.join(dir_path,'raw_columns.txt'),sep='\t').replace({'name':col_d})

        # read cdf tables and rename in ExternalIdentifiers col if necessary
        cdft = pd.read_csv(os.path.join(dir_path,'cdf_tables.txt'),sep='\t',index_col='cdf_element')  # note index
        for k in col_d.keys():
            cdft['raw_identifier_formula'] = cdft['raw_identifier_formula'].str.replace(
                '\<{}\>'.format(k),'<{}>'.format(col_d[k]))
        self.cdf_tables = cdft

        # determine how to treat ballot measures (ballot_measure_style)
        with open(os.path.join(dir_path,'ballot_measure_style.txt'),'r') as f:
            self.ballot_measure_style=f.read().strip()

        # determine whether the file has columns for counts by vote types, or just totals
        count_columns=pd.read_csv(os.path.join(dir_path,'count_columns.txt'),sep='\t').replace({'RawName':col_d})
        self.count_columns=count_columns
        if list(count_columns['CountItemType'].unique()) == ['total']:
            self.totals_only=True
        else:
            self.totals_only=False

        if self.ballot_measure_style == 'yes_and_no_are_candidates':
            # TODO read ballot_measure_selection_list from raw_identifiers.txt
            ri_df = pd.read_csv(os.path.join(dir_path,'raw_identifiers.txt'),sep='\t')
            self.ballot_measure_selection_list = ri_df[ri_df.cdf_element=='BallotMeasureSelection'].loc[:,'raw_identifier_value'].to_list()
            #with open(os.path.join(dir_path,'ballot_measure_selections.txt'),'r') as ff:
                #selection_list = ff.readlines()
            #self.ballot_measure_selection_list = [x.strip() for x in selection_list]

            bms_str=cdft.loc['BallotMeasureSelection','raw_identifier_formula']
            # note: bms_str will start and end with <>
            self.ballot_measure_selection_col = bms_str[1:-1]
        else:
            self.ballot_measure_selection_list=None  # TODO is that necessary?

        with open(os.path.join(dir_path,'atomic_reporting_unit_type.txt'),'r') as ff:
            self.atomic_reporting_unit_type = ff.readline()


if __name__ == '__main__':
    # get absolute path to local_data directory
    current_dir=os.getcwd()
    path_to_src_dir=current_dir.split('/election_anomaly/')[0]

    s = State('NC',f'{path_to_src_dir}/local_data/')
    mu = Munger('../../mungers/nc_primary/',cdf_schema_def_dir='../CDF_schema_def_info/')
    f = pd.read_csv('../../local_data/NC/data/2020p_asof_20200305/nc_primary/results_pct_20200303.txt',sep='\t')

    # initialize main session for connecting to db
    eng, meta_generic = dbr.sql_alchemy_connect(db_name=s.short_name)
    Session = sessionmaker(bind=eng)
    session = Session()

    mu.check_new_results_dataset(f,s,session)

    print('Done (states_and_files)!')
