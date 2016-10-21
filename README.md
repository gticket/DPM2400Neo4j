## DPM2400Neo4j
#### Creating Neo4j database from the provided csv files
To obtain a Neo4j database for the European Banking authority (EBA) datapoint model (DPM) 2.4.0.0 download all csv files from the DPM240 zip file and run the below statement.  
Be sure to replace [your neo4j folder] with the folder path where your Neo4j files should be stored and replace [your csv folder] with the folder path where you downloaded the csv files.  
  *neo4jImport --into "[your neo4j folder]\dpm2400.graphdb" --nodes "[your csv folder]\Neo4jCell.csv" --nodes "[your csv folder]\Neo4jDataPointVersion.csv" --nodes "[your csv folder]\Neo4jCliques.csv" --relationships "[your csv folder]\Neo4jCellDataPointVersion.csv" --relationships "[your csv folder]\Neo4jDataPointVersionCell.csv" --relationships "[your csv folder]\Neo4jCliqueNodes.csv" --relationships "[your csv folder]\Neo4jNodesClique.csv" --relationships "[your csv folder]\Neo4jCliqueHierarchy.csv" --relationships "[your csv folder]\Neo4jHierarchyClique.csv" --delimiter ";" --array-delimiter "|"*

#### To generate the csv files using python
To generate such csv files for other versions of the DPM below listed actions need to be performed.  
1. download the latest/relevant version of the EBA DPM from the [eba website] (http://www.eba.europa.eu/regulation-and-policy/supervisory-reporting/implementing-technical-standard-on-supervisory-reporting-data-point-model-)  
2. open the access database and export the following tables to text files (semicolon as delimiter, no text qualifier): DataPointVersion, mvCellLocation, TableVersion, Dimension, Member  
3. download both python 2.7 scripts and run the script dpmAsGraph after updating the path variable (line 24) 
Note that this query will take several hours to compleet on a laptop (about 4 hours on an intel i5-5300U CPU @2.30GHz with 16 GB of RAM). If you are only interested in a subset of the DPM, you can update the report filter in line 8.

####Some basic info on the DPM
Every cell of the single rule book reports (corep, finrep, etc) is linked to at most one datapointversion. A cell without a datapointversion is a greyed out cell (never gets any values).  
One datapointversion is linked to one or more cells. Cells which are linked to the same datapointversion must contain the same value.  
A datapointversion has a technical key (the datapointvid) and a functional key (the categorisation key) as such the terms datapointversion and categorisation key are interchangeble.  
The categorisation key is a concatenation (in alphabetical order) of the dimension code and member id tuples which are relevant for it.  
Each categorisation key has one metric dimension. The corresponding member describes what kind of value is to be reported in a cell. The other dimension member tuples describe the context of the cell (what kind of positions should be reported there).  
For further details about the EBA DPM please see the [eba website] (http://www.eba.europa.eu/regulation-and-policy/supervisory-reporting/implementing-technical-standard-on-supervisory-reporting-data-point-model-).

####Some basic info on Neo4j
Neo4j is a graphical database. There is a free community edition.  
A graphical database contains 2 basic elements: nodes and edges (called relationships in Neo4j). Nodes can have labels, relationships are of a certain type and both have properties.  
It comes with a query language called cypher.  
To download and install Neo4j or for further info on Neo4j and on cypher, please see the [Neo4j website](http://neo4j.com/).

####Info on the csv files
The DPM cells and categorisation keys are nodes of the graph.  
The links between cells and categorisation keys are relationships in the graph.  
When categorisation keys have the same dimensions and all but 1 of these dimensions have identical members than these are considered similar (they form a clique). These cliques are also nodes and each of the similar categorisation keys get a relationship to that clique node. The clique is identified by the common dimension member tuples and by the varying dimension.  
If the common dimension member tuples match with an existing categorisation key, these get a relationship to each other (that categorisation key is considered as a parent of the clique).  
If there is no such match, the clique is labelled as an orphan clique. When the varying dimension of such an orphan clique is the metric dimension the clique is labelled as a context clique.

####Some cypher queries
The graph contains a lot of relationships. The easiest way to limit the results is to filter on properties of cell nodes.  
**get the different sheets of the cells (n:cell)** 
```
Match (n:cell) Return Distinct n.sheet, count(n.sheet) Order by n.sheet  
```
**get cells from a certain report {sheet:"F 01.01"} which share a categorisation key with other cells (will contain the same value)**  
```
Match (c1:cell {sheet:"F 01.01"}) -[r1]-> (ck:categorisationkey) <-[r2]- (c2:cell)  
Return c1, c2, ck, r1, r2  
Order by c1.sheet, c2.sheet, c1.row, c2.row, c1.column, c2.column, c1.dimension, c2.dimension  
```
**list all cells of a report ({sheet:"P 01.01"}) which are linked to cells of a different report**  
```
Match (cs:cell {sheet:"P 01.01"}) -[r*1..4]-> (co:cell) Where co.sheet <> cs.sheet Return cs, r, co  
```
**list all orphaned cliques of a report ({sheet:"C 67.00.a"})**  
```
Match (cs:cell {sheet:"C 67.00.a"}) -[r1]-> () -[r2]-> (oc:orphanClique) Return cs, r1, r2, oc  
```
Another way to proceed is to return only one cell. Find relationships by double clicking on that cell.  
**get one specific cell ({sheet:"C 107.01.a",row:"010",column:"010",dimension:"000"})**  
```
Match (a:cell {sheet:"C 107.01.a",row:"010",column:"010",dimension:"000"})  
Return a  
```
If you want to see what the relationship is between two specific cells the shortest path algorithm can be used.  
**find the shortest path between two cells (sheet:"C 07.00.b",row:"090",column:"210",dimension:"007" and sheet:"C 07.00.a",row:"090",column:"200",dimension:"007")**  
```
Match p=shortestPath(  
  (a:cell {sheet:"C 07.00.b",row:"090",column:"210",dimension:"007"})-[*]-(b:cell {sheet:"C 07.00.a",row:"090",column:"200",dimension:"007"}))  
Return p  
```
