import os
from dpmAsGraphFunctions import applyFilter, distance, decompose, intersection, convertToDict, convertToCatk, getCatgorisationInfo
from datetime import datetime

################################################################################################
# define report filter -- CHANGE AS NEEDED                                                     #
################################################################################################
repFilter = ['%']
#repFilter = ['F%']
#repFilter = ['C%']
#repFilter = ['P%']
#repFilter = ['C 07.00.%','C 09.01%','C 11.00']
#repFilter = ['C 07.00.%'] # 1'41" --> 4'
#repFilter = ['C 07.00.a']
#repFilter = ['C 11.00']

################################################################################################
# Location of the text files which have been exported from the EBA DPM 2.4.0.0 access database #
# assumes this is in a subfolder called DPM240 of this python file: CHANGE AS NEEDED           #
################################################################################################

currentdir = os.path.dirname(__file__)
print currentdir
path = os.path.join(currentdir, 'DPM240') # CHANGE AS NEEDED
fileDataPointVersion = 'DataPointVersion.txt'
fileMvCellLocation = 'mvCellLocation.txt'
fileTableVersion = 'TableVersion.txt'
fileDimension = 'Dimension.txt'
fileMember = 'Member.txt'   

################################################################################################
# Load the data                                                                                #
################################################################################################
print("%s: Data loading started" % (str(datetime.now())))

# Load the relevant DPM 2.3.1.0 files
if not os.path.isfile(path + '\\' + fileTableVersion):
    print('No file %s found in directory %s' % (fileTableVersion,path))
if not os.path.isfile(path + '\\' + fileDataPointVersion):
    print('No file %s found in directory %s' % (fileDataPointVersion,path))
if not os.path.isfile(path + '\\' + fileMvCellLocation):
    print('No file %s found in directory %s' % (fileMvCellLocation,path))
if not os.path.isfile(path + '\\' + fileDimension):
    print('No file %s found in directory %s' % (fileDimension,path))
if not os.path.isfile(path + '\\' + fileMember):
    print('No file %s found in directory %s' % (fileMember,path))
    
# Get the info from the relevant files
ftbv = open(path + '\\' + fileTableVersion,'r')
fdpv = open(path + '\\' + fileDataPointVersion,'r')
fclc = open(path + '\\' + fileMvCellLocation,'r')
fdim = open(path + '\\' + fileDimension,'r')
fmem = open(path + '\\' + fileMember,'r')

# Consider only report versions with open end validity date, remove end of lines characters and quotes, split on comma
tblVerInfo = [x[2] for x in [d.replace('\n','').replace('"','').split(';') for d in ftbv] if x[7] == '']
print('Number of currently valid report versions is %i' % (len(tblVerInfo)))
# Remove all report versions which do not match with the filter
tblVer = applyFilter(tblVerInfo,repFilter)
print('Number of report versions after applying report filter is %i' % (len(tblVer)))
# Retain only the cells from tables in the table version array
cellInfo = [x for x in [d.replace('\n','').replace('"','').split(';') for d in fclc] if x[2] in tblVer]
print('Number of cells retained for the reports is %i' % (len(cellInfo)))
# Dimension info - description field in table Dimension contains end of line characters - additional checks needed
ffdim = [x for x in fdim]
lfdim = len(ffdim)
dimpos = 0
dim = {}
while dimpos < lfdim - 1:
     # a new dimension record will always start with a digit, the description fields rarely contains a digit
    if ffdim[dimpos + 1][0] in {'0','1','2','3','4','5','6','7','8','9'}:
        dimsplit = ffdim[dimpos].replace('\n','').split(';')
        dim[dimsplit[2]] = dimsplit[3]
    else:
        ffdim[dimpos + 1] = ffdim[dimpos] + ffdim[dimpos + 1]
    dimpos +=1
dimsplit = ffdim[dimpos].replace('\n','').split(';')
dim[dimsplit[2]] = dimsplit[3]
fdim.close()
maxDimLen = max([len(d) for d in dim])
print('Number of records in the file %s is %i' % (fileDimension,len(dim)))
# Member info
mem = {int(y[0]):y[3] for y in [x.replace('\n','').split(';') for x in fmem]}
fmem.close()
maxMemLen = max([len(str(m)) for m in mem])
print('Number of records in the file %s is %i' % (fileMember,len(mem)))
# Datapointversion info
dpv = [x for x in fdpv]
fdpv.close()
print('Number of records in the file %s is %i' % (fileDataPointVersion,len(dpv)))

################################################################################################
# Creating various data structures to be used in the processing:                               #
################################################################################################
# Create a cell dictionary with the most recent cells (highest taxonomy id)
# Create a datapointVID dictionary of the cells with the datapointVID as key and the cell keys as values (array of values)
# Create a dictionary dpvInfo by formatting and filtering of the datapoint array (datapointVID must be in the above created dictionary)
# Update cells dictionary by adding the categorisationkey
# Create a look up categorisationkeys dictionary of categorisationkeys where the value is the array of cells with that categorisationkey
# Create an array of the categorisationkeys keys
# Perform a number of sanety checks
################################################################################################
print("%s: Creation of data structures started" % (str(datetime.now())))

# Create a cell dictionary with the most recent cells (highest taxonomy id)
# {(reportversion,row,col,dimension):[datapointVID,metricID,taxonomyID,categorisationkey,cellID]}
cells = {}
for cell in cellInfo:
    # cellID
    key = (cell[2],cell[3],cell[4],cell[5]) # (reportversion,row,col,dimension)
    value = [cell[6],cell[8],cell[15],'',int(cell[0])] # [datapointVID,metricID,taxonomyID,categorisationkey,cellID]
    if value[0] != '':
        value[0] = int(value[0])
    # If the cell is not yet in the dictionary, add it
    if cells.get(key,0) == 0:
        cells[key] = value
    else:
        # If the cell is already in the dictionary, replace it if the taxonomyID is more recent (higher value)
        if cells[key][2] < value[2]:
            cells[key] = value
print('Number of most recent cells for the reports is %i' % (len(cells)))
#print cells

# Create a datapointVID dictionary of the cells with the datapointVID as key and the cell keys as values (array of values)
# {datapointvid:[(reportversion,row,col,dimension),...]}
# This will ease the look up of the categorisation key of the datapointvid of the cells
# note that some cells do not have a datapointVID (greyed out cells)
datapointVID = {}
nbrOfGreyedOutCells = 0
for cell in cells:
    # datapointVID not yet present --> add
    if datapointVID.get(cells[cell][0],0) == 0 and cells[cell][0] != '': # cell[0] is datapointVID
        datapointVID[cells[cell][0]] = [cell]
    # datapointVID already present --> append
    else:
        if cells[cell][0] != '':
            datapointVID[cells[cell][0]].append(cell)
        else:
            nbrOfGreyedOutCells += 1
print('Number of datapointVIDs in the reports is %i' % (len(datapointVID)))
print('Number of greyed out cells in the reports is %i' % (nbrOfGreyedOutCells))
#print datapointVID

# Create a dictionary dpvInfo by formatting and filtering of the datapoint array (datapointVID must be in the above created dictionary)
# {datapointVID:categorisationkey}
dpvInfo = {int(x[0]):x[6] for x in [d.replace('\n','').replace('"','').split(';') for d in dpv] if int(x[0]) in datapointVID}
print('Number of datapointVIDs in the dictionary is %i' % (len(dpvInfo)))
#print dpvInfo

# Update cells dictionary by adding the categorisationkey
for cell in cells:
    # if the cell has a datapointVID (not greyed out) # cell[0] is datapointVID
    if cells[cell][0] != '':
        cells[cell][3] = dpvInfo[cells[cell][0]] # cell[3] is categorisationkey
print('Number of cells in the reports is %i' % (len(cells)))
#for cell in cells:
#    print(cell)
#    print(cells[cell])

# Create a look up categorisationkeys dictionary of categorisationkeys where the value is the array of cells with that categorisationkey
categorisationkeys = {}
for cell in cells:
    #print cell
    if cells[cell][3] != '':
        if categorisationkeys.get(cells[cell][3],0) == 0:
            categorisationkeys[cells[cell][3]] = [cell]
        else:
            categorisationkeys[cells[cell][3]].append(cell)
            
# Create an array of the categorisation key keys
catk = categorisationkeys.keys()

#print catk
# Perform a number of sanety checks
# if a cell has no datapointVID it should also not have a metricID
for cell in cells:
    if (cells[cell][0] == '' and cells[cell][1] != '') or (cells[cell][0] != '' and cells[cell][1] == ''):
        print('Problem with cell %s. If a cell has no datapointVID it should also not have a metricID' % (str(cell)))

################################################################################################
# Create neo4j node/vertices and edges/link files:                                             #
################################################################################################
# Name the neo4j files
# The cells are vertices/nodes
# Add the categorisation keys as nodes/vertices
# Create edges between the categorisation keys and cells (in both directions)
# Create parent child relationships based on the 'distance' between categorisation keys
################################################################################################

print("%s: Creation of nodes and edges files started" % (str(datetime.now())))
# Name the neo4j files
path = os.path.join(currentdir, 'DPM240') 
pathNeo = path # CHANGE AS NEEDED
cellsOutput = 'Neo4jCell.csv' # the cells are the nodes
dpvOutput = 'Neo4jDataPointVersion.csv' # the cells are the nodes
dpvCellsOutput = 'Neo4jCellDataPointVersion.csv' # the cell nodes are linked (have edges) to categorisation key nodes
celldpvsOutput = 'Neo4jDataPointVersionCell.csv' # the categorisation key nodes are linked (have edges) to cell nodes
cliquesOutput = 'Neo4jCliques.csv' # parent child intersections with the varying dimension
cliqueNodesOutput = 'Neo4jCliqueNodes.csv' # cliques edges to the corresponding child nodes
nodesCliqueOutput = 'Neo4jNodesClique.csv' # cliques edges to the corresponding child nodes
cliqueHierarchyOutput = 'Neo4jCliqueHierarchy.csv' # child node edges to the corresponding cliques
hierarchyCliqueOutput = 'Neo4jHierarchyClique.csv' # child node edges to the corresponding cliques

# The cells are vertices/nodes
vertices = [cell for cell in cells]
print('Number of cell vertices is %i' % (len(vertices)))
fileCells = open(pathNeo + '\\' + cellsOutput,'w')
fileCells.write('cellid:ID(cell);sheet;row;column;dimension;datapointvid:int;taxonomyid:int;categorisationkey;description;:LABEL\n')
for vertex in vertices:
    fileCells.write(str(cells[vertex][4]) + ';' + str(vertex[0]) + ';' + str(vertex[1]) + ';' + str(vertex[2]) + ';' + str(vertex[3]) + ';' + str(cells[vertex][0]) + ';' + str(cells[vertex][2]) + ';' + str(cells[vertex][3]))
    st = ''
    infoAll = getCatgorisationInfo(cells[vertex][3], dim, mem)
    for info in sorted(infoAll.keys()):
        st += str(infoAll[info]) + '|'
    if len(st) > 0:
        fileCells.write(';' + st[:-1] + ';cell\n')
    else:
        fileCells.write(';;greyedOutCell\n')
fileCells.close()

# Add the categorisation keys as nodes/vertices
print('number of categorisation key vertices is %i' % (len(catk)))
fileCatk = open(pathNeo + '\\' + dpvOutput,'w')
fileCatk.write('categorisationkey:ID(catk);description;:LABEL\n')
for vertex in catk:
    fileCatk.write(vertex)
    st = ''
    infoAll = getCatgorisationInfo(vertex, dim, mem)
    for info in sorted(infoAll.keys()):
        st += str(infoAll[info]) + '|'
    if len(st) > 0:
        fileCatk.write(';' + st[:-1] + ';categorisationkey\n')
    else: # should not happen since currently only real categorisation keys are stored in catk
        fileCatk.write(';;dummyCategorisationkey\n')
fileCatk.close()

# Create edges between the categorisation keys and cells (in both directions)
fileCellCatk = open(pathNeo + '\\' + dpvCellsOutput,'w')
fileCellCatk.write(':START_ID(cell);:END_ID(catk);:TYPE\n') # clique,childnode)
fileCatkCell = open(pathNeo + '\\' + celldpvsOutput,'w')
fileCatkCell.write(':START_ID(catk);:END_ID(cell);:TYPE\n') # clique,childnode)
for cell in vertices:
    if cells[cell][3] != '':
        fileCellCatk.write(str(cells[cell][4]) + ';' + str(cells[cell][3]) + ';cellHasAsCategorisationKey\n')
        fileCatkCell.write(str(cells[cell][3]) + ';' + str(cells[cell][4]) + ';IsCategorisationKeyOfCell\n')
fileCellCatk.close()
fileCatkCell.close()
#print vertices

# Create parent child relationships based on the 'distance' between categorisation keys
'''
################################################################################################
# The calculation of distances between categorisation keys is a cpu intensive process          #
# This calculation should be avoided if possible                                               #
# The DPM configuration allows us to define a number of lowerbounds on the distances between   #
# cells thus allowing to reduce the number of distance calculations                            #
# First a lowerbound is calculated between each row of each report version:                    #
#    for each row of each report version take the intersection of all not greyed out cells (   #
#    with a categorisation key)                                                                #
#    calculate the distance between these intersections                                        #
#    only cells that belong to rows of report versions for which the 'intersection' distance   #
#    between their rows is 1 or less need to be considered                                     #
# Next lowerbound can be established by calculating the length of the categorisation key string# 
#    only cells that have a length difference which is equal or less than the length of the    #
#    longest dimension and member values need to be considered                                 #
################################################################################################
'''
# Display the number of categorisation keys that need to be processed
nbrOfCatk = len(catk)
print("%s: Categorisation keys pre processing (lower bound distance determination) started" % (str(datetime.now())))
print('There are %i categorisation keys to process.' % (nbrOfCatk))
# Create a dictionary of cliques where the key is a tuple containing the parent categorisation key and the 
# extra dimension in the child categorisation key. The value is a set of categorisation keys which form the clique.
cliques = {}

# Create a dictionary for the cliques hierarchy where the key is the parent categorisation key of the clique members and 
# the value is an array of cliques
cliqueHierarchy = {} # {categorisation key:[cliques]}

# Get intersection of all categoristion keys per row of each report version (first lowerbound)
print("%s: Categorisation key determination of the intersection of report version rows started" %(str(datetime.now())))
reportVersionIntersection = {}
for cell in cells:
    if cells[cell][3] != '':
        #print("Current intersect: %s" % (reportVersionIntersection.get(cell[0],0)))
        #currentIntersect = reportVersionIntersection.get(cell[0],0)
        currentIntersect = reportVersionIntersection.get((cell[0],cell[1]),0)
        if currentIntersect == 0:
            #print("Catk of current cell: %s" % (cells[cell][3]))
            #reportVersionIntersection[cell[0]] = cells[cell][3]
            reportVersionIntersection[(cell[0],cell[1])] = cells[cell][3]
        else:
            #print("New intersection (between %s and %s)" % (currentIntersect,cells[cell][3]))
            #print("New intersection: %s" % (intersection(currentIntersect,cells[cell][3])))
            #reportVersionIntersection[cell[0]] = intersection(currentIntersect,cells[cell][3])
            reportVersionIntersection[(cell[0],cell[1])] = intersection(currentIntersect,cells[cell][3])
#print reportVersionIntersection

print("%s: Distance determination of the intersection of report version rows started" %(str(datetime.now())))
# Set of report version row tuples with intersection minimum distance no more than 1
reportVersionClose = set([])
reportVersion = reportVersionIntersection.keys()
lrpv = len(reportVersion)
for lrpvi in range(lrpv):
    for lrpvj in range(lrpvi + 1,lrpv):
        #print reportVersion[lrpvi]
        #print reportVersionIntersection[reportVersion[lrpvi]]
        if distance(reportVersionIntersection[reportVersion[lrpvi]],reportVersionIntersection[reportVersion[lrpvj]]) <= 1:
            reportVersionClose.add((reportVersion[lrpvi],reportVersion[lrpvj]))
print("%s: There are %i report version row combinations (out of %i) which could have categorisation keys which are closely related" % (str(datetime.now()),len(reportVersionClose),len(reportVersionIntersection)*(len(reportVersionIntersection)-1)/2))

# Make an estimate which categorisation keys could requirer processing based on the length of the categorisation key (second lowerbound)
catkDist = {} # dictionary to store the positive combinations {i:{j1,j2,j3,...},...}
for i in range(nbrOfCatk):
    if i%1000 == 0:
        print("at iteration %i" % (i))
    for j in range(i+1,nbrOfCatk):
        #if (categorisationkeys[catk[i]][0][0] == categorisationkeys[catk[j]][0][0] or
        #    (categorisationkeys[catk[i]][0][0],categorisationkeys[catk[j]][0][0]) in reportVersionClose):
        if ( (categorisationkeys[catk[i]][0][0],categorisationkeys[catk[i]][0][1]) == (categorisationkeys[catk[j]][0][0],categorisationkeys[catk[j]][0][1]) or
            ((categorisationkeys[catk[i]][0][0],categorisationkeys[catk[i]][0][1]),(categorisationkeys[catk[j]][0][0],categorisationkeys[catk[j]][0][1])) in reportVersionClose):
            if abs(len(catk[i]) - len(catk[j])) <= maxDimLen + maxMemLen:
                if catkDist.get(i,-1) != -1:
                    catkDist[i].add(j)
                else:
                    catkDist[i] = {j}
l = sum([len(catkDist[x]) for x in catkDist])
print("%s: Categorisation keys pre processing (lower bound distance determination) ended" % (str(datetime.now())))
print("Dictionary catkDist contains %i values" % (l))

# Build an array of tuples of categorisation keys which are no futher apart than 1 dimension
print("%s: Calculation of distances started" % (str(datetime.now())))
distCalc = 0
dropped = 0
catkProcess = []
count = 0
mod = 1
catkDistKeys = catkDist.keys() # trick to be able to drop each key after it has been processed (to shrink the dictionary)
for i in catkDistKeys:
    #remember = {}
    remember = []
    if i%mod == 0:
        count += 1
        if count%3 == 0:
            mod *= 2
        print("%s: processing (distance <= 1 determination) categorisation key %i started (%i distances calculated, %i dropped so far)" %(str(datetime.now()),i,distCalc,dropped))
    for j in catkDist[i]:
        d = distance(catk[i],catk[j])
        #remember[j] = d
        remember.append((j,d))
        if d <= 1:
            # add tupple to set for which the relationship needs to be betermined
            catkProcess.append((i,j))
    distCalc += len(catkDist[i])
    # if a is x distance from b and y distance from c than b and c are at least abs(x-y) distance from each other
    # remove from catkDist those combinations where the mimimum distance, as obtained above, is more than one
    if i%mod == 0:
        print("%s: %i distances calculated, dropping redundant distance determinations started" %(str(datetime.now()),len(catkDist[i])))
    dropStep = 0
    lrem = len(remember)
    # shrink the dictionary
    catkDist.pop(i)
    dropStep = dropped
    for ii in range(lrem):
        if remember[ii][0] in catkDist:
            for ij in range(ii+1,lrem):
                if remember[ij][0] in catkDist[remember[ii][0]]:
                    if abs(remember[ii][1] - remember[ij][1]) > 1:
                        catkDist[remember[ii][0]].remove(remember[ij][0])
                        dropped += 1
    dropStep = dropped - dropStep
    if i%mod == 0:
        print("%s: dropped %i redundant distance determinations" %(str(datetime.now()),dropStep))

print("%s: Calculations of distances ended" % (str(datetime.now())))                    
#print catkProcess
print("number of categorisation keys which are less than 1 dimension apart is %i" % (len(catkProcess)))
print("ratio of categorisation keys which are less than 1 dimension apart to the number of calculations: %f" % (1.0*len(catkProcess)/distCalc))

# Iterate over each categorisation key and check relation ships
print("%s: Categorisation keys processing (relation ship determination) started" % (str(datetime.now())))
for (i,j) in catkProcess:
    varDim = ''
    siblings = 0
    # decompose the categorisation keys
    common, celli, cellj = decompose(catk[i],catk[j])
    # get the varying dimension, the parent, the child and the sibling indicator
    if len(celli) == 0: # i is the parent of j
        for x in convertToDict(cellj).keys(): # format the varying dimension as a string
            varDim += x
            parent = catk[i]
            child = catk[j]
    else: # j is the parent of i OR i and j have a common dimension with a different member
        for x in convertToDict(celli).keys():
            varDim += x
            if len(cellj) == 0: # j is parent
                parent = catk[j]
                child = catk[i]
            else:
                siblings = 1
    # add to cliques and add categorisation keys to clique
    if cliques.get((common,varDim),0) == 0:
        cliques[(common,varDim)] = set([])
    if siblings == 1:
        cliques[(common,varDim)].add(catk[i])
        cliques[(common,varDim)].add(catk[j])
    else:
        cliques[(common,varDim)].add(child)
    # add parent relationship, if the parent exists as a categorisation key
    if categorisationkeys.get(common,0) != 0:
        if cliqueHierarchy.get(common,0) == 0:
            cliqueHierarchy[common] = [(common,varDim)]
        else:
            if not (common,varDim) in cliqueHierarchy[common]:
                cliqueHierarchy[common].append((common,varDim))
print("%s: Categorisation keys processing (relation ship determination) ended" % (str(datetime.now())))
                    
#print cliques
#print cliqueHierarchy
print("Number of cliques: %i" % (len(cliques)))
print("Number of categorisation keys in the cliques: %i " % (sum([len(cliques[value]) for value in cliques])))
print("Number of parents of cliques: %i" % (len(cliqueHierarchy)))
print("Number of cliques with parents: %i " % (sum([len(cliqueHierarchy[value]) for value in cliqueHierarchy])))

fileCliques = open(pathNeo + '\\' + cliquesOutput,'w')
fileCliques.write('clique:ID(clique);descriptionCategorisationKey;descriptionVaryingDimension;:LABEL\n')
#print('clique:ID(clique);:LABEL')
fileCliqueNodes = open(pathNeo + '\\' + cliqueNodesOutput,'w')
fileCliqueNodes.write(':START_ID(clique);:END_ID(catk);:TYPE\n') # clique,childnode
fileNodesClique = open(pathNeo + '\\' + nodesCliqueOutput,'w')
fileNodesClique.write(':START_ID(catk);:END_ID(clique);:TYPE\n') # clique,childnode
#print(':START_ID(clique);:END_ID(cell);:TYPE')
for clique in cliques:
    fileCliques.write(clique[0] + '-' + clique[1] + ';')
    st = ''
    infoAll = getCatgorisationInfo(clique[0], dim, mem)
    for info in sorted(infoAll.keys()):
        st += str(infoAll[info]) + '|'
    if len(st) > 0:
        fileCliques.write(st[:-1] + ';')
    else:
        fileCliques.write(';')
    if clique[1] != '':
        fileCliques.write(dim[clique[1]])
    if clique[1] == 'ATY':
        fileCliques.write(';contextClique\n')
    elif clique[1] == '': # should no longer happen since we are working with categorisation keys
        fileCliques.write(';identityClique\n')
    elif categorisationkeys.get(clique[0],0) == 0:
        fileCliques.write(';orphanClique\n')
    else:
        fileCliques.write(';parentClique\n')
    #print(clique[0] + clique[1] + ';clique')
    for catk in cliques[clique]:
        #print(clique[0] + '-' + clique[1] + ';' + catk + ';cliqueContainsCategorisationKey\n') 
        fileCliqueNodes.write(clique[0] + '-' + clique[1] + ';' + catk + ';cliqueContainsCategorisationKey\n')
        fileNodesClique.write(catk + ';' + clique[0] + '-' + clique[1] + ';categorisationKeyIsPartOfClique\n')
        #print(clique[0] + clique[1] + ';' + str(cells[cell][4]) + ';contains')
fileCliques.close()
fileCliqueNodes.close()
fileNodesClique.close()
fileCliqueHierarchy = open(pathNeo + '\\' + cliqueHierarchyOutput,'w')
fileCliqueHierarchy.write(':START_ID(catk);:END_ID(clique);:TYPE\n') # parent,clique
fileHierarchyClique = open(pathNeo + '\\' + hierarchyCliqueOutput,'w')
fileHierarchyClique.write(':START_ID(clique);:END_ID(catk);:TYPE\n') # parent,clique
for parent in cliqueHierarchy:
    for clique in cliqueHierarchy[parent]:
        fileCliqueHierarchy.write(parent + ';' + clique[0] + '-' + clique[1] + ';categorisationKeyOfClique\n')
        fileHierarchyClique.write(clique[0] + '-' + clique[1] + ';' + parent + ';cliqueHasAsCategorisationKey\n')
fileCliqueHierarchy.close()
fileHierarchyClique.close()
print("%s: Processing finished" % (str(datetime.now())))

'''
------------
Neo4j Code -
------------
cd C:\program files (x86)\neo4j community\bin
neo4jImport --into "C:\Users\glenn.ticket\Documents\Neo4j\dpm2400.graphdb" --nodes "C:\Users\glenn.ticket\Dropbox\MyPython\myModules\DPM\DPM240\Neo4jCell.csv" --nodes "C:\Users\glenn.ticket\Dropbox\MyPython\myModules\DPM\DPM240\Neo4jDataPointVersion.csv" --nodes "C:\Users\glenn.ticket\Dropbox\MyPython\myModules\DPM\DPM240\Neo4jCliques.csv" --relationships "C:\Users\glenn.ticket\Dropbox\MyPython\myModules\DPM\DPM240\Neo4jCellDataPointVersion.csv" --relationships "C:\Users\glenn.ticket\Dropbox\MyPython\myModules\DPM\DPM240\Neo4jDataPointVersionCell.csv" --relationships "C:\Users\glenn.ticket\Dropbox\MyPython\myModules\DPM\DPM240\Neo4jCliqueNodes.csv" --relationships "C:\Users\glenn.ticket\Dropbox\MyPython\myModules\DPM\DPM240\Neo4jNodesClique.csv" --relationships "C:\Users\glenn.ticket\Dropbox\MyPython\myModules\DPM\DPM240\Neo4jCliqueHierarchy.csv" --relationships "C:\Users\glenn.ticket\Dropbox\MyPython\myModules\DPM\DPM240\Neo4jHierarchyClique.csv" --delimiter ";" --array-delimiter "|"
neo4jImport --into "C:\Users\glenn.ticket\Documents\Neo4j\dpm2310.graphdb" --nodes "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCell.csv" --nodes "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jDataPointVersion.csv" --nodes "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCliques.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCellDataPointVersion.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jDataPointVersionCell.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCliqueNodes.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jNodesClique.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCliqueHierarchy.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jHierarchyClique.csv" --delimiter ";" --array-delimiter "|"
neo4jImport --into "C:\Users\glenn.ticket\Documents\Neo4j\dpm2310F.graphdb" --nodes "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCell.csv" --nodes "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jDataPointVersion.csv" --nodes "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCliques.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCellDataPointVersion.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jDataPointVersionCell.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCliqueNodes.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jNodesClique.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCliqueHierarchy.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jHierarchyClique.csv" --delimiter ";" --array-delimiter "|"
neo4jImport --into "C:\Users\glenn.ticket\Documents\Neo4j\dpm2310C.graphdb" --nodes "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCell.csv" --nodes "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jDataPointVersion.csv" --nodes "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCliques.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCellDataPointVersion.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jDataPointVersionCell.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCliqueNodes.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jNodesClique.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jCliqueHierarchy.csv" --relationships "C:\Users\glenn.ticket\Documents\DPMfiles\Neo4jHierarchyClique.csv" --delimiter ";" --array-delimiter "|"

// get the different sheets of the cells
Match (n:cell) Return Distinct n.sheet, count(*) Order by n.sheet
// get cells from a certain report which share a categorisation key with other cells (will contain the same value)
Match (c1:cell {sheet:"F 01.01"}) -[r1]-> (ck:categorisationkey) <-[r2]- (c2:cell)
Return c1, c2, ck, r1, r2
Order by c1.sheet, c2.sheet, c1.row, c2.row, c1.column, c2.column, c1.dimension, c2.dimension
// get one specific cell ({sheet:"C 107.01.a",row:"010",column:"010",dimension:"000"})
Match (a:cell {sheet:"C 107.01.a",row:"010",column:"010",dimension:"000"})
Return a
// list all cells of a report ({sheet:"P 01.01"}) which are linked to cells of a different report
Match (cs:cell {sheet:"P 01.01"}) -[r*1..4]-> (co:cell) Where co.sheet <> cs.sheet Return cs, r, co
// list all orphaned cliques of a report ({sheet:"C 67.00.a"})
Match (cs:cell {sheet:"C 67.00.a"}) -[r1]-> () -[r2]-> (oc:orphanClique) Return cs, r1, r2, oc
// find the shortest path between two cells (sheet:"C 07.00.b",row:"090",column:"210",dimension:"007" and sheet:"C 07.00.a",row:"090",column:"200",dimension:"007")
Match p=shortestPath(
  (a:cell {sheet:"C 07.00.b",row:"090",column:"210",dimension:"007"})-[*]-(b:cell {sheet:"C 07.00.a",row:"090",column:"200",dimension:"007"}))
Return p

// get the different link types
Match () -[r]-> () Return distinct type(r), count(*)
// get the different labels
START n=node(*) RETURN distinct labels(n), count(*)
// get cells with multiple categorisation keys (ZERO RECORDS since this does not exist)
Match (c:cell) --> (ck1:categorisationkey), (c) --> (ck2:categorisationkey)  where not ck1 = ck2 return c, ck1
// get (some) of the P 01.01 cells
Match (a) -[r]-> (b) -[rs]-> (c) where a.sheet = "P 01.01" return a, type(r), b, type(rs), c
Match (a) -[r*]-> (c) where a.sheet = "P 01.01" and c.sheet = "P O1.O1" return a, type(r)
// get the different cells with categorisations keys
Match (b) --> (a:cell) Return b, a
// get cliques with the categorisationkeys (and the cells) these contain
Match (a) -[r:cliqueContainsCategorisationKey]-> (b) -[c:IsCategorisationKeyOfCell]-> (d)
Where d.column = "010" // Where d.row = "010"
Return a, b, c
// get the different categorisation keys of the cells
Match (a) -[r:IsCategorisationKeyOfCell]-> (b) return distinct a, b
// get the categorisation keys of cliques, the cliques members, the categorisation keys and the cells
Match (d) --> (a) --> (b) --> (c) Return d,a,b,c
Match (d) --> (a) --> (b) --> (c) where d.categorisationkey = "ATY1478BAS1510PRP2575" Return d,a,b,c
Match (d) --> (a) --> (b) --> (c) Return d,a,b,c
// get the different categorisation keys of the cliques
Match (a) -[r:IsCategorisationKeyOfCell]-> (b) return distinct a, b
// get the parents of cliques, the cliques and the cell these contain
Match (a) -[r:parentOfClique]-> (b) --> (c) return a, b, c
// get all the cliques and the cells these contain but which do not have parent cells
Match (b) -[r:contains]-> (c) where not () --> (b) return b, type(r), c
// get all cliques and the cells these contain where these contain at least one row 120 cell
Match (m:clique) --> (n:cell {row:'120'}), (m) --> (p) return m, n, p
MATCH (c) -[rr]-> (a) -[r:parent]-> (b) RETURN TYPE(rr),a,c,b
MATCH (a) -[r:parent]-> (b) -[rr:parent]-> (c) RETURN a,b
Match (a) -[r]-> (b) Return r, a, b # will show relationships in the graph even with autocompleet off but not in the row view
Match (a) -[r]-> (b) Return Type(r), a, b # will not show relationships in the graph unless autocompleet is on but will list the type of relationship in the row view
// find the shortest path between cells 010 010 and 120 030
MATCH p=shortestPath(
  (cell010010 {row:"010",column:"010"})-[*]-(cell120030 {row:"120",column:"030"})
)
RETURN p
Match (a:cell)
where (a.sheet = "C 07.00.a" and a.row = "090" and a.column = "200" and a.dimension = "007")
   or (a.sheet = "C 07.00.b" and a.row = "090" and a.column = "210" and a.dimension = "007")
return a
Match (a) -[r]-> (b)
Return Type(r), r, a.row, b.row, a.column, b.column, a.categorisationkey, b.categorisationkey
Order by a.row, b.row, a.column, b.column
Match (a) -[r]-> () Return Distinct Type(r), a // returns the nodes that have a relationship and lists the types
Match (n) Where n.row in ['010','020'] Return n Order by n.row, n.column;
// list all nodes without relationships
MATCH (a)
WHERE Not () --> (a) AND NOT (a) --> ()
RETURN a
ORDER BY a.row, a.column;
// list all nodes which are parents and siblings
Match (a) -[p]-> (), (a) -[s]-> (b)
Where Type(p) = 'parent' and Type(s) = 'sibling'
Return Distinct a, a.row, a.column
Order by a.row, a.column;
// list all nodes which are linked as sibling to another node but which aren't parent themself
Match () -[s]-> (n)
Where Type(s) = 'sibling' and Not (n) -[:parent]-> ()
Return Distinct n, n.row, n.column;
// adding an index -- no composite indexes ?
CREATE INDEX ON :cell(row);
CREATE INDEX ON :cell(column);
// collect the child nodes per parent node
Match (p) -[:parent]-> (c)
Return p, count(c), collect(c.datapointvid), collect(c.row), collect(c.column)
Order by p.row, p.column;
// collect the child nodes per parent node and check these are siblings of each other
// note: leave level sibling needs to be enabled
//       what if there is only one child ?
Match (p) -[:parent]-> (c),
      (c) -[:sibling]-> (o),
      (p) -[:parent]-> (o)
Return p, count(c), collect(c.datapointvid)
Order by p.row, p.column;
// list all nodes which are 2 relationships away from any other node
MATCH (a) -[*2]-> ()
RETURN a
// list all nodes which are 2 parent levels away from any other node
MATCH (a) -[:parent*2]-> ()
RETURN a
// list all nodes without parent but with a datapointvid
Match (a)
where not () --> (a) and a.datapointvid > 0
return a, a.row, a.column
// list all cliques
Match (a:clique)
Return a
// list all cliques with their content
Match (a:clique) --> (b) Return a, b
'''