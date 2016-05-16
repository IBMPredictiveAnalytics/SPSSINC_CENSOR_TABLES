# SPSSINC CENSOR TABLES
## Censor cells of a pivot table based on the values of a test statistic
 Use this command to blank out or otherwise obscure cells in the most recent pivot table of a selected type based on the value of a specified statistic in the table. For example, you can blank out cell statistics based on small counts or blank out insignificant correlations in a correlation matrix.

---
Requirements
----
- IBM SPSS Statistics 18 or later and the corresponding IBM SPSS Statistics-Integration Plug-in for Python.

For users with IBM SPSS Statistics version 22 or higher, the SPSSINC CENSOR TABLES extension bundle is installed as part of IBM SPSS Statistics-Essentials for Python.

---
Installation intructions
----
1. Open IBM SPSS Statistics
2. Navigate to Utilities -> Extension Bundles -> Download and Install Extension Bundles
3. Search for the name of the extension and click Ok. Your extension will be available.

---
Tutorial
-----
Censor cells based on the contents of neighboring cells

SPSS CENSOR TABLES COMMAND = "*command syntax to execute*"  
CRITLABEL="*leaf label of criterion row or column*"  
CRITVALUE = *value to test for censoring*  
TESTTYPE= "*comparison operator to apply*"  
DIRECTION= ROW^&#42;&#42; or COLUMN  
NEIGHBORS = *list of column numbers to censor*  
SUBTYPE = "*OMS table subtype*"
PROCESS = *PREVIOUS^&#42;&#42; or ALL*

/OPTIONS HIDECRITFIELD APPENDCAPTION CAPTION SYMBOL

/HELP

^&#42; Required  
^&#42;&#42; Default

SPSSINC  CENSOR TABLES /HELP prints this help and does nothing else.

Example: blank out means based on small counts
```
SPSSINC CENSOR TABLES 
COMMAND="CTABLES /TABLE origin BY accel [MEAN, COUNT]  /SLABELS POSITION=ROW."
CRITLABEL="Count" CRITVALUE=25 NEIGHBORS=-1 DIRECTION=COLUMN, TESTTYPE="<"
/OPTIONS SYMBOL="*".
```

Example: blank out insignificant correlations from CORRELATIONS.
```
CORRELATIONS
/VARIABLES=fuel_cap horsepow length lnsales mpg price
/PRINT=TWOTAIL NOSIG
/MISSING=PAIRWISE.

SPSSINC CENSOR TABLES
CRITLABEL="Sig. (2-tailed)" TESTTYPE=">" CRITVALUE=.05
DIRECTION=COLUMN NEIGHBORS=-1 1
SUBTYPE="'Correlations'"
/OPTIONS HIDECRITFIELD 
SYMBOL=" ".
```


**COMMAND** is an optional command such as CTABLES to run before applying the censoring.
If it is long, it can be written as
```COMMAND = "part1"  "part2" ...```  (Note that the literals are NOT joined with +.)
If no command is specified, the most recent matching table is censored.

**CRITLABEL** is the innermost text of the row or column containing the statistic
to be used for censoring.  The default is "Count".  The text is case sensitive.

**CRITVALUE** is a number that is used for the test comparison.  It defaults to 5.

**TESTTYPE** specifies the type of comparison to use.  The absolute value of the
criterion cell is compared with the test type.  TESTTYPE must be a quoted string
that is one of <, <=, =, ==, !=, >, >=.  The default is "<".  The expression evaluated
is 
```
abs(cell value) testtype critvalue
```


**NEIGHBORS** is a list of one or more numbers indicating which rows or columns are
to be censored.  0 is the criterion cell itself; negative numbers are to the left or above;
positive numbers to the right or below.  -1, for example, is the cell immediately left or
above the criterion cell.  The default is 1.

**DIRECTION** can be ROW or COLUMN.  It determines how the NEIGHBORS numbers
are interpreted.  It defaults to ROW.

You can specify the table type to process
using **SUBTYPE**.  You can find the subtype by right clicking in the outline on an instance 
or from *Utilties/OMS* identifiers.  The subtype name should be in quotes.  
Case and white space do not matter.

**PROCESS** specifies what tables to process.  If a subtype was specified,
PROCESS applies within that set.  Specify PREVIOUS to process only the
last table or ALL to process all the tables in the set.

OPTIONS
-------
The OPTIONS subcommand provides control of the table appearance.

**HIDECRITFIELD** specifies that the entire row or column containing the criterion
statistics should be hidden.

By default, a caption is added to the table indicating the number of cells censored and
the censoring statistic.  **APPENDCAPTION**=NO suppresses the caption.

**CAPTION** = "text" specifies the text for the caption.

**SYMBOL**="text" specifies the text to replace the contents of a censored cell.  It
defaults to blank.

---
License
----

- Apache 2.0

Contributors
----

 - IBM SPSS
