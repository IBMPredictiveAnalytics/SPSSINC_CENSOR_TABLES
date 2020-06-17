# extension command implementation for SPSSINC CENSOR TABLES command
#/***********************************************************************
# * Licensed Materials - Property of IBM 
# *
# * IBM SPSS Products: Statistics Common
# *
# * (C) Copyright IBM Corp. 1989, 2020
# *
# * US Government Users Restricted Rights - Use, duplication or disclosure
# * restricted by GSA ADP Schedule Contract with IBM Corp. 
# ************************************************************************/


__author__ = "SPSS, JKP"
__version__ = "1.3.0"

# history
# 21-dec-2009 enable translation
# 13-dec-2012 suppress caption if no censoring was done.
# 29-sep-2014 add PROCESS keyword
#try:
    #import wingdbstub
    #if wingdbstub.debugger != None:
        #import time
        #wingdbstub.debugger.StopDebug()
        #time.sleep(2)
        #wingdbstub.debugger.StartDebug()
    #import thread
    #wingdbstub.debugger.SetDebugThreads({thread.get_ident(): 1}, default_policy=0)
    ## for V19 use
    ##    ###SpssClient._heartBeat(False)
#except:
    #pass    

import spss
if not int(spss.GetDefaultPlugInVersion()[4:6]) >= 17:
    # Do not translate: translation function will not be defined at this point
    raise ImportError("This module requires at least SPSS Statistics 17")
import SpssClient, sys, time, re, locale, operator
from extension import floatex
from spssaux import GetSPSSVersion
spssver = [int(i) for i in GetSPSSVersion().split('.')]
spssverLt1702 = spssver[:-1] < [17,0,2]
spssverLe1702 = spssver[:-1] <= [17,0,2]

from extension import Template, Syntax, processcmd


# Do not translate


# Additional examples using the function.
#Example: censorLatest
#This example blanks out the means for all cells with a count value < 100.  See the function help for other censoring options.
#cmd='ctables   /TABLE origin BY accel [MEAN, COUNT]'
#rc=tables17.censorLatest(critvalue=100, desout=desout, neighborlist=[-1], direction='row')

#Example: blank out insignificant correlations from CORRELATIONS.
# Uses car_sales.sav

#CORRELATIONS
  #/VARIABLES=fuel_cap horsepow length lnsales mpg price
  #/PRINT=TWOTAIL NOSIG
  #/MISSING=PAIRWISE.

#SPSSINC CENSOR TABLES
#CRITLABEL="Sig. (2-tailed)" TESTTYPE=">" CRITVALUE=.05
#DIRECTION=COLUMN NEIGHBORS=-1 1
#SUBTYPE="'Correlations'"
#/OPTIONS HIDECRITFIELD 
#SYMBOL=" ".

def Run(args):
    """Execute the SPSS CENSOR TABLES command"""
    args = args[list(args.keys())[0]]
    ###print args   #debug

    oobj = Syntax([
        Template("COMMAND", subc="",  ktype="literal", var="cmd", islist=True),
        Template("SUBTYPE", subc="", ktype="str", var="subtype", islist=False),
        Template("CRITLABEL", subc="", ktype="literal", var="critfield"),
        Template("CRITVALUE", subc="", ktype="float", var="critvalue"),
        Template("NEIGHBORS", subc="", ktype="int", var="neighborlist", islist=True),
        Template("DIRECTION", subc="", ktype="str", var="direction"),
        Template("TESTTYPE", subc="",  ktype="str", var="testtype"),
        Template("PROCESS", subc="", ktype="str", var="process",
            vallist=["preceding", "all"]),
        
        Template("HIDECRITFIELD", subc="OPTIONS", ktype="bool", var="hidecrit"),
        Template("APPENDCAPTION", subc="OPTIONS", ktype="bool", var="appendcaption"),
        Template("CAPTION", subc="OPTIONS", ktype="literal", var="othercaption"),
        Template("CONDITIONALCAPTION", subc="OPTIONS", ktype="bool", var="conditionalcaption"),
        Template("SYMBOL", subc="OPTIONS", ktype="literal", var="symbol"),
        Template("HELP", subc="", ktype="bool")])

    # ensure localization function is defined
    global _
    try:
        _("---")
    except:
        def _(msg):
            return msg

    # A HELP subcommand overrides all else
    if "HELP" in args:
        #print helptext
        helper()
    else:
        processcmd(oobj, args, censorLatest)

def helper():
    """open html help in default browser window
    
    The location is computed from the current module name"""
    
    import webbrowser, os.path
    
    path = os.path.splitext(__file__)[0]
    helpspec = "file://" + path + os.path.sep + \
         "markdown.html"
    
    # webbrowser.open seems not to work well
    browser = webbrowser.get()
    if not browser.open_new(helpspec):
        print(("Help file not found:" + helpspec))
try:    #override
    from extension import helper
except:
    pass
def censorLatest(cmd=None, desout=None, critfield='Count', 
        subtype=None, process="preceding",
        critvalue=5, symbol=" ",  neighborlist=[1], direction='row', testtype="<", appendcaption=True,
        othercaption=None, hidecrit=False, conditionalcaption=True):
    """Run the command(s), cmd and censor specified cells based on criterion and return the number of cells censored.

    If cmd is empty or not supplied, it is not run, and the requisite tables should already exist.
    if tablenum is specified, it is the absolute table number to process.
    Otherwise, the most recent table is used.
    If subtype is specified, the most recent table with that OMS subtype is used.  If
    subtype has a redundant pair of outer quotes as would be produced from Copy OMS Subtype,
    they are ignored.
    Set appendtitle and appendcaption to False to suppress the corresponding append.
    desout can be specified as the handle to the designated Viewer.  If None, this module will find it.

    critfield specifies the leaf text of the cell to use for the criterion value.
    critvalue is the threshold value.  The absolute value of a cell is tested against the criterion value.
    neighborlist is a list of relative positions that should be censored.  Positive to the right/above,
    negative to the left/below.  In order to censor the criterion field itself, include 0 in neighborlist
    direction is 'row' for items in the same row or 'column' for items in the same column.
    The label is expected in the dimension opposite to direction.
    symbol is the value that should replace a censored field, defaulting to blank.
    hidecrit if True causes the criterion row or column to be hidden.

    Note that censoring a field may still leave its value discoverable if it is included in a total.

    Example: censor statistics in  a table when counts are small:
    cmd="CTABLES /TABLE origin BY accel [MEAN, COUNT]  /SLABELS POSITION=ROW."
    rc= tables17.censorLatest(critvalue=10, desout=desout, neighborlist=[-1], direction='column')

    Example: blank out insignificant correlations in the output from CORRELATIONS:
    cmd=r"CORRELATIONS  /VARIABLES=availblt avg_purc chckout"
    tables17.censorLatest(cmd=cmd, critvalue=.01, critfield="Sig. (2-tailed)", 
        testtype=">", neighborlist=[0,1,-1], direction='column')

    """
    # debugging
    # makes debug apply only to the current thread
    #try:
        #import wingdbstub
        #if wingdbstub.debugger != None:
            #import time
            #wingdbstub.debugger.StopDebug()
            #time.sleep(2)
            #wingdbstub.debugger.StartDebug()
        #import thread
        #wingdbstub.debugger.SetDebugThreads({thread.get_ident(): 1}, default_policy=0)
        ## for V19 use
        ##    ###SpssClient._heartBeat(False)
    #except:
        #pass    
    encoding = locale.getlocale()[1]
    if not isinstance(critfield, str):
        critfield = str(critfield, encoding)
    failed = True
    if subtype:
        subtype = "".join(subtype.lower().split())
        subtype = re.sub(r"""(['"])(.*)\1""",r"\2", subtype)
    if cmd:
        spss.Submit(cmd)

    try:
        time.sleep(1.0)
        SpssClient.StartClient()
        if desout is None:
            desout= SpssClient.GetDesignatedOutputDoc()

        if spssverLe1702:
            spss.Submit("_SYNC.")
        items = desout.GetOutputItems()
        itemkt = items.Size() - 1
        tablenumbers = []
        while itemkt >= 0:
            item = items.GetItemAt(itemkt)
            if item.GetType() == SpssClient.OutputItemType.PIVOT:
                if subtype is None or subtype == "".join(item.GetSubType().lower().split()):
                    tablenumbers.append(itemkt)
                    if process == "preceding":
                        break
            itemkt-= 1
        if not tablenumbers:
            raise ValueError(_("No table found to process."))

        for tablenum in tablenumbers:
            censorkt = tcensor(items, tablenum, critfield, critvalue, symbol, neighborlist, direction, testtype,
                appendcaption=appendcaption, othercaption=othercaption, hidecrit=hidecrit, 
                conditionalcaption=conditionalcaption)
    finally:
        SpssClient.StopClient()


def tcensor(objItems, main, critfield='Count', 
            critvalue=5, symbol="", neighborlist=[1], direction='row', testtype='<',
            appendcaption=True,othercaption=None, hidecrit=False, conditionalcaption=True):
    """censor the cells of table main in designated Viewer window."""

    ###objItems = desviewer.GetOutputItems()
    main = objItems.GetItemAt(main)
    if main.GetType() != SpssClient.OutputItemType.PIVOT:
        raise ValueError(_("A specified item is not a pivot table or does not exist."))

    # create criterion function
    try:
        ttype = ['<', '<=','=','==','>','>=','!=', '~='].index(testtype)
        if ttype == 0:
            olist = [True, False, False]
        elif ttype == 1:
            olist = [True, True, False]
        elif ttype == 2 or ttype == 3:
            olist = [False, True, False]
        elif ttype == 4:
            olist = [False, False, True]
        elif ttype == 5:
            olist = [False, True, True]
        elif ttype == 6 or olist == 7:
            olist = [True, False, True]
    except:
        raise ValueError(_("Invalid comparison type: ") + testtype)

    def crittest(value):
        """return whether value meets the criterion test.

        Tries to handle locale formatted and decorated strings via floatex function"""

        try:
            c = operator.eq(abs(floatex(value)), critvalue)
            return olist[c+1]
        except:
            return False

    try:
        PivotTable = main.GetSpecificType()
    except:
        time.sleep(.5)
        PivotTable = main.GetSpecificType()  # give it another chance
    censorkt = 0
    try:
        PivotTable.SetUpdateScreen(False)
        if direction == 'row':
            lblarray = PivotTable.ColumnLabelArray()
        elif direction == 'column':
            lblarray = PivotTable.RowLabelArray()			
        else:
            raise ValueError(_("direction must be 'row' or 'column'"))
        censorkt = censortbl(lblarray, PivotTable, critfield, crittest, symbol, 
                             neighborlist, direction, hidecrit, conditionalcaption)
        if appendcaption and (not conditionalcaption or (conditionalcaption and censorkt > 0)):
            if othercaption is None:
                othercaption = _("Censoring criterion: %s.  Number of values censored: %s") % (critfield, str(censorkt))
            PivotTable.SetCaptionText(PivotTable.GetCaptionText() + "\n" + othercaption)
        PivotTable.Autofit()
    finally:
        PivotTable.SetUpdateScreen(True)
        return censorkt

def censortbl(labels, PivotTable, critfield, crittest, symbol, neighborlist, direction, hidecrit, conditionalcaption):
    """Censor the table, returning the number of values censored.

    labels is the row or column label array where the critfield should be found.
    PivotTable is the table to process.
    crittest is a test function to be used for the comparison.
    symbol is the symbol used to replace the value.
    neighborlist is the list of neighboring cells in which to do the replacement when the test succeeds
    direction is row or col, which determines how to interpret neighborlist.
    hidecrit if True causes the criterion row or column to be hidden."""

    # an empty symbol can cause the DataCellArray to collapse
    if symbol == '':
        symbol = ' '
    try:
        datacells = PivotTable.DataCellArray()
        rows = direction == 'row'
        if rows:
            dimsize = datacells.GetNumColumns()
            otherdimsize = datacells.GetNumRows()
            lbllimit = labels.GetNumRows() - 1
        else:
            dimsize = datacells.GetNumRows()
            otherdimsize = datacells.GetNumColumns()
            lbllimit = labels.GetNumColumns() - 1
        censorkt = 0
        foundcritfield = False
        c = LayerManager(PivotTable)
        for facenumber, face in enumerate(c.layers()):
            for i in range(dimsize):
                a1, a2 = _sargs(rows, lbllimit, i)
                if labels.GetValueAt(a1, a2)  == critfield:
                    foundcritfield = True
                    for other in range(otherdimsize):
                        aa1, aa2 = _sargs(rows, other, i)
                        if crittest(datacells.GetValueAt(aa1, aa2)):
                            for offset in neighborlist:
                                if 0 <= i+ offset < dimsize:
                                    aaa1, aaa2 = _sargs(rows, other, i + offset)
                                    datacells.SetValueAt(aaa1, aaa2, symbol)
                                    datacells.SetHAlignAt(aaa1, aaa2, SpssClient.SpssHAlignTypes.SpssHAlRight)  # right align cell
                                    censorkt += 1
                    if hidecrit and facenumber == 0:   # only need to hide once for all the layers
                        hide(labels, rows, i, lbllimit)
    except AttributeError as e:
        raise SystemError(_("Error in censortbl: %s") % e.args[0])
    if not foundcritfield:
        raise AttributeError(_("The criterion field was not found in the table: %s") % critfield)

    return censorkt

def hide(array, rows, i, lastdim):
    """Hide the data and labels at i.
    array is the array of row or column labels.
    i is the row or column number to hide.
    lastdim is the index of the innermost label row or column."""

    #collblarray = PivotTable.columnlabelarray()
    #lblnumrows = collblarray.numrows
    x, y = _sargs(rows, lastdim, i)
    array.HideLabelsWithDataAt(x, y)

def _sargs(row,x,y):
    """ return x, y, if row == True else y,x"""
    if row:
        return (x,y)
    else:
        return (y,x)

class LayerManager(object):
    def __init__(self, pt):
        """pt is an activated pivot table"""
        self.ptmgr = pt.PivotManager()
        self.numlayerdims = self.ptmgr.GetNumLayerDimensions()
        self. layercats = []
        self.layercurrcat = []
        for c in range(self.numlayerdims):
            self.layercats.append(self.ptmgr.GetLayerDimension(c).GetNumCategories())
            self.layercurrcat.append(self.ptmgr.GetLayerDimension(c).GetCurrentCategory())

    def layers(self):
        """Generator to iterate over all the categories of all the dimensions in the layer.

        Returns the current category number, but the main purpose is to change the current category."""

        if self.numlayerdims == 0:
            yield 0
        else:
            for ld in range(self.numlayerdims):
                cc = self.layercurrcat[ld]
                for c in range(self.layercats[ld]):
                    yield cc
                    cc = (cc+1) % self.layercats[ld]
                    self.ptmgr.LayerDimension(ld).SetCurrentCategory(cc)
