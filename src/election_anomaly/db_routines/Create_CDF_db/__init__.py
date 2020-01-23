#!/usr/bin/python3
# under construction
# db_routines/Create_CDF_db/__init__.py
# TODO may need to add "NOT NULL" requirements per CDF

import db_routines as dbr
import sqlalchemy
from db_routines import create_schema
from sqlalchemy import MetaData, Table, Column,CheckConstraint,UniqueConstraint,Integer,String,Date,ForeignKey
# NB: imports above are used within string argument to exec()
from sqlalchemy.orm import sessionmaker
import os


def create_common_data_format_schema(session, schema, e_table_list, dirpath='CDF_schema_def_info/'):
    """ schema example: 'cdf'; Creates cdf tables in the given schema
    e_table_list is a list of enumeration tables for the CDF, e.g., ['ReportingUnitType','CountItemType', ... ]
    """
    create_schema(session, schema)
    eng = session.bind
    metadata = MetaData(bind=eng,schema=schema)

    #%% create the single sequence for all db ids
    id_seq = sqlalchemy.Sequence('id_seq', metadata=metadata,schema=schema)

    #%% create enumeration tables and push to db
    print('Creating enumeration tables')
    for t in e_table_list:
        print('\t'+t)
        exec('Table(\'' + t + '\',metadata, Column(\'Id\',Integer, id_seq,server_default=id_seq.next_value(),primary_key=True), Column(\'Txt\',String),schema = \'' + schema + '\')')
    metadata.create_all()

    #%% create all other tables, in set order because of foreign keys
    fpath = dirpath + 'tables.txt'
    print('Creating other tables, from ' + fpath + ':')
    with open(fpath, 'r') as f:
        table_def_list = eval(f.read())
    for table_def in table_def_list:
        name = table_def[0]
        field_d = table_def[1]
        print('\t'+ name)
        col_string_list = ['Column(\''+ f['fieldname'] + '\',' + f['datatype'] + ')' for f in field_d['fields']] + ['Column(\'' + e + '_Id\',ForeignKey(\'' + schema + '.' + e + '.Id\')),Column(\'Other' + e + '\',String)' for e in field_d['enumerations']] + ['Column(\'' + oer['fieldname'] + '\',ForeignKey(\'' + schema + '.' + oer['refers_to'] + '.Id\'))' for oer in field_d['other_element_refs']] + ['CheckConstraint(\'"' + nnf + '" IS NOT NULL\',name = \'' + field_d['short_name'] + '_' + nnf + '_not_null\' )' for nnf in field_d['not_null_fields']] + ['UniqueConstraint(' + ','.join(['\'' + x +'\'' for x in uc]) + ',name=\'' + field_d['short_name'] + '_ux' + str(field_d['unique_constraints'].index(uc)) + '\')' for uc in field_d['unique_constraints']]
        table_creation_string = 'Table(\''+ name + '\',metadata,Column(\'Id\',Integer,id_seq,server_default=id_seq.next_value(),primary_key=True),' + ','.join(col_string_list) + ', schema=\'' + schema + '\')'
        exec(table_creation_string)
        metadata.create_all()
    return metadata

# TODO should we somewhere check consistency of enumeration_table_list and the files in enumerations/ ? Is the file enumeration_table_list ever used?
def enum_table_list(dirpath= 'CDF_schema_def_info/'):
    if not dirpath[-1] == '/': dirpath += '\''
    file_list = os.listdir(dirpath + 'enumerations/')
    for f in file_list:
        assert f[-4:] == '.txt', 'File name in ' + dirpath + 'enumerations/ not in expected form: ' + f
    enum_table_list = [f[:-4] for f in file_list]
    list_file = dirpath + 'enumeration_table_list'
    if os.path.isfile(list_file): os.remove(list_file)
    with open(list_file,'a') as out_f:
        for t in enum_table_list: out_f.write(t)
    return enum_table_list

def fill_cdf_enum_tables(session,meta,e_table_list,dirpath= 'CDF_schema_def_info/'):
    """takes lines of text from file and inserts each line into the txt field of the enumeration table"""
    if not dirpath[-1] == '/': dirpath += '\''
    for f in e_table_list:
        table = meta.tables[meta.schema + '.' + f]
        print(table.key)
        with open(dirpath + 'enumerations/' + f + '.txt', 'r') as f:
            entries = f.read().splitlines()
        for entry in entries:
            ins = table.insert().values(Txt=entry)
            session.execute(ins)
    session.commit()
    return

if __name__ == '__main__':
    eng,meta = dbr.sql_alchemy_connect(paramfile='../../../local_data/database.ini')
    Session = sessionmaker(bind=eng)
    session = Session()

    schema='test'
    e_table_list = enum_table_list(dirpath = '../../CDF_schema_def_info/')
    metadata = create_common_data_format_schema(session, schema, e_table_list, dirpath ='../../CDF_schema_def_info/')
    fill_cdf_enum_tables(session,metadata,e_table_list,dirpath='../../CDF_schema_def_info/')
    print ('Done!')

    eng.dispose()