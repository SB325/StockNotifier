import psycopg2
from pypika import PostgreSQLQuery # Table #,Schema, Table #, #Functions #, Field #pypika cannot create or delete tables
import numpy as np
import platform
#from math import math

class postgres_io:
    def __init__(self):
        self.on_remote = 'Linux' in platform.system()
        self.start_connection(self.on_remote)
        
    def __del__(self):
        self.connection.close()
    
    def start_connection(self,on_remote):
        if on_remote:
            database_endpoint = "market-db-1.cqntsr6agzce.us-east-1.rds.amazonaws.com"
            self.connection = psycopg2.connect(database="postgres", user="postgres", password="b3y0ndth3pal3#",host=database_endpoint, port="5432")
        else:
            self.connection = psycopg2.connect(database="postgres", user="postgres", password="b3y0ndth3pal3#",host="127.0.0.1", port="5432")
        print("Database opened successfully")
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()
        
    def view_table_names(self,tablesuffix=''):
        if len(tablesuffix):
            self.cursor.execute('SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE table_name like \'' + tablesuffix + '%\'' )
        else:
            self.cursor.execute('SELECT * FROM INFORMATION_SCHEMA.TABLES ')

        tn = []
        for tname in self.cursor.fetchall(): 
            tn.append((tname[2]))
        return tn
        
    def view_columns(self,tablename):
        self.cursor.execute('SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = \'' + tablename + '\'')
        cols = self.cursor.fetchall()
        colout = []
        for cname in cols:
            colout.append(cname[0])
        return colout

    def get_nrows(self,tablename):
        self.cursor.execute('SELECT count(*) from ' + tablename )
        nrows = self.cursor.fetchall()
        nrows = nrows[0][0]
        return nrows
    
    def get_number_of_repeated_rows(self,tablename, ticker):
        self.cursor.execute('SELECT count(*) occurrences FROM ' + tablename + \
                    ' where ticker = \'' + ticker + '\' group by ' + \
                    'posixtime_ms having count(*) > 1')
        nrows = self.cursor.fetchall()
        return len([i[0] for i in nrows if i[0]>1])
    
    def get_entire_column(self, tablename, column):
        # select column from tablename  
        self.cursor.execute('SELECT ' + column + ' FROM ' + tablename)
        data = self.cursor.fetchall()
        dataout = [n[0].strip() for n in data]
        return dataout
    
    def get_from_multi_filter(self, tablename, columns, vals):
        # each element of column list pertains to a different filter
        # the filter type: "min/max" or "in" filter determined by vals list
        # if type(vals[:]) = int or float, use min/max filter
        # if type(vals[:]) = string, use "in" matching filter
        colnames = self.view_columns(tablename)     #from existing table
        qstr = 'SELECT * from ' + tablename + ' where '  
        nfilters = len(vals[0])
        for cnt, n in enumerate(vals):
            if (type(n[0])==float) or (type(n[0])==int):
                print(columns[cnt])
                assert(len(n)==2), 'sublist must be 2 for numeric type.'
                assert(n[0] < n[1]), 'second value must be greater than first.'
                qstr = qstr + columns[cnt][0] + ' gt ' + n[0] + \
                    columns[cnt][0] + ' lt ' + n[1] 
            elif (type(n[0])==str):
                print(n)
                qstr = qstr + ','.join(columns[0]) + ' IN (\'' + \
                '\',\''.join(n) + '\') '
        
        qstr = qstr[:-1]
        return self.evaluate_query_get(qstr, tablename)
    
    def custom_query(self, tablename, columns_out, *args): #querystr):
        qstr = 'SELECT ' + columns_out + ' from ' + tablename
        if args:
            args=args[0]
            for n in args:
                qstr = qstr + ' ' + n
        print(qstr)
        self.cursor.execute( qstr )
        return self.cursor.fetchall()
            
    def get_max_value(self,table,column):
        self.cursor.execute('SELECT MAX(' + column + ') FROM ' + table )
        return self.cursor.fetchall()[0][0]
        
    def get_min_value(self,table,column):
        self.cursor.execute('SELECT MIN(' + column + ') FROM ' + table )
        return self.cursor.fetchall()[0][0]
    
    def get_max_value_given_eq_constr(self,table, maxcolumn, column, val):
        self.cursor.execute('SELECT MAX(' + maxcolumn + ') FROM ' + table + \
                            ' WHERE ' + column + '=\'' + val + '\'')
        val = self.cursor.fetchall()[0][0]
        return val
    
    def get_values_gt_val_given_ticker(self,table, selcolumn, column, column2, val, val2):
        self.cursor.execute('SELECT ' + selcolumn + ' FROM ' + table + \
                            ' WHERE ' + column + ' >= \'' + val + '\' and ' + \
                            column2 + ' = ' + val2 )
        outp = self.cursor.fetchall()
        if outp:
            outp = [i[0] for i in outp]

        return outp
    
    def get_values_eq_val_given_ticker(self,table, selcolumn, column, val):
        self.cursor.execute('SELECT ' + selcolumn + ' FROM ' + table + \
                            ' WHERE ' + column + ' = \'' + val + '\'')
        outp = self.cursor.fetchall()
        if outp:
            outp = [i[0] for i in outp]
        else:
            outp = outp[0]
        return outp
    
    def evaluate_query_get(self,s,t):
        #if not 'SELECT' in s:
        #    s = eval(s)
        #    print(s.get_sql())
        #    self.cursor.execute(s.get_sql())
        #else:
        print(f"Query:\n{s}")
        self.cursor.execute(s)
        return self.cursor.fetchall()
    
    def evaluate_query_set(self,sqlstr):
        s = eval(sqlstr)
        self.cursor.execute(s.get_sql())
        return self.cursor.fetchall()
    
    def get_range_query_str(self,min,max):
        # downselect values in column for values between min and max
        return '[' + str(min) + ':' + str(max) + ']'
    
    def replace_cell(self, tablename, col, row, rowval, val):
        sqlstr = 'UPDATE ' + tablename + \
        ' SET ' + col + ' = ' + val + ' WHERE ' + row + \
            ' = ' + rowval + ';'
        self.cursor.execute(sqlstr)
        
    def enter_data_into_table(self, tablename, columns, data):
        # tablename - single string
        # columns   - [1 x n] list of strings
        # data      - [1 x m x n] list of lists. Each of n strings must match 
        #   types from corresponding Table(tablename)

        try:
            print('Entering data into ' + tablename )
            #print('Entering (' + ', '.join(columns) + ') data into ' + tablename )
        except (AttributeError, TypeError):
            raise AssertionError('tablename should be a string')

        origrows = self.get_max_value(tablename,'key_')  # number of rows in existing table
        if not origrows:
            origrows = 0
        x = np.array(data)
        if len(np.shape(x))==1:
            nrows = 1
        else:
            nrows = np.shape(x)[0]             # number of rows in input data

        columns.insert(0,'KEY_')            # append PRIMARY KEY column (needed for all tables)
        keyappend = [i+1 for i in range(origrows, nrows+origrows)]
            
        # append incremental primary key to each row of input data lists
        if nrows > 1:
            for cnt, n in enumerate(data):
                data[cnt].insert(0,keyappend[cnt])
        else:
            #data = data[0]
            if type(data[0])==list:
                data = data[0]
                
            data.insert(0,keyappend[0])
        
        # for dynamic insertion of m lists of data, use eval() function

        insertstr = ''
        if nrows == 1:
            data = tuple(data)
            insertstr = 'data,'
        else:
            for intt, row in enumerate(data):
                data[intt] = tuple(row)
                insertstr = insertstr + 'data[' + str(intt) + '],'
        #print(data)    
        pref = 'PostgreSQLQuery.into(tablename).insert('
        insertstr = insertstr[:-1]
        q = eval(pref + insertstr + ')')
        #print(q.get_sql())
        self.cursor.execute(q.get_sql()) 
        self.commit_table()

    def remove_repeated_rows(self,tablename):
        # In case entered data is repeated, remove repeats from table
        querystart = 'DELETE FROM ' + tablename + ' a USING ' + tablename + ' b ' + \
                        'WHERE a.key_ < b.key_ '
        if tablename=='funddata_mktd':                
            self.cursor.execute(querystart + \
                        'AND a.ticker = b.ticker ' + \
                        'AND a.cusip = b.cusip ' + \
                        'AND a.description = b.description ' + \
                        'AND a.low52 = b.low52')
                
        elif tablename=='techdata_mktd':
            self.cursor.execute(querystart + \
                        'AND a.ticker = b.ticker ' + \
                        'AND a.open = b.open ' + \
                        'AND a.close = b.close ' + \
                        'AND a.high = b.high ' + \
                        'AND a.low = b.low')
    
        elif tablename=='news_mktd':
            self.cursor.execute(querystart + \
                        'AND a.Id = b.Id ' + \
                        'AND a.ticker = b.ticker ' + \
                        'AND a.author = b.author ' + \
                        'AND a.title = b.title ' + \
                        'AND a.url = b.url')
                
        elif tablename=='model_output_mktd':
            self.cursor.execute(querystart + \
                        'AND a.ticker = b.ticker ' + \
                        'AND a.posixtime_ms = b.posixtime_ms ' + \
                        'AND a.fiveday = b.fiveday')
        
        elif tablename=='real_time_news_data':
            self.cursor.execute(querystart + \
                        'AND a.Time = b.Time ' + \
                        'AND a.Headline = b.Headline ' + \
                        'AND a.Ticker = b.Ticker')
        
        # Reassign key_ column so that it goes from 1 to num_rows
        #keyvals = str(tuple([i for i in range(1,self.get_nrows(tablename))]))
        #keyvals = keyvals[1:]
        #keyvals = keyvals[:-1]
        
    def resequence_table(self, tablename, key):
        self.cursor.execute('DROP SEQUENCE IF EXISTS keyvals')
        self.cursor.execute('CREATE SEQUENCE keyvals START 1')
        self.cursor.execute('UPDATE ' + tablename + ' SET ' + key + ' = setval(\'keyvals\',1)' ) #'ORDER BY ' + colselect )
        self.commit_table()
        
    def create_table(self,tablename, columnames, types, nullflags):
        # ensure that each column has a sample data value. type will be inferred from that
        try:
            print('Creating table (' + tablename + ') with columns')
        except (AttributeError, TypeError):
            raise AssertionError('tablename and columnnames should be strings')
        
        assert (len(columnames) == len(types)), 'each column must have a type!'
            
        t = []
        for n in types:
            if type(n)==float:
                t.append('DOUBLE PRECISION')
            elif type(n)==str:
                if len(n)<2:
                    t.append('CHAR(100)')
                elif len(n)==2:
                    t.append('CHAR(1000)')
                elif len(n)==3:
                    t.append('CHAR(10000)')
            elif type(n)==int:
                if n<(2**31):
                    t.append('INT')
                else:
                    t.append('BIGINT')
        
        v = []
        for n in nullflags:
            if n==False:
                v.append('')
            elif n==True:
                v.append('NOT NULL')
        
        try:
            querythread = 'CREATE TABLE ' + tablename + '(' + \
                'KEY_ INT PRIMARY KEY NOT NULL, '
            for idx, val in enumerate(columnames):
                querythread = querythread + ' ' + columnames[idx] + ' ' + t[idx] + ' ' + v[idx] + ','
            querythread = querythread[:-1] + ')'
            print(querythread)

            self.cursor.execute(querythread)
            self.commit_table()
        except (AttributeError, TypeError):
            raise AssertionError('Table entry failed.')
        
        print('Table (' + tablename + ') created successfully!')

    def trim_trailing_whitespace(self, tablename, column):
        # trim trailing whitespace from column data of type STRING
        str = 'UPDATE ' + tablename + ' SET ' + column + \
        ' = RTRIM ( SELECT ticker FROM ' + tablename + ')'
        print(str)
        self.cursor.execute(str)
        print(f"Removed Trailing whitespace from columns {column} in table {tablename}")
        
    def clear_table(self,tablename):
        # don't use this function unless absolutely necessary
        self.cursor.execute('TRUNCATE TABLE ' + tablename )
        print('Cleared all rows of table ' + tablename )
        
    def copy_table(self,tablename, copyname):
        self.cursor.execute('CREATE TABLE ' + copyname + ' as (SELECT * FROM ' + tablename + ')')
        print('Created table ' + copyname + ' as copy of table ' + tablename )
        
    def commit_table(self):
        self.connection.commit()
        print("Table Committed")

    def close_connection(self):
        self.connection.close()
        print("Database connection closed.")
