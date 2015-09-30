import re

################################################################################################
# Functions used in the processing of dpmAsGraph                                               #
################################################################################################
def applyFilter(reports,repFilters):
    '''
    Filters the table versions array reports by applying the string filters in the filter array repFilters.
    The filters can contain wildchard symbols % (any number of characters) at any location of the filter.
    If a report matches any of the filters, it is included in the result set.
    Input: reports - array of report version codes
           repFilters - array of filter criteria with or without % symbols
    Output: set of reports (sub set of the input reports) which satisfy any of the filter criteria
    
    >>> filt = ["%11%","%.a","F%c"]
    >>> tbl = ["C 07.00.a", "C 11.00", "C 15.00", "F 08.00.a", "F 08.00.b"]
    >>> result = applyFilter(tbl,filt)
    >>> sorted([rpv for rpv in result])
    ['C 07.00.a', 'C 11.00', 'F 08.00.a']
    >>> filt = ["%11%","C 07.00.a"]
    >>> tbl = ["C 07.00.a", "C 11.00", "C 15.00", "F 08.00.a", "F 08.00.b"]
    >>> result = applyFilter(tbl,filt)
    >>> sorted([rpv for rpv in result])
    ['C 07.00.a', 'C 11.00']
    '''
    return {tblVer for filt in repFilters for tblVer in reports if re.match(str(filt).replace("%","(.*)"), tblVer)}

def distance(catk1, catk2):
    '''
    Determine the distance between both categorisation keys
    Common dimension member combinations do not impact the distance
    When a common dimension has a different member, this increases the distance with one
    Each dimension which is not common increases the distance with one
    So we count the distinct dimensions found in the union but not in the intersection
    of the dimension member combinations of the categorisation keys  
    
    >>> catk1 = 'ABC1234DEF5678GHI9012'
    >>> catk2 = 'ABC1234DEF5678GHI999'
    >>> distance(catk1, catk2)
    1
    >>> catk1 = 'ABC1234DEF5678GHI9012'
    >>> catk2 = 'ABC1234DEF5678III999'
    >>> distance(catk1, catk2)
    2
    >>> catk1 = 'ABC1234DEF5678GHI9012'
    >>> catk2 = 'ABC1234DEF5678GHI9012JKL99'
    >>> distance(catk1, catk2)
    1
    >>> catk1 = 'ABC1234DEF5678GHI9012JKL99'
    >>> catk2 = 'ABC1234DEF5678GHI999JKL99'
    >>> distance(catk1, catk2)
    1
    >>> catk1 = 'ABC1234DEF5678GHI9012'
    >>> catk2 = 'ABC1234DEF5678GHI999JKL99'
    >>> distance(catk1, catk2)
    2
    >>> catk1 = 'ABC888DEF5678GHI9012JKL99'
    >>> catk2 = 'ABC1234DEF5678GHI999JKL99'
    >>> distance(catk1, catk2)
    2
    >>> catk1 = 'ABC888DEF5678GHI9012JKL99'
    >>> catk2 = 'ABC1234EEE5678GHI999KKL99'
    >>> distance(catk1, catk2)
    6
    >>> catk1 = 'ABC888DEF5678GHI9012JKL99'
    >>> catk2 = 'ABC1234EEE5678GHI999HHH5678III666LLL777'
    >>> distance(catk1, catk2)
    8
    '''
    return len({re.findall(r'[A-Z]+',dimmem)[0] for dimmem in set(re.findall(r'[A-Z]+[0-9]+',catk1)).symmetric_difference(set(re.findall(r'[A-Z]+[0-9]+',catk2)))})

def decompose(catk1, catk2):
    '''
    From 2 categorisation keys obtain 3 categorisation keys. One containing the common dimension member combinations
    and the others containing those combinations which are unique to each of the respective categorisation keys.
    Input: catk1 and catk2 are datapointvid categorisation keys
    Output: the common dimenson members, the none common once of catk1 and the none common once of catk2 as categorisation keys
    Remark: a dimension member combination is only common if both the dimension and member values match
    
    >>> catk1 = 'ABC1234DEF5678GHI9012'
    >>> catk2 = 'ABC1234DEF5678GHI9099'
    >>> x, y, z = decompose(catk1, catk2)
    >>> x
    'ABC1234DEF5678'
    >>> y
    'GHI9012'
    >>> z
    'GHI9099'
    >>> catk1 = 'ABC1234DEF5678GHI9012'
    >>> catk2 = 'ABC1234DEF5678GHI9012UPD1111XYZ9099'
    >>> x, y, z = decompose(catk1, catk2)
    >>> x
    'ABC1234DEF5678GHI9012'
    >>> y
    ''
    >>> z
    'UPD1111XYZ9099'
    >>> catk1 = 'ABC1234DEF5678GHI9012'
    >>> catk2 = 'UPD1111XYZ9099'
    >>> x, y, z = decompose(catk1, catk2)
    >>> x
    ''
    >>> y
    'ABC1234DEF5678GHI9012'
    >>> z
    'UPD1111XYZ9099'
    '''
    dimmem1 = re.findall(r'[A-Z]+[0-9]+',catk1)
    dimmem2 = re.findall(r'[A-Z]+[0-9]+',catk2)
    cm = [dimmem for dimmem in dimmem1 if dimmem in dimmem2]
    r1 = [dimmem for dimmem in dimmem1 if not dimmem in dimmem2]
    r2 = [dimmem for dimmem in dimmem2 if not dimmem in dimmem1]
    return ''.join(cm), ''.join(r1), ''.join(r2)

def intersection(catk1, catk2):
    '''
    From 2 categorisation keys obtain the common dimension member combinations
    Input: catk1 and catk2 are datapointvid categorisation keys
    Output: the common dimenson members
    Remark: a dimension member combination is only common if both the dimension and member values match
    
    >>> catk1 = 'ABC1234DEF5678GHI9012'
    >>> catk2 = 'ABC5555DEF5678GHI9099'
    >>> intersection(catk1, catk2)
    'DEF5678'
    '''
    dimmem1 = re.findall(r'[A-Z]+[0-9]+',catk1)
    dimmem2 = re.findall(r'[A-Z]+[0-9]+',catk2)
    cm = [dimmem for dimmem in dimmem1 if dimmem in dimmem2]
    return ''.join(cm)

def convertToDict(catk):
    '''
    Converts the categorisation key to a dictionary with dimensions as keys and members as values.
    A valid categorisationvid contains one or more dimension code and member id concatenations.
    Such concatenations can be described as a regular expression [A-Z]*[0-9]*
    Input: catk is a datapointvid categorisation key
    Output: the dictionary with the dimension codes from the categorisation key as keys and the corresponding member ids
    (in the categorisation key) as values
    Note that an invalid input gets truncated up to the point where it follows the regular expression 
    
    >>> catk = 'ABC1234DEF5678GHI9012'
    >>> result = convertToDict(catk)
    >>> sorted([(dim,result[dim]) for dim in result])
    [('ABC', 1234), ('DEF', 5678), ('GHI', 9012)]
    >>> catk = ''
    >>> convertToDict(catk)
    {}
    '''
    return {dimMeb[:re.match(r'[A-Z]+',dimMeb).end()]:int(dimMeb[re.match(r'[A-Z]+',dimMeb).end():]) for dimMeb in re.findall(r'[A-Z]+[0-9]+', catk)}

def convertToCatk(dictCatk):
    '''
    Converts a dimension member dictionary to a categorisation key
    Input: setCatk a dimension member dictionary
    Output: a datapointvid like categorisation key
    
    >>> dictx = {'ABC':1234,'DEF':5678,'GHI':9012}
    >>> convertToCatk(dictx)
    'ABC1234DEF5678GHI9012'
    >>> dictx = {}
    >>> convertToCatk(dictx)
    ''
    '''
    catk = ''
    for x in sorted(dictCatk.keys()):
        catk += x
        catk += str(dictCatk[x])
    return catk

def getCatgorisationInfo(catk, dimensions, members):
    '''
    Transform the abstract categorisation key into a descriptive file.
    Input: catk a datapointvid categorisation key
    Ouput: a dictionary where the keys are tuples of dimension member combinations and the values are tuples
           of the dimension and member descriptions
    
    >>> dim = {'ABC':'eerste drie', 'DEF':'tweede drie','XYZ':'laatste drie'}
    >>> mem = {1234:'maandag',5678:'dinsdag',9012:'woensdag'}
    >>> x = 'DEF5678XYZ1234'
    >>> getCatgorisationInfo(x, dim, mem)
    {('DEF', 5678): ('tweede drie', 'dinsdag'), ('XYZ', 1234): ('laatste drie', 'maandag')}
    '''
    dictCatk = convertToDict(catk)
    return {(d,dictCatk[d]):(dimensions[d],members[dictCatk[d]]) for d in dictCatk}

def _test():
    import doctest
    return doctest.testmod()

if __name__ == "__main__":
    _test()
# python dpmAsGraphFunctions.py -v